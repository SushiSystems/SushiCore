# session.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Runs the tests of a module's build tree and prints the budget line of the run."""

from __future__ import annotations

import inspect
import os
import random
import time
from pathlib import Path
from typing import Callable, Optional

from ..memory_reading import free_memory_mb
from ..files import DiskFiles, Files
from .budget import print_budget, scope_of
from .filtered_run import run_filtered_shards
from .job_count import choose_jobs, share_of
from .labels import LabelSelection, large_needs_a_filter
from .module_tests import ModuleTests
from .rerun import K_NOTHING_RERUN, FailedTestRerun, RerunOutcome
from .result_files import ResultFileError, failed_tests
from .shards import gtest_results_folder, registers_shards

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
              files: Files | None = None, seed_source: Callable[[int, int], int] | None = None,
              cpu_count: Callable[[], int | None] = os.cpu_count,
              free_memory: Callable[[], int] = free_memory_mb) -> int:
    """Run the tests *selection* names over the module's tree, then print the budget line.

    The budget line is a report: it never changes the exit code, which is CTest's.

    Args:
        module: What the module CLI hands the command.
        selection: The labels to run.
        name_filter: A CTest ``-R`` pattern over ``Suite.Case`` names; over a build that registers its
            cases in shards, a GoogleTest filter. A module with a ``run_program`` runs the selected shards
            itself, each under its size filter narrowed by this one; any other module's shards receive it
            as ``GTEST_FILTER``.
        repeat: Reruns each test up to this many times, stopping at its first failure.
        jobs: How many tests run at once; one per core, lowered to fit the free memory of the selected
            sizes, when None.
        every_size: Whether the run was asked for every size, which allows the ``large`` tests unfiltered.
        sanitizer: Builds the tree of this sanitizer first and tests it, instead of the plain tree.
        own_tests: Runs the module's own pytest suite for *selection* instead of CTest.
        shuffle: Runs the tests of each program in a random order; the seed is printed.
        seed: The shuffle seed, to repeat an order; a new random one when None.
        files: The file system the tree check, the JUnit file and the budget reader are looked for in; the disk when None.
        seed_source: Draws a seed between its two bounds when *seed* is None; ``random.randint`` when None.
        cpu_count: Reports the cores of the machine; ``os.cpu_count`` by default.
        free_memory: Reports the free physical memory in megabytes; the build gate's reader by default.

    A failed test is rerun once, alone, before the budget line, and one that passes on the rerun is
    reported flaky; the exit code stays CTest's. The per-case times of the shards, which a run over
    sharded tests writes as GoogleTest XML, join the budget line.

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
    results = gtest_results_folder(tree)
    for stale in files.children(results):
        files.remove(stale)
    console.info("Labels: " + ", ".join(
        [size.value for size in selection.sizes] + (["quarantined"] if selection.quarantined else [])))
    if jobs is None:
        choice = choose_jobs(cpu_count(), free_memory(), share_of(selection.sizes))
        console.info(choice.line())
        jobs = choice.jobs
    shuffle_seed = (seed if seed is not None else (seed_source or random.randint)(K_SEED_MIN, K_SEED_MAX)) if shuffle else None
    if shuffle_seed is not None:
        console.info(f"Shuffle seed: {shuffle_seed} (repeat with --seed {shuffle_seed})")
    started = time.monotonic()
    if name_filter and module.run_program is not None and registers_shards(tree, files):
        code = run_filtered_shards(module, tree, selection, name_filter, jobs=jobs, repeat=repeat,
                                   shuffle_seed=shuffle_seed, junit=junit, files=files)
    else:
        code = _run_ctest(module, tree, selection, name_filter, repeat, jobs, shuffle_seed, junit, files)
    scope = scope_of(selection, filtered=bool(name_filter), every_size=every_size, repeated=repeat > 0)
    rebuilt = sanitizer is not None or (module.rebuilt is not None and module.rebuilt(tree))
    outcome = _rerun_failures(module, tree, junit, files) if code != 0 else K_NOTHING_RERUN
    print_budget(module, junit, scope, time.monotonic() - started, rebuilt, files=files,
                 cases=results, rerun=outcome.results)
    if code != 0:
        console.error(f"Tests failed (exit {code}).")
    return code


def _run_ctest(module: ModuleTests, tree: Path, selection: LabelSelection, name_filter: Optional[str],
               repeat: int, jobs: int, shuffle_seed: Optional[int], junit: Path, files: Files) -> int:
    """Run the module's CTest call over *tree* and return its exit code."""
    console = module.console()
    keywords = dict(label_regex=selection.ctest_include(), exclude_label_regex=selection.ctest_exclude(),
                    filter=name_filter, repeat=repeat, jobs=jobs, output_junit=junit)
    if name_filter and registers_shards(tree, files):
        if _takes(module.run_ctest, "gtest_filter"):
            keywords.update(filter=None, gtest_filter=name_filter)
        else:
            console.warn("This CLI's CTest call cannot take a GoogleTest filter, so --filter names CTest "
                         "tests, and the tests are shards.")
    if shuffle_seed is not None:
        if _takes(module.run_ctest, "shuffle_seed"):
            keywords["shuffle_seed"] = shuffle_seed
        else:
            console.warn("This CLI's CTest call cannot take a shuffle seed, so the tests run in their given order.")
    return module.run_ctest(tree, **keywords)


def _takes(run_ctest, keyword: str) -> bool:
    """Returns whether the CTest call of a module accepts *keyword*, by name or through ``**keywords``."""
    try:
        parameters = inspect.signature(run_ctest).parameters.values()
    except (TypeError, ValueError):
        return False
    return any(parameter.name == keyword or parameter.kind is inspect.Parameter.VAR_KEYWORD
               for parameter in parameters)


def _rerun_failures(module: ModuleTests, tree: Path, junit: Path, files: Files) -> RerunOutcome:
    """Rerun the tests that failed in the run whose JUnit file is *junit*, and say what came of it."""
    console = module.console()
    try:
        failed = failed_tests(files.read_text(junit)) if files.is_file(junit) else ()
    except ResultFileError as error:
        console.warn(f"The failed tests are not rerun: {error}.")
        return K_NOTHING_RERUN
    outcome = FailedTestRerun(module, tree, files).rerun(failed)
    if outcome.flaky:
        console.warn("Flaky, failed in the run and passed alone: " + ", ".join(outcome.flaky))
    if outcome.failing:
        console.warn("Failed again alone: " + ", ".join(outcome.failing))
    return outcome


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
