# session.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Runs the tests of a module's build tree and judges the run by its time limits."""

from __future__ import annotations

import inspect
import random
import time
from pathlib import Path
from typing import Callable, Optional

from ..build_admission import default_jobs
from ..memory_reading import free_memory_mb
from ..files import DiskFiles, Files
from .accelerator_slots import write_resource_spec
from .budget import judge_run, scope_of
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
    """Signals the end of a run before CTest starts, with the exit code to return; not a failure."""

    def __init__(self, code: int) -> None:
        super().__init__(code)
        self.code = code


K_UNJUDGED_TEXT = "The time limits are not judged under a sanitizer, which slows every test."


def run_tests(module: ModuleTests, selection: LabelSelection, *, name_filter: Optional[str] = None,
              repeat: int = 0, jobs: Optional[int] = None, every_size: bool = False,
              sanitizer: Optional[str] = None, own_tests: bool = False,
              shuffle: bool = True, seed: Optional[int] = None,
              files: Files | None = None, seed_source: Callable[[int, int], int] | None = None,
              default_count: Callable[[], int] = default_jobs,
              free_memory: Callable[[], int] = free_memory_mb) -> int:
    """Run the tests *selection* names over the module's tree, then judge the run by its time limits.

    A sanitized run is not judged by them: a sanitizer makes every test several times slower, and its
    oracle is the report it prints, not the clock.

    Args:
        name_filter: A CTest ``-R`` pattern; a GoogleTest filter over sharded tests.
        repeat: Reruns each test up to this many times, stopping at its first failure.

    Returns CTest's exit code when not 0, else the budget's: 1 or 2.
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
        choice = choose_jobs(default_count(), free_memory(), share_of(selection.sizes))
        console.info(choice.line())
        jobs = choice.jobs
    shuffle_seed = (seed if seed is not None else (seed_source or random.randint)(K_SEED_MIN, K_SEED_MAX)) if shuffle else None
    if shuffle_seed is not None:
        console.info(f"Shuffle seed: {shuffle_seed} (repeat with --seed {shuffle_seed})")
    rebuilt = sanitizer is not None or (module.rebuilt is not None and module.rebuilt(tree))
    started = time.monotonic()
    if name_filter and module.run_program is not None and registers_shards(tree, files):
        code = run_filtered_shards(module, tree, selection, name_filter, jobs=jobs, repeat=repeat,
                                   shuffle_seed=shuffle_seed, junit=junit, files=files)
    else:
        code = _run_ctest(module, tree, selection, name_filter, repeat, jobs, shuffle_seed, junit, files)
    scope = scope_of(selection, filtered=bool(name_filter), every_size=every_size, repeated=repeat > 0)
    outcome = _rerun_failures(module, tree, junit, files) if code != 0 else K_NOTHING_RERUN
    if sanitizer is None:
        budget = judge_run(module, tree, junit, scope, time.monotonic() - started, rebuilt, files=files,
                           cases=results, rerun=outcome.results)
    else:
        console.info(K_UNJUDGED_TEXT)
        budget = 0
    if code != 0:
        console.error(f"Tests failed (exit {code}).")
        return code
    return budget


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
    if _takes(module.run_ctest, "resource_spec_file"):
        keywords["resource_spec_file"] = write_resource_spec(tree, files)
    else:
        console.warn("This CLI's CTest call cannot take a resource file, so device shards may share a device.")
    if shuffle_seed is not None:
        if _takes(module.run_ctest, "shuffle_seed"):
            keywords["shuffle_seed"] = shuffle_seed
        else:
            console.warn("This CLI's CTest call cannot take a shuffle seed, so the tests run in their given order.")
    return module.run_ctest(tree, **keywords)


def _takes(run_ctest: Callable[..., int], keyword: str) -> bool:
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
