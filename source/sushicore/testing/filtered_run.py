# filtered_run.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Runs the shards of a build under a case filter of the caller, which CTest cannot narrow."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ..files import Files
from .gtest_filter import intersect_filters
from .junit_report import junit_text
from .labels import LabelSelection
from .module_tests import ModuleTests
from .shard_registrations import ShardRegistration, shard_registrations
from .shards import gtest_results_folder


def run_filtered_shards(module: ModuleTests, tree: Path, selection: LabelSelection, user_filter: str, *,
                        jobs: int, repeat: int, shuffle_seed: int | None, junit: Path, files: Files) -> int:
    """Run the selected shards of *tree* under *user_filter* through the module's ``run_program``.

    A shard registers its own ``--gtest_filter``, which GoogleTest ranks above any variable, so the
    shard's program is run here with the filter narrowed to the cases the shard's filter and
    *user_filter* both select. A shard that cannot hold such a case is not run. Each shard keeps its
    sharding variables and its timeout, writes its GoogleTest XML to the results folder, and its
    exit code goes into the JUnit file *junit*.

    Args:
        module: What the module CLI hands the command; its ``run_program`` must be set.
        tree: The built tree.
        selection: The labels to run.
        user_filter: The GoogleTest filter the caller asked for.
        jobs: How many shards run at once.
        repeat: Runs the cases of each shard this many times; once when 0.
        shuffle_seed: The shuffle seed handed to each shard, or None for no shuffle.
        junit: The JUnit file to write.
        files: The file system the registrations are read from and the JUnit file is written to.

    Returns:
        0 when every shard that ran passed, otherwise 1.
    """
    runs = [(shard, narrowed) for shard in shard_registrations(tree, files) if selection.selects(shard.labels)
            for narrowed in [intersect_filters(shard.size_filter, user_filter)] if narrowed is not None]
    console = module.console()
    if not runs:
        console.warn(f"No shard can hold a case that matches '{user_filter}'; nothing ran.")
    with ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        codes = list(pool.map(lambda run: _run_shard(module, tree, run[0], run[1], repeat, shuffle_seed), runs))
    files.write_text(junit, junit_text({shard.name: code for (shard, _), code in zip(runs, codes)}))
    return 0 if all(code == 0 for code in codes) else 1


def _run_shard(module: ModuleTests, tree: Path, shard: ShardRegistration, narrowed: str, repeat: int,
               shuffle_seed: int | None) -> int:
    """Run one shard under the filter *narrowed* and return its exit code."""
    environment = dict(shard.environment)
    if shuffle_seed is not None:
        environment.update(GTEST_SHUFFLE="1", GTEST_RANDOM_SEED=str(shuffle_seed))
    arguments = [f"--gtest_filter={narrowed}", *shard.arguments,
                 f"--gtest_output=xml:{gtest_results_folder(tree) / (shard.name + '.xml')}"]
    if repeat > 0:
        arguments.append(f"--gtest_repeat={repeat}")
    return module.run_program(shard.program, arguments, env=environment, timeout=shard.timeout)
