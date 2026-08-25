"""Locate built executables under a build tree.

Every Sushi* CLI has to answer the same question -- "which of the files under
``build/`` is a program I can run?" -- and every one of them answered it with
its own copy of this walk. The copies drifted only in one place: which sibling
directories to skip, because a module that builds a dependency in-tree must not
offer that dependency's executables as its own.

So the walk lives here and the skip list is the caller's, supplied once when it
builds an :class:`ExecutableIndex`. Nothing else about the search is
configurable, which is the point: `sr run`, `se run`, `sa run` and `sb run`
should not be able to disagree about what counts as an executable.
"""

from __future__ import annotations

import os
import platform
from pathlib import Path
from typing import Protocol

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

    console: object  # a rich.console.Console, for printing a renderable

    def error(self, message: str) -> None: ...


def _is_executable(path: Path) -> bool:
    """Whether *path* is a runnable program rather than a build artifact."""
    if not path.is_file():
        return False
    name = path.name
    if name.startswith("."):
        return False
    # *.so / *.so.1 style shared objects on Linux: the suffix check below misses
    # the versioned ones, so match the substring.
    if ".so" in name:
        return False
    if path.suffix.lower() in _SKIP_SUFFIXES:
        return False
    if _IS_WINDOWS:
        return path.suffix.lower() == ".exe"
    # Linux: a regular file carrying an execute bit and no library suffix.
    return os.access(path, os.X_OK)


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

    def select(self, build_root: Path, console: ConsoleLike) -> Path | None:
        """Print a table of executables and prompt for one. None if there are none."""
        # Imported here, not at module scope: `find`/`match` are used on every
        # `run` and must not pay for rich's table machinery to be imported.
        from rich.prompt import IntPrompt
        from rich.table import Table

        exes = self.find(build_root)
        if not exes:
            console.error("No executables found. Build the project first.")
            return None

        table = Table(title="Available executables", show_lines=False)
        table.add_column("#", justify="right", style="cyan")
        table.add_column("Name", style="bold")
        table.add_column("Path", style="dim")
        for i, exe in enumerate(exes, 1):
            table.add_row(str(i), exe.name, str(exe.relative_to(build_root.parent)))
        console.console.print(table)

        choice = IntPrompt.ask(
            "Select a number", choices=[str(i) for i in range(1, len(exes) + 1)]
        )
        return exes[choice - 1]
