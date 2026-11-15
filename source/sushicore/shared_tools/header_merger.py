# header_merger.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Puts a shared file under the license header of the repository that receives it."""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

from .licence_toolkit import LicenceToolkit

K_SETTINGS = "tools/settings.py"
K_HEADER_TEMPLATE = "tools/check_all.py"
K_HEADER_SUFFIX = ".py"
K_PROJECT_ROW = 1
K_YEAR = re.compile(r"Copyright \(c\) (\d{4})-present")


def split_header(text: str) -> tuple[str, str]:
    """Returns the leading run of comment lines of a Python file and the rest."""
    lines = text.splitlines(keepends=True)
    count = 0
    while count < len(lines) and lines[count].startswith("#"):
        count += 1
    return "".join(lines[:count]), "".join(lines[count:])


def first_year(this_year: int, *texts: str | None) -> int:
    """Returns the year of the first copyright row found in the texts, or this_year."""
    for text in texts:
        found = K_YEAR.search(text or "")
        if found:
            return int(found.group(1))
    return this_year


class HeaderMerger:
    """Builds the text of a shared file under the header of one repository."""

    def __init__(self, toolkit: LicenceToolkit, root: Path) -> None:
        """Reads the repository's template header and settings once."""
        self._toolkit = toolkit
        self._template = _read(root / K_HEADER_TEMPLATE)
        self._header = self._target_header(root)
        self._neutral = toolkit.header("", toolkit.licence("", "", "", (), (), (), (), False))

    def merged(self, relative: str, upstream: str, current: str | None, year: int) -> str:
        """Returns a shared file as the repository should hold it: upstream's body under its own header.

        A Python file the repository does not hold yet takes the header of its template, one of its own
        shared files, with the first line naming the new file. Any other source file takes the block the
        repository's settings build, dated *year*.
        """
        if self._toolkit.is_source(relative) and not relative.endswith(K_HEADER_SUFFIX):
            if self._header is None:
                return upstream
            return self._toolkit.rewrite(relative, upstream, self._header, year)
        if not relative.endswith(K_HEADER_SUFFIX):
            return upstream
        if current is not None:
            return split_header(current)[0] + split_header(upstream)[1]
        if self._template is None:
            return upstream
        rows = split_header(self._template)[0].splitlines(keepends=True)
        if not rows:
            return upstream
        rows[0] = f"# {Path(relative).name}\n"
        return "".join(rows) + split_header(upstream)[1]

    def body(self, relative: str, text: str) -> str:
        """Returns what a shared file says apart from its license block and its newline style."""
        if relative.endswith(K_HEADER_SUFFIX):
            body = split_header(text)[1]
        elif self._toolkit.is_source(relative):
            body = self._toolkit.rewrite(relative, text, self._neutral, 0)
        else:
            body = text
        return body.replace("\r\n", "\n")

    def _target_header(self, root: Path) -> object | None:
        """Returns the block the repository's own settings and template header describe, or None."""
        settings_path = root / K_SETTINGS
        if self._template is None or not settings_path.is_file():
            return None
        rows = split_header(self._template)[0].splitlines()
        if len(rows) <= K_PROJECT_ROW:
            return None
        spec = importlib.util.spec_from_file_location("target_settings", settings_path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        licence = self._toolkit.from_module(module)
        if licence is None:
            return None
        return self._toolkit.header(
            rows[K_PROJECT_ROW].removeprefix("#").strip(), licence, closed=licence.closed
        )


def _read(path: Path) -> str | None:
    """Returns a file's text, or None when it does not exist."""
    return path.read_text(encoding="utf-8") if path.is_file() else None
