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
from .program_cases import may_hold_a_case, suites_by_program
from .shard_registrations import ShardRegistration, shard_registrations
from .shards import gtest_results_folder


def run_filtered_shards(module: ModuleTests, tree: Path, selection: LabelSelection, user_filter: str, *,
                        jobs: int, repeat: int, shuffle_seed: int | None, junit: Path, files: Files) -> int:
    """Run the selected shards of *tree* under *user_filter* through the module's ``run_program``.

    A shard runs with the filter narrowed to the cases its filter and *user_filter* both
    select; a shard that cannot hold such a case is not run. *repeat* runs the cases of each
    shard that many times, once when 0.

    Returns 0 when every shard that ran passed, otherwise 1.
    """
    suites = suites_by_program(tree, files)
    runs = [(shard, narrowed) for shard in shard_registrations(tree, files) if selection.selects(shard.labels)
            if may_hold_a_case(suites.get(shard.program), user_filter)
            for narrowed in [intersect_filters(shard.size_filter, user_filter)] if narrowed is not None]
    console = module.console()
    if not runs:
        console.warn(f"No shard can hold a case that matches '{user_filter}'; nothing ran.")
    accelerated = [run for run in runs if run[0].needs_accelerator]
    alone = [run for run in runs if not run[0].needs_accelerator]

    def run_in_turn(queue: list[tuple[ShardRegistration, str]]) -> list[int]:
        return [_run_shard(module, tree, shard, narrowed, repeat, shuffle_seed) for shard, narrowed in queue]

    with ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        in_turn = pool.submit(run_in_turn, accelerated)
        alone_codes = list(pool.map(lambda run: _run_shard(module, tree, run[0], run[1], repeat, shuffle_seed), alone))
        codes_of = dict(zip((id(run) for run in alone), alone_codes))
        codes_of.update(zip((id(run) for run in accelerated), in_turn.result()))
    codes = [codes_of[id(run)] for run in runs]
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
