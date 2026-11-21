# discovery.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Locates the built executables under a build tree.

The reasoning is in docs/architecture/OVERVIEW.md, section `discovery`.
"""

from __future__ import annotations

import os
import platform
from pathlib import Path
from typing import Protocol, final

from .example_catalog import Example, ExampleCatalog

_DEFAULT_MAX_DEPTH = 4

# Build-system bookkeeping, never a program the user asked for.
_BUILD_SYSTEM_DIRS = frozenset({"CMakeFiles", "vcpkg_installed", "_deps"})

_SKIP_SUFFIXES = frozenset({
    ".cmake", ".ninja", ".log", ".txt", ".json", ".a", ".o",
    ".cmake_install", ".lib", ".pdb", ".obj", ".dll", ".so",
})

_IS_WINDOWS = platform.system().lower() == "windows"


class ConsoleLike(Protocol):
    """The slice of a CLI's console module :meth:`ExecutableIndex.select` needs.

    Declared structurally so sushicore never imports a specific CLI's console:
    the dependency points from each CLI into this package, never back.
    """

    def error(self, message: str) -> None:
        """Prints an error line."""

    def table(self, columns: list[str], rows: list[list[str]], title: str = "") -> None:
        """Prints a table of *rows* under *columns*."""

    def prompt(self, message: str, default: str | None = None) -> str:
        """Asks *message* and returns the answer, or *default*."""


def _is_executable(path: Path) -> bool:
    """Whether *path* is a runnable program rather than a build artifact."""
    if not path.is_file():
        return False
    name = path.name
    if name.startswith("."):
        return False
    # A versioned shared object such as libx.so.1 has no ".so" suffix; match the substring.
    if ".so" in name:
        return False
    if path.suffix.lower() in _SKIP_SUFFIXES:
        return False
    if _IS_WINDOWS:
        return path.suffix.lower() == ".exe"
    # Linux: a regular file carrying an execute bit and no library suffix.
    return os.access(path, os.X_OK)


@final
class ExecutableIndex:
    """Finds runnable programs under a build tree, skipping what the CLI names.

    *skip_dirs* are directory names pruned from the walk in addition to the
    build system's own bookkeeping -- in practice the sibling module checkouts
    this project builds in-tree (sushiengine skips ``sushiruntime``; sushiai
    skips that and ``sushiblas``). Names, not paths: the walk prunes by
    directory name at any depth.
    """

    __slots__ = ("_skip_dirs", "_max_depth")

    def __init__(self, *, skip_dirs: object = (), max_depth: int = _DEFAULT_MAX_DEPTH) -> None:
        self._skip_dirs = _BUILD_SYSTEM_DIRS | frozenset(skip_dirs)  # type: ignore[arg-type]
        self._max_depth = max_depth

    def find(self, build_root: Path) -> list[Path]:
        """Return candidate executables under *build_root*, depth-limited.

        Sorted by lowercased name so the numbering `select` prints is stable
        across runs and across platforms.
        """
        if not build_root.is_dir():
            return []
        found: list[Path] = []
        root_depth = len(build_root.parts)
        for dirpath, dirnames, filenames in os.walk(build_root):
            depth = len(Path(dirpath).parts) - root_depth
            if depth >= self._max_depth:
                dirnames[:] = []
            dirnames[:] = [d for d in dirnames if d not in self._skip_dirs]
            for fname in filenames:
                candidate = Path(dirpath) / fname
                if _is_executable(candidate):
                    found.append(candidate)
        return sorted(found, key=lambda p: p.name.lower())

    def match(self, build_root: Path, query: str) -> Path | None:
        """Exact name (or stem) match, falling back to a substring match."""
        exes = self.find(build_root)
        for exe in exes:
            if exe.name == query or exe.stem == query:
                return exe
        for exe in exes:
            if query.lower() in exe.name.lower():
                return exe
        return None

    def select(self, build_root: Path, console: ConsoleLike, *,
               examples: ExampleCatalog | None = None) -> Path | None:
        """Print a table of executables and prompt for one. None if there are none.

        With *examples* the table lists the built examples, each with its brief, in the order
        the repository registers them. A build that has none lists every executable instead.
        """
        exes = self.find(build_root)
        if not exes:
            console.error("No executables found. Build the project first.")
            return None

        built = self._built_examples(exes, examples) if examples is not None else []
        if built:
            return self._offer(
                console, ["#", "Name", "What it does"],
                [[example.name, example.brief] for example, _ in built],
                [path for _, path in built],
                f"Examples ({len(built)} of {len(exes)} programs)")
        return self._offer(
            console, ["#", "Name", "Path"],
            [[exe.name, str(exe.relative_to(build_root.parent))] for exe in exes],
            exes, "Available executables")

    @staticmethod
    def _built_examples(exes: list[Path], examples: ExampleCatalog) -> list[tuple[Example, Path]]:
        """Return each registered example that has a built executable, in registration order."""
        paths = {exe.stem: exe for exe in exes}
        return [(example, paths[example.name])
                for example in examples.entries() if example.name in paths]

    @staticmethod
    def _offer(console: ConsoleLike, columns: list[str], rows: list[list[str]],
               choices: list[Path], title: str) -> Path | None:
        """Print *rows* numbered under *columns* and return the choice the user numbers."""
        console.table(columns, [[str(i), *row] for i, row in enumerate(rows, 1)], title=title)
        answer = console.prompt("Select a number").strip()
        if not answer.isdigit() or not 1 <= int(answer) <= len(choices):
            console.error(f"'{answer}' is not a number from 1 to {len(choices)}.")
            return None
        return choices[int(answer) - 1]

    def resolve(self, build_root: Path, console: ConsoleLike, *, target: str | None = None,
                sort: bool = False, default: str = "",
                examples: ExampleCatalog | None = None, list_all: bool = False) -> Path | None:
        """The executable a `run` command should launch, or None with the reason printed.

        *sort* means "let me pick", an explicit *target* wins over everything else, and *default*,
        a CLI's configured ``target_bin``, runs when neither was given. When picking, *examples*
        limits the choice to the built examples and *list_all* offers every executable anyway.
        Every failing path prints one message and returns None.
        """
        if sort:
            return self.select(build_root, console, examples=None if list_all else examples)

        if target:
            exe = self.match(build_root, target)
            if exe is None:
                console.error(f"Executable matching '{target}' not found.")
            return exe

        exe = self.match(build_root, default)
        if exe is None:
            console.error(f"Default target '{default}' not found.")
        return exe
