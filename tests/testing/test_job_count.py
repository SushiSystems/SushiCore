# test_job_count.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the job count a test run chooses when it is given none."""

import pytest

from sushicore.build_gate import K_RESERVE_MB
from sushicore.testing.job_count import K_TEST_SHARE_MB, choose_jobs

pytestmark = pytest.mark.small


def test_one_job_per_core_when_the_memory_holds_them():
    assert choose_jobs(8, K_RESERVE_MB + 8 * K_TEST_SHARE_MB).jobs == 8


def test_the_count_falls_when_the_memory_holds_fewer_shares_than_cores():
    assert choose_jobs(32, K_RESERVE_MB + 3 * K_TEST_SHARE_MB + 10).jobs == 3


def test_a_machine_short_of_memory_still_runs_one_job():
    assert choose_jobs(8, 0).jobs == 1


def test_a_machine_that_cannot_count_its_cores_runs_one_job():
    assert choose_jobs(None, 100000).jobs == 1


def test_the_line_names_the_count_and_what_bounded_it():
    line = choose_jobs(8, 100000).line()
    assert line.startswith("Jobs: 8 (cores 8, free memory 100000 MB")
