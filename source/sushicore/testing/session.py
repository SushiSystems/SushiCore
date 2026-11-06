# session.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Runs the tests of a module's build tree and prints the budget line of the run."""

from __future__ import annotations

import inspect
import random
import time
from pathlib import Path
from typing import Callable, Optional

from ..files import DiskFiles, Files
from .budget import print_budget, scope_of
from .labels import LabelSelection, large_needs_a_filter
from .module_tests import ModuleTests

#: The exit code of a request the command could not act on, as for every shared command.
K_EXIT_UNUSABLE = 2

#: The range of seeds GoogleTest accepts.
K_SEED_MIN = 1
K_SEED_MAX = 99999


class _Stop(Exception):
    """Ends a run before CTest starts, with the exit code to return."""

    def __init__(self, code: int) -> None:
        super().__init__(code)
        self.code = code


def run_tests(module: ModuleTests, selection: LabelSelection, *, name_filter: Optional[str] = None,
              repeat: int = 0, jobs: Optional[int] = None, every_size: bool = False,
              sanitizer: Optional[str] = None, own_tests: bool = False,
              shuffle: bool = True, seed: Optional[int] = None,
              files: Files | None = None, seed_source: Callable[[int, int], int] | None = None) -> int:
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
        shuffle: Runs the tests of each program in a random order; the seed is printed.
        seed: The shuffle seed, to repeat an order; a new random one when None.
        files: The file system the tree check, the JUnit file and the budget reader are looked for in; the disk when None.
        seed_source: Draws a seed between its two bounds when *seed* is None; ``random.randint`` when None.

    Returns:
        CTest's exit code, or 2 when the request cannot be acted on.
    """
    files = files if files is not None else DiskFiles()
    console = module.console()
    try:
        if own_tests:
            ignored = [flag for flag, given in (("--filter", name_filter), ("--repeat", repeat),
                                                ("--jobs", jobs), ("--all", every_size),
                                                ("--sanitize", sanitizer)) if given]
            return _run_own_tests(module, selection, ignored)
        if large_needs_a_filter(selection, filtered=bool(name_filter), every_size=every_size):
            raise _refuse(module, "The large tests need real hardware. Narrow the run with --filter, "
                                  "or pass --all to run every size.")
        tree = _tree_of(module, sanitizer, files)
    except _Stop as stop:
        return stop.code

    junit = (tree / "Testing" / "junit.xml").resolve()
    files.write_text(junit, "")
    files.remove(junit)
    console.info("Labels: " + ", ".join(
        [size.value for size in selection.sizes] + (["quarantined"] if selection.quarantined else [])))
    shuffle_seed = (seed if seed is not None else (seed_source or random.randint)(K_SEED_MIN, K_SEED_MAX)) if shuffle else None
    if shuffle_seed is not None:
        console.info(f"Shuffle seed: {shuffle_seed} (repeat with --seed {shuffle_seed})")
    keywords = dict(label_regex=selection.ctest_include(), exclude_label_regex=selection.ctest_exclude(),
                    filter=name_filter, repeat=repeat, jobs=jobs, output_junit=junit)
    if shuffle_seed is not None:
        if _takes_shuffle_seed(module.run_ctest):
            keywords["shuffle_seed"] = shuffle_seed
        else:
            console.warn("This CLI's CTest call cannot take a shuffle seed, so the tests run in their given order.")
    started = time.monotonic()
    code = module.run_ctest(tree, **keywords)
    scope = scope_of(selection, filtered=bool(name_filter), every_size=every_size, repeated=repeat > 0)
    rebuilt = sanitizer is not None or (module.rebuilt is not None and module.rebuilt(tree))
    print_budget(module, junit, scope, time.monotonic() - started, rebuilt, files=files)
    if code != 0:
        console.error(f"Tests failed (exit {code}).")
    return code


def _takes_shuffle_seed(run_ctest) -> bool:
    """Returns whether the CTest call of a module accepts ``shuffle_seed``, by name or through ``**keywords``."""
    try:
        parameters = inspect.signature(run_ctest).parameters.values()
    except (TypeError, ValueError):
        return False
    return any(parameter.name == "shuffle_seed" or parameter.kind is inspect.Parameter.VAR_KEYWORD
               for parameter in parameters)


def _refuse(module: ModuleTests, message: str) -> _Stop:
    """Says *message* as an error and returns the stop that ends the run with the usage code."""
    module.console().error(message)
    return _Stop(K_EXIT_UNUSABLE)


def _run_own_tests(module: ModuleTests, selection: LabelSelection, ignored: list[str]) -> int:
    """Run the module's pytest suite, or refuse when the module has none or an option would be dropped."""
    if module.cli_tests is None:
        raise _refuse(module, f"{module.profile.program} has no tests of its own to run with --cli.")
    if ignored:
        raise _refuse(module, "--cli runs the pytest suite for the labels alone; "
                              f"it cannot take {', '.join(ignored)}.")
    return module.cli_tests(selection)


def _tree_of(module: ModuleTests, sanitizer: Optional[str], files: Files) -> Path:
    """Returns the tree to test, building the sanitizer's first; raises a stop when it cannot be tested."""
    tree = module.build_tree() if sanitizer is None else _sanitized_tree(module, sanitizer)
    if not files.is_dir(tree):
        raise _refuse(module, f"{tree} not found. Run `{module.profile.program} build` first.")
    fault = module.check_tree(tree)
    if fault:
        raise _refuse(module, fault)
    return tree


def _sanitized_tree(module: ModuleTests, sanitizer: str) -> Path:
    """Builds the tree of *sanitizer*, matched to the module's names without regard to case, and returns it."""
    names = {name.lower(): name for name in module.sanitized.names} if module.sanitized else {}
    if sanitizer.lower() not in names:
        raise _refuse(module, f"{module.profile.program} cannot test the sanitizer '{sanitizer}'; "
                              f"it builds: {', '.join(names.values()) or 'none'}.")
    name = names[sanitizer.lower()]
    code = module.sanitized.build(name)
    if code != 0:
        raise _Stop(code)
    return module.sanitized.tree(name)
