# rerun.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Reruns the tests that failed in a run once, alone, and tells a flaky one from a failing one."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from ..files import Files
from .module_tests import ModuleTests
from .result_files import ResultFileError, failed_tests, failing_cases
from .shards import gtest_results_folder, program_of, rerun_results_folder


@dataclass(frozen=True, slots=True)
class RerunOutcome:
    """What the rerun of the failed tests of a run found.

    Attributes:
        results: The folder of GoogleTest XML files, or the JUnit file, the rerun wrote; None when
            nothing was rerun. The budget reader takes it as ``--rerun``.
        flaky: The tests and cases that failed in the run and passed alone.
        failing: The tests and cases that failed again alone.
    """

    results: Path | None
    flaky: tuple[str, ...]
    failing: tuple[str, ...]


K_NOTHING_RERUN = RerunOutcome(results=None, flaky=(), failing=())


class FailedTestRerun:
    """Reruns the failed tests of one run, once each, alone.

    A failed shard reruns only its failing cases, by ``--gtest_filter`` on its program, so the
    passing cases are not paid for again. Any other failed test, and a shard whose failing cases
    cannot be read or whose module cannot run its program, reruns whole through CTest.

    Args:
        module: What the module CLI hands the command.
        tree: The built tree the run tested.
        files: The file system the result files are read from and cleared in.
    """

    def __init__(self, module: ModuleTests, tree: Path, files: Files) -> None:
        self._module = module
        self._tree = tree
        self._files = files

    def rerun(self, failed: Sequence[str]) -> RerunOutcome:
        """Rerun the failed CTest tests *failed* alone once, and return what came of it."""
        if not failed:
            return K_NOTHING_RERUN
        folder = rerun_results_folder(self._tree)
        for stale in self._files.children(folder):
            self._files.remove(stale)
        by_case: dict[str, tuple[str, ...]] = {}
        whole: list[str] = []
        for name in failed:
            cases = self._failing_cases_of(name)
            if cases:
                by_case[name] = cases
            else:
                whole.append(name)
        self._module.console().info(f"Rerunning {len(failed)} failed test(s) once, alone.")
        flaky: list[str] = []
        failing: list[str] = []
        for shard, cases in by_case.items():
            passed = self._rerun_cases(shard, cases, folder) == 0
            (flaky if passed else failing).extend(cases)
        junit = self._tree / "Testing" / "rerun_junit.xml"
        if whole:
            still_failing = self._rerun_whole(whole, junit)
            flaky.extend(name for name in whole if name not in still_failing)
            failing.extend(name for name in whole if name in still_failing)
        results = folder if by_case else junit
        return RerunOutcome(results=results, flaky=tuple(flaky), failing=tuple(failing))

    def _failing_cases_of(self, name: str) -> tuple[str, ...]:
        """Return the failing cases of the shard *name*, or none when it is no shard or they cannot be read."""
        if program_of(name) is None or self._module.run_program is None:
            return ()
        report = gtest_results_folder(self._tree) / f"{name}.xml"
        if not self._files.is_file(report):
            return ()
        try:
            return failing_cases(self._files.read_text(report))
        except ResultFileError:
            return ()

    def _rerun_cases(self, shard: str, cases: Sequence[str], folder: Path) -> int:
        """Run the *cases* of *shard* alone through the module's program and return its exit code."""
        report = folder / f"{shard}.xml"
        return self._module.run_program(program_of(shard), [f"--gtest_filter={':'.join(cases)}",
                                                            f"--gtest_output=xml:{report}"])

    def _rerun_whole(self, names: Sequence[str], junit: Path) -> frozenset[str]:
        """Rerun the CTest tests *names* alone, one job, and return the ones that failed again."""
        self._files.remove(junit)
        pattern = "^(" + "|".join(re.escape(name) for name in names) + ")$"
        self._module.run_ctest(self._tree, label_regex=None, exclude_label_regex=None, filter=pattern,
                               repeat=0, jobs=1, output_junit=junit)
        if not self._files.is_file(junit):
            return frozenset(names)
        try:
            return frozenset(failed_tests(self._files.read_text(junit)))
        except ResultFileError:
            return frozenset(names)
