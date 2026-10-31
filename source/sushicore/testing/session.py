# session.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Runs the tests of a module's build tree and prints the budget line of the run."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

from .budget import print_budget, scope_of
from .labels import LabelSelection, large_needs_a_filter
from .module_tests import ModuleTests

#: The exit code of a request the command could not act on, as for every shared command.
K_EXIT_UNUSABLE = 2


class _Stop(Exception):
    """Ends a run before CTest starts, with the exit code to return."""

    def __init__(self, code: int) -> None:
        super().__init__(code)
        self.code = code


def run_tests(module: ModuleTests, selection: LabelSelection, *, name_filter: Optional[str] = None,
              repeat: int = 0, jobs: Optional[int] = None, every_size: bool = False,
              sanitizer: Optional[str] = None, own_tests: bool = False) -> int:
    """Run the tests *selection* names over the module's tree, then print the budget line.

    The budget line is a report: it never changes the exit code, which is CTest's.

    Args:
        module: What the module CLI hands the command.
        selection: The labels to run.
        name_filter: A CTest ``-R`` pattern over ``Suite.Case`` names.
        repeat: Reruns each test up to this many times, stopping at its first failure.
        jobs: How many tests run at once.
        every_size: Whether the run was asked for every size, which allows the ``large`` tests unfiltered.
        sanitizer: Builds the tree of this sanitizer first and tests it, instead of the plain tree.
        own_tests: Runs the module's own pytest suite for *selection* instead of CTest.

    Returns:
        CTest's exit code, or 2 when the request cannot be acted on.
    """
    console = module.console()
    try:
        if own_tests:
            return _run_own_tests(module, selection)
        if large_needs_a_filter(selection, filtered=bool(name_filter), every_size=every_size):
            raise _refuse(module, "The large tests need real hardware. Narrow the run with --filter, "
                                  "or pass --all to run every size.")
        tree = _tree_of(module, sanitizer)
    except _Stop as stop:
        return stop.code

    junit = (tree / "Testing" / "junit.xml").resolve()
    junit.parent.mkdir(parents=True, exist_ok=True)
    junit.unlink(missing_ok=True)
    console.info("Labels: " + ", ".join(
        [size.value for size in selection.sizes] + (["quarantined"] if selection.quarantined else [])))
    started = time.monotonic()
    code = module.run_ctest(
        tree, label_regex=selection.ctest_include(), exclude_label_regex=selection.ctest_exclude(),
        filter=name_filter, repeat=repeat, jobs=jobs, output_junit=junit)
    scope = scope_of(selection, filtered=bool(name_filter), every_size=every_size, repeated=repeat > 0)
    print_budget(module, junit, scope, time.monotonic() - started)
    if code != 0:
        console.error(f"Tests failed (exit {code}).")
    return code


def _refuse(module: ModuleTests, message: str) -> _Stop:
    """Says *message* as an error and returns the stop that ends the run with the usage code."""
    module.console().error(message)
    return _Stop(K_EXIT_UNUSABLE)


def _run_own_tests(module: ModuleTests, selection: LabelSelection) -> int:
    """Run the module's pytest suite, or refuse when the module has none."""
    if module.cli_tests is None:
        raise _refuse(module, f"{module.profile.program} has no tests of its own to run with --cli.")
    return module.cli_tests(selection)


def _tree_of(module: ModuleTests, sanitizer: Optional[str]) -> Path:
    """Returns the tree to test, building the sanitizer's first; raises a stop when it cannot be tested."""
    if sanitizer is None:
        tree = module.build_tree()
    else:
        if module.sanitized is None or sanitizer.lower() not in module.sanitized.names:
            known = ", ".join(module.sanitized.names) if module.sanitized else "none"
            raise _refuse(module, f"{module.profile.program} cannot test the sanitizer '{sanitizer}'; "
                                  f"it builds: {known}.")
        code = module.sanitized.build(sanitizer.lower())
        if code != 0:
            raise _Stop(code)
        tree = module.sanitized.tree(sanitizer.lower())
    if not tree.is_dir():
        raise _refuse(module, f"{tree} not found. Run `{module.profile.program} build` first.")
    fault = module.check_tree(tree)
    if fault:
        raise _refuse(module, fault)
    return tree
