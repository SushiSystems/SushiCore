# test_job_resolution.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that the job count is the flag, else the config key, else the default."""

import pytest

from sushicore import build_admission
from sushicore.job_resolution import resolve_jobs

pytestmark = pytest.mark.small


@pytest.fixture(autouse=True)
def _sixteen_threads(monkeypatch):
    monkeypatch.delenv("CMAKE_BUILD_PARALLEL_LEVEL", raising=False)
    monkeypatch.setattr(build_admission.os, "cpu_count", lambda: 16)


def test_an_explicit_count_wins_over_the_config_key_and_the_default():
    assert resolve_jobs(3, 9) == 3


def test_a_config_key_wins_over_the_default_when_no_flag_is_given():
    assert resolve_jobs(None, 9) == 9


@pytest.mark.parametrize("configured", [None, 0])
def test_no_flag_and_no_config_key_take_the_threads_less_four(configured):
    assert resolve_jobs(None, configured) == 12
