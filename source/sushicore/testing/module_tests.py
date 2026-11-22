# module_tests.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What one module CLI hands the shared ``test`` command."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Protocol, final

from ..profile import ModuleProfile
from .labels import LabelSelection


class TestConsole(Protocol):
    """The three console methods the command prints through."""

    __test__ = False

    def info(self, text: str) -> None:
        """Prints an info line."""

    def warn(self, text: str) -> None:
        """Prints a warning line."""

    def error(self, text: str) -> None:
        """Prints an error line."""


@final
@dataclass(frozen=True)
class SanitizedTests:
    """The sanitizer builds a module can test.

    Args:
        names: The values ``--sanitize`` accepts, such as ``address`` and ``thread``.
        build: Builds the tree of one sanitizer and returns the exit code of the build.
        tree: The built tree of one sanitizer.
    """

    names: tuple[str, ...]
    build: Callable[[str], int]
    tree: Callable[[str], Path]


def _tree_is_fine(tree: Path) -> Optional[str]:
    """Report no fault in the build tree *tree*."""
    del tree
    return None


@final
@dataclass(frozen=True)
class ModuleTests:
    """What one module CLI hands the shared ``test`` command.

    Args:
        profile: Names the module and its program.
        project_root: The checkout the budget reader and the exemption file are looked for in.
        build_tree: The built tree CTest runs over.
        run_ctest: Runs CTest over a tree and returns its exit code.
        run_program: Runs one of the module's programs by its CTest test name; None when none.
        configured_jobs: Reads the ``build_jobs`` config key when the command runs; None or 0 for none.
    """

    profile: ModuleProfile
    project_root: Callable[[], Path]
    console: Callable[[], TestConsole]
    build_tree: Callable[[], Path]
    run_ctest: Callable[..., int]
    run: Callable[[list[str], Path], int]
    check_tree: Callable[[Path], Optional[str]] = _tree_is_fine
    panel: Optional[str] = None
    sanitized: Optional[SanitizedTests] = None
    cli_tests: Optional[Callable[[LabelSelection], int]] = None
    rebuilt: Optional[Callable[[Path], bool]] = None
    run_program: Optional[Callable[..., int]] = None
    configured_jobs: Callable[[], Optional[int]] = lambda: None
