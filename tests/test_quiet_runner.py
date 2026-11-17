# test_quiet_runner.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the runner of a caller that shows no output."""

import sys

import pytest

from sushicore.quiet_runner import quiet_runner


@pytest.mark.small
def test_a_quiet_runner_captures_without_printing(capfd):
    code, stdout, _ = quiet_runner().capture([sys.executable, "-c", "print('seen')"])
    assert (code, stdout.strip(), capfd.readouterr().out) == (0, "seen", "")
