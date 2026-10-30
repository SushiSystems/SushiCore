# test_doctor_command.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests running a module's checks and how the run is reported."""

from pathlib import Path

import pytest

from sushicore.profile import ModuleProfile
from sushicore.provision import doctor_command
from sushicore.provision.module_provision import ModuleProvision


pytestmark = pytest.mark.small


class _Console:
    def __init__(self):
        self.tables = []

    def table(self, columns, rows, title=""):
        self.tables.append((columns, rows, title))

    def error(self, text):
        pass


def _binary_module(console):
    profile = ModuleProfile(name="sushidsp", program="sd", env_prefix="SD", root_marker="m")
    return ModuleProvision(profile=profile, project_root=lambda: Path("."), load_config=lambda: None,
                           console=lambda: console, is_binary=lambda: True)


def test_a_binary_install_runs_the_python_check_and_reports_its_payload():
    console = _Console()
    outcome = doctor_command.run_doctor(_binary_module(console), None)
    assert console.tables[0][2] == "Doctor"
    assert [check["name"] for check in outcome.payload["checks"]]
    assert outcome.ok == (outcome.code == 0)


def test_the_run_draws_the_table_once_and_leaves_the_result_to_the_caller():
    console = _Console()
    doctor_command.run_doctor(_binary_module(console), None)
    assert len(console.tables) == 1
