# example_catalog.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Lists the examples a repository builds, each with the sentence its source gives it.

The reasoning is in docs/architecture/OVERVIEW.md, section `example_catalog`.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import final

K_EXAMPLES_FOLDER = Path("applications") / "examples"
K_REGISTRATION_FILE = "CMakeLists.txt"

# The first argument is a literal name; a name from a variable is a wrapper's own body.
_REGISTRATION = re.compile(
    r"(?<!\w)(?:\w*add_example|add_executable)\(\s*(?P<name>[\w.+-]+)(?P<arguments>[^)]*)\)")
_COMMENT = re.compile(r"#[^\n]*")
_SOURCE = re.compile(r"[\w./+-]+\.(?:cpp|cc|cxx)")
_BRIEF = re.compile(r"@brief\s+(?P<text>.*?)(?=\n\s*\*\s*@|\n\s*\*/)", re.DOTALL)
_CONTINUATION = re.compile(r"\s*\n\s*\*\s*")


@dataclass(frozen=True, slots=True)
class Example:
    """Holds one example: its target name and the `@brief` of its source."""

    name: str
    brief: str


@final
class ExampleCatalog:
    """Reads the examples a repository registers under one folder.

    Every `CMakeLists.txt` under the folder is read, the folder's own first, and each call that
    names a literal target through `add_executable` or a wrapper called `<prefix>add_example`
    is one example. The repository's own registration is the only list, so a new example appears
    here without an edit to this class, whatever the repository calls its wrapper.

    Args:
        examples_dir: The folder that holds the examples, `K_EXAMPLES_FOLDER` of a checkout.
    """

    def __init__(self, examples_dir: Path) -> None:
        self._examples_dir = examples_dir

    @classmethod
    def in_project(cls, project_root: Path) -> ExampleCatalog:
        """Returns the catalog of the examples under *project_root*."""
        return cls(project_root / K_EXAMPLES_FOLDER)

    def entries(self) -> list[Example]:
        """Returns the examples in registration order; empty when the folder has none."""
        found: dict[str, Example] = {}
        for registration in self._registration_files():
            text = _COMMENT.sub("", registration.read_text(encoding="utf-8"))
            for match in _REGISTRATION.finditer(text):
                name = match.group("name")
                sources = _SOURCE.findall(match.group("arguments"))
                found.setdefault(name, Example(name, self._brief_of(registration, name, sources)))
        return list(found.values())

    def _registration_files(self) -> list[Path]:
        """Returns every registration file under the folder, shallowest first."""
        if not self._examples_dir.is_dir():
            return []
        files = [
            Path(directory) / K_REGISTRATION_FILE
            for directory, _, names in os.walk(self._examples_dir)
            if K_REGISTRATION_FILE in names
        ]
        return sorted(files, key=lambda path: (len(path.parts), path.as_posix()))

    @staticmethod
    def _brief_of(registration: Path, name: str, sources: list[str]) -> str:
        """Returns the `@brief` of the source the target is named after, or of its first."""
        named = [
            source for source in sources
            if name == Path(source).stem or name.endswith("_" + Path(source).stem)
        ]
        for source in named or sources[:1]:
            path = registration.parent / source
            if path.is_file():
                found = _BRIEF.search(path.read_text(encoding="utf-8"))
                return _CONTINUATION.sub(" ", found.group("text")).strip() if found else ""
        return ""
