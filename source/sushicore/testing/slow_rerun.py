# slow_rerun.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Reruns the tests a run found over their time limit, one at a time, so their time alone is judged."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path

from ..files import Files
from .module_tests import ModuleTests
from .result_files import ResultFileError, case_names
from .shards import gtest_results_folder, program_of, slow_results_folder


class SlowTestRerun:
    """Reruns the tests of one run that were over a time limit, alone.

    A case of a shard reruns through its program, its cases of one shard in one process with no other
    test running, and writes GoogleTest XML. Any other test reruns through CTest with one job and writes
    JUnit. A shard case whose module cannot run its program is not rerun, and the reader judges its
    time in the run.

    Args:
        module: What the module CLI hands the command.
        tree: The built tree the run tested.
        files: The file system the result files are read from and cleared in.
    """

    def __init__(self, module: ModuleTests, tree: Path, files: Files) -> None:
        self._module = module
        self._tree = tree
        self._files = files

    def rerun(self, names: Sequence[str]) -> tuple[Path, ...]:
        """Rerun the tests *names* alone and return the result files and folders the rerun wrote."""
        if not names:
            return ()
        folder = slow_results_folder(self._tree)
        for stale in self._files.children(folder):
            self._files.remove(stale)
        shard_of = self._shard_of_each_case()
        by_shard: dict[str, list[str]] = defaultdict(list)
        whole: list[str] = []
        for name in names:
            if name in shard_of:
                by_shard[shard_of[name]].append(name)
            elif program_of(name) is None:
                whole.append(name)
        self._module.console().info(f"Rerunning {len(names)} test(s) over a time limit alone, one at a time.")
        written: list[Path] = []
        if by_shard and self._module.run_program is not None:
            for shard, cases in by_shard.items():
                self._module.run_program(program_of(shard), [f"--gtest_filter={':'.join(cases)}",
                                                             f"--gtest_output=xml:{folder / (shard + '.xml')}"])
            written.append(folder)
        if whole:
            junit = self._tree / "Testing" / "slow_junit.xml"
            self._files.remove(junit)
            pattern = "^(" + "|".join(re.escape(name) for name in whole) + ")$"
            self._module.run_ctest(self._tree, label_regex=None, exclude_label_regex=None, filter=pattern,
                                   repeat=0, jobs=1, output_junit=junit)
            if self._files.is_file(junit):
                written.append(junit)
        return tuple(written)

    def _shard_of_each_case(self) -> dict[str, str]:
        """Return the shard each case of the run ran in, read from the shards' GoogleTest XML files."""
        shard_of: dict[str, str] = {}
        for path in self._files.children(gtest_results_folder(self._tree)):
            if path.suffix != ".xml" or program_of(path.stem) is None:
                continue
            try:
                for case in case_names(self._files.read_text(path)):
                    shard_of[case] = path.stem
            except ResultFileError:
                continue
        return shard_of
