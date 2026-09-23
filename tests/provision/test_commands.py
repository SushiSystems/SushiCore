# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the setup/doctor/link/unlink commands."""

from __future__ import annotations

import typer
from typer.testing import CliRunner

from sushicore.profile import ModuleProfile
from sushicore.provision.commands import ModuleProvision, register_provision_commands
from sushicore.provision.config import ProvisionSettings
from sushicore.workspace import registered_modules


def _app(tmp_path, recording_console):
    profile = ModuleProfile(name="sushidsp", program="sd", env_prefix="SD",
                            root_marker="sushidsp.marker")
    app = typer.Typer()

    @app.callback()
    def _root():
        """Test app."""

    register_provision_commands(app, ModuleProvision(
        profile=profile, project_root=lambda: tmp_path / "dsp",
        load_config=lambda: ProvisionSettings(platform="linux"),
        console=lambda: recording_console))
    return app


def test_link_and_unlink_without_hub(tmp_path, recording_console):
    ws = tmp_path / "ws"
    (ws / ".sushistack").mkdir(parents=True)
    app = _app(tmp_path, recording_console)
    runner = CliRunner()
    assert runner.invoke(app, ["link", "--workspace", str(ws)]).exit_code == 0
    assert registered_modules(ws) == {"sushidsp": str(tmp_path / "dsp").replace("\\", "/")}
    assert runner.invoke(app, ["unlink", "--workspace", str(ws)]).exit_code == 0
    assert registered_modules(ws) == {}


def test_link_outside_a_workspace_exits_two(tmp_path, recording_console, monkeypatch):
    monkeypatch.delenv("SUSHISTACK_HOME", raising=False)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(_app(tmp_path, recording_console), ["link"])
    assert result.exit_code == 2


def test_doctor_filters_by_group(tmp_path, recording_console):
    result = CliRunner().invoke(_app(tmp_path, recording_console), ["doctor", "--for", "infer"])
    assert result.exit_code == 0
