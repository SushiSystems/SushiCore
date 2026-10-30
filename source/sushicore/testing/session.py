# session.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Runs the tests of a module's build tree and prints the budget line of the run."""

from __future__ import annotations

import time
from typing import Optional

from .budget import large_needs_a_filter, reader_command, scope_of
from .labels import LabelSelection
from .module_tests import ModuleTests

#: The exit code of a request the command could not act on, as for every shared command.
K_EXIT_UNUSABLE = 2


def run_tests(module: ModuleTests, selection: LabelSelection, *, name_filter: Optional[str] = None,
              repeat: int = 0, jobs: Optional[int] = None, every_size: bool = False) -> int:
    """Run the tests *selection* names over the module's tree, then print the budget line.

    The budget line is a report: it never changes the exit code, which is CTest's.

    Args:
        module: What the module CLI hands the command.
        selection: The labels to run.
        name_filter: A CTest ``-R`` pattern over ``Suite.Case`` names.
        repeat: Reruns each test up to this many times, stopping at its first failure.
        jobs: How many tests run at once.
        every_size: Whether the run was asked for every size, which allows the ``large`` tests unfiltered.

    Returns:
        CTest's exit code, or 2 when the request cannot be acted on.
    """
    console = module.console()
    if large_needs_a_filter(selection, filtered=bool(name_filter), every_size=every_size):
        console.error("The large tests need real hardware. Narrow the run with --filter, "
                      "or pass --all to run every size.")
        return K_EXIT_UNUSABLE
    tree = module.build_tree()
    if not tree.is_dir():
        console.error(f"{tree} not found. Run `{module.profile.program} build` first.")
        return K_EXIT_UNUSABLE
    fault = module.check_tree(tree)
    if fault:
        console.error(fault)
        return K_EXIT_UNUSABLE

    junit = (tree / "Testing" / "junit.xml").resolve()
    junit.parent.mkdir(parents=True, exist_ok=True)
    junit.unlink(missing_ok=True)
    console.info("Labels: " + ", ".join(
        [size.value for size in selection.sizes] + (["quarantined"] if selection.quarantined else [])))
    started = time.monotonic()
    code = module.run_ctest(
        tree, label_regex=selection.ctest_include(), exclude_label_regex=selection.ctest_exclude(),
        filter=name_filter, repeat=repeat, jobs=jobs, output_junit=junit)
    wall_seconds = time.monotonic() - started
    _print_budget(module, junit, scope_of(selection, filtered=bool(name_filter), every_size=every_size,
                                          repeated=repeat > 0), wall_seconds)
    if code != 0:
        console.error(f"Tests failed (exit {code}).")
    return code


def _print_budget(module: ModuleTests, junit, scope: str, wall_seconds: float) -> None:
    """Print the budget line of a run when the repository carries the reader and the run wrote a file."""
    root = module.project_root()
    command = reader_command(root, junit, scope, wall_seconds)
    if command is None:
        return
    console = module.console()
    if not junit.is_file():
        console.warn("The run wrote no JUnit file, so the budget line is skipped.")
        return
    if module.run(command, root) != 0:
        console.warn("The budget reader failed; the run's own result is unchanged.")
