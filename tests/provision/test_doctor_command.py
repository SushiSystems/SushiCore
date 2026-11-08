# test_doctor_command.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests running a module's checks and how the run is reported."""

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.profile import ModuleProfile
from sushicore.provision import doctor_command
from sushicore.provision.module_provision import ModuleProvision


def _binary_module(console):
    """Return a binary install of a module whose console is *console*."""
    profile = ModuleProfile(name="sushidsp", program="sd", env_prefix="SD", root_marker="m")
    return ModuleProvision(profile=profile, project_root=lambda: Path("."), load_config=lambda: None,
                           console=lambda: console, is_binary=lambda: True)


def _tables(console):
    """Return the arguments of every table the recording console took."""
    return [args for name, args in console.calls if name == "table"]


@pytest.mark.small
def test_a_binary_install_runs_the_python_check():
    """Check that a binary install runs the python check and titles its table Doctor."""
    console = RecordingConsole()
    outcome = doctor_command.run_doctor(_binary_module(console), None)
    assert _tables(console)[0][2] == "Doctor"
    assert [check["name"] for check in outcome.payload["checks"]] == ["python"]


@pytest.mark.small
def test_a_binary_install_reports_success_when_the_python_check_passes():
    """Check that the outcome's flag agrees with its exit code."""
    outcome = doctor_command.run_doctor(_binary_module(RecordingConsole()), None)
    assert outcome.ok == (outcome.code == 0)


@pytest.mark.small
def test_the_run_draws_the_table_once_and_leaves_the_result_to_the_caller():
    """Check that the run draws one table and no result event."""
    console = RecordingConsole()
    doctor_command.run_doctor(_binary_module(console), None)
    assert (len(_tables(console)), [name for name, _ in console.calls if name == "result"]) == (1, [])
