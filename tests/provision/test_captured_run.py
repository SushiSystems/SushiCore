# test_captured_run.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The deprecated package_install helpers still run a command and warn."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from sushicore.provision.package_install import CapturedRun, capture_command, run_command

pytestmark = pytest.mark.medium


def test_capture_command_returns_the_code_and_the_output_and_warns(tmp_path: Path):
    """Check that a captured run keeps its output and warns as deprecated."""
    with pytest.warns(DeprecationWarning):
        done = capture_command([sys.executable, "-c", "print('hi')"], tmp_path)
    assert done == CapturedRun(0, "hi\n") or (done.code == 0 and "hi" in done.output)


def test_run_command_returns_the_exit_code_and_warns(tmp_path: Path):
    """Check that a run answers the child's exit code."""
    with pytest.warns(DeprecationWarning):
        assert run_command([sys.executable, "-c", "raise SystemExit(3)"], tmp_path) == 3


def test_a_missing_executable_answers_127(tmp_path: Path):
    """Check that a command that cannot start answers 127, as before."""
    with pytest.warns(DeprecationWarning):
        assert capture_command(["no-such-program-xyz"], tmp_path).code == 127
