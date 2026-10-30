# module_tests.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""What one module CLI hands the shared ``test`` command."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from ..profile import ModuleProfile


def _tree_is_fine(tree: Path) -> Optional[str]:
    """Report no fault in the build tree *tree*."""
    del tree
    return None


@dataclass(frozen=True)
class ModuleTests:
    """What one module CLI hands the shared ``test`` command.

    Args:
        profile: Names the module and its program.
        project_root: The checkout the budget reader and the exemption file are looked for in.
        console: Returns the console the command prints through.
        build_tree: The built tree CTest runs over.
        run_ctest: Runs CTest over a tree with the module's environment. It takes the tree and the
            keywords ``label_regex``, ``exclude_label_regex``, ``filter``, ``repeat``, ``jobs`` and
            ``output_junit``, and returns CTest's exit code.
        run: Runs a command in a folder and returns its exit code; the budget reader goes through it.
        check_tree: Names a fault of the tree, such as a stale configuration, or returns None.
        panel: The help panel the command is listed under, or None for the default.
    """

    profile: ModuleProfile
    project_root: Callable[[], Path]
    console: Callable[[], object]
    build_tree: Callable[[], Path]
    run_ctest: Callable[..., int]
    run: Callable[[list[str], Path], int]
    check_tree: Callable[[Path], Optional[str]] = _tree_is_fine
    panel: Optional[str] = None
