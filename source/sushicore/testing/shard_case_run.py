# shard_case_run.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Runs some cases of one shard through its program, as the shard runs them under CTest."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from ..files import Files
from .module_tests import ModuleTests
from .shard_registrations import shard_registrations
from .shards import program_of

#: The variables that split a program's cases into shards; a rerun of named cases runs them all.
K_SHARD_VARIABLES = frozenset({"GTEST_TOTAL_SHARDS", "GTEST_SHARD_INDEX"})


def run_shard_cases(module: ModuleTests, tree: Path, files: Files, shard: str, cases: Sequence[str],
                    report: Path) -> int:
    """Run the *cases* of the shard *shard* and write their GoogleTest XML to *report*.

    The program gets the arguments, the environment and the timeout the shard registers, so it
    starts as it does under CTest, apart from the sharding variables: the filter already names
    each case. A shard the tree no longer registers runs with none of them.

    Returns:
        The exit code of the program.
    """
    registration = next((entry for entry in shard_registrations(tree, files) if entry.name == shard), None)
    arguments = [f"--gtest_filter={':'.join(cases)}", f"--gtest_output=xml:{report}"]
    if registration is None:
        return module.run_program(program_of(shard), arguments)
    return module.run_program(registration.program, [*arguments, *registration.arguments],
                              env={name: value for name, value in registration.environment.items()
                                   if name not in K_SHARD_VARIABLES}, timeout=registration.timeout)
