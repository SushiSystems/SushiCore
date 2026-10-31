# budget.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Decides the scope of a test run and builds the command of the budget reader a repository carries."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from .labels import K_DEFAULT_LABELS, LabelSelection
from .module_tests import ModuleTests

#: Where the shared budget reader sits below a repository root.
K_READER = Path("tools") / "testing" / "test_budget.py"

#: Where a repository lists the tests that already break a limit, below its root.
K_EXEMPTIONS = Path("tests") / "budget_exemptions.toml"


def scope_of(selection: LabelSelection, *, filtered: bool, every_size: bool, repeated: bool) -> str:
    """Returns the scope the budget reader judges a run by.

    ``default`` is the run of ``small`` and ``medium`` that nothing narrowed, ``large`` is a run of every
    size, and ``partial`` is any other, whose totals never gate.

    Args:
        selection: The labels the run selected.
        filtered: Whether a name filter narrowed the run.
        every_size: Whether the run was asked for every size.
        repeated: Whether the run repeated its tests.
    """
    if filtered or repeated:
        return "partial"
    if every_size:
        return "large"
    if selection.sizes == K_DEFAULT_LABELS and not selection.quarantined:
        return "default"
    return "partial"


def reader_command(root: Path, junit: Path, scope: str, wall_seconds: float) -> Optional[list[str]]:
    """Returns the command that prints the budget line of a run, or None when the root carries no reader.

    Args:
        root: The repository root.
        junit: The JUnit file the run wrote.
        scope: What :func:`scope_of` returned.
        wall_seconds: The wall time of the whole run.
    """
    reader = root / K_READER
    if not reader.is_file():
        return None
    command = [sys.executable, str(reader), str(junit), "--scope", scope,
               "--wall", f"{wall_seconds:.1f}", "--root", str(root)]
    if (root / K_EXEMPTIONS).is_file():
        command += ["--exemptions", str(root / K_EXEMPTIONS)]
    return command


def print_budget(module: ModuleTests, junit: Path, scope: str, wall_seconds: float) -> None:
    """Print the budget line of a run through the module's runner.

    Nothing is printed when the repository carries no reader. A run that wrote no JUnit file, and a reader
    that fails, are said in a warning and change nothing else.
    """
    root = module.project_root()
    command = reader_command(root, junit, scope, wall_seconds)
    if command is None:
        return
    console = module.console()
    if not junit.is_file():
        console.warn("The run wrote no JUnit file, so the budget line is skipped.")
    elif module.run(command, root) != 0:
        console.warn("The budget reader failed; the run's own result is unchanged.")
