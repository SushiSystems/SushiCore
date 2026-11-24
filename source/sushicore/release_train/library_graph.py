# library_graph.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Reads which Sushi library pins which, and orders a release so each library follows what it pins."""

from __future__ import annotations

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import final

from ..files import Files
from .errors import ReleaseTrainError

#: The file of a library that pins the Sushi libraries below it.
K_PINS_FILE = Path("cli/sushistack.deps.toml")
#: The table of that file that holds the Sushi pins.
K_PINS_TABLE = "sushisystems"


@final
@dataclass(frozen=True, slots=True)
class LibraryGraph:
    """The Sushi libraries of a workspace and the libraries each one pins.

    Attributes:
        pins: For each library, by folder name, the libraries it pins.
    """

    pins: Mapping[str, frozenset[str]]

    @staticmethod
    def read(workspace: Path, files: Files) -> "LibraryGraph":
        """Return the graph of every folder of *workspace* that holds a pins file."""
        pins: dict[str, frozenset[str]] = {}
        for folder in files.children(workspace):
            path = folder / K_PINS_FILE
            if files.is_file(path):
                table = tomllib.loads(files.read_text(path)).get(K_PINS_TABLE, {})
                pins[folder.name] = frozenset(table)
        return LibraryGraph(pins)

    def train(self, changed: Iterable[str]) -> list[str]:
        """Return *changed* and every library that pins one of them, each after what it pins.

        Raises ReleaseTrainError when a name is no library of the graph or the pins form a cycle.
        """
        start = set(changed)
        unknown = sorted(start - set(self.pins))
        if unknown:
            raise ReleaseTrainError(f"no library {', '.join(unknown)} in the workspace")
        members = set(start)
        grew = True
        while grew:
            above = {name for name, below in self.pins.items() if below & members} - members
            members |= above
            grew = bool(above)
        ordered: list[str] = []
        while len(ordered) < len(members):
            ready = sorted(name for name in members - set(ordered)
                           if not (self.pins[name] & members) - set(ordered))
            if not ready:
                raise ReleaseTrainError(f"the pins of {', '.join(sorted(members - set(ordered)))} form a cycle")
            ordered.extend(ready)
        return ordered
