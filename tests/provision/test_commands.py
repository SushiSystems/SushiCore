# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the setup/doctor/link/unlink commands."""

from __future__ import annotations

import os

import typer
from typer.testing import CliRunner

from sushicore.profile import ModuleProfile
from sushicore.provision import commands, probe
from sushicore.provision.commands import ModuleProvision, register_provision_commands
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.lock import ProvisionLock
from sushicore.provision.packages import LinuxPackageManager
from sushicore.workspace import registered_modules


class _FakeAptManager(LinuxPackageManager):
    """A Linux package manager stand-in that reports success without shelling out."""

    name = "apt"

    def available(self) -> bool:
        """Report itself as always present."""
        return True

    def is_installed(self, pkg: str) -> bool:
        """Report every package as already installed."""
        return True

    def install(self, pkgs: list[str], dry_run: bool) -> bool:
        """Report every install as successful, without running one."""
        return True


def _write_fragment(root):
    """Write a minimal ``sushistack.deps.toml`` fragment under *root*'s cli/ directory."""
    fragment = root / "cli" / "sushistack.deps.toml"
    fragment.parent.mkdir(parents=True, exist_ok=True)
    fragment.write_text(
        '[widget]\ndescription = "test widget"\nlinux_apt = ["widget-dev"]\n', encoding="utf-8")
    return fragment


def _table_rows(calls, header):
    """Return the rows of the first recorded ``console.table`` call with *header*."""
    for name, args in calls:
        if name == "table" and args and args[0] == header:
            return args[1]
    raise AssertionError(f"no table call with header {header} in {calls}")


def _quiet_setup(monkeypatch, provision_home, managers):
    """Silence the pieces of ``setup`` a unit test must not depend on.

    Fakes the package managers, skips the standard doctor checks (which read this
    machine's real toolchain), turns off the progress bar (which needs a real Rich
    console, not the recording fake), and creates the dependency root the lock file
    is written under.
    """
    monkeypatch.setattr(commands, "_managers_for", lambda cfg: managers)
    monkeypatch.setattr(commands, "standard_checks", lambda cfg, fix: [])
    monkeypatch.setattr(commands, "_SHOW_PROGRESS", False)
    provision_home.mkdir(parents=True, exist_ok=True)


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


def test_setup_dry_run_detects_the_module_fragment_and_writes_nothing(
        tmp_path, recording_console, provision_home, monkeypatch):
    _quiet_setup(monkeypatch, provision_home, managers=[])
    root = tmp_path / "dsp"
    _write_fragment(root)

    result = CliRunner().invoke(_app(tmp_path, recording_console), ["setup", "--dry-run"])

    assert result.exit_code == 0
    rows = _table_rows(recording_console.calls, ["Component", "Status", "Owner", "Detail"])
    widget_row = next(row for row in rows if row[0] == "widget")
    assert widget_row[2] == "sushidsp"
    assert not (root / "cli" / "config.local.toml").exists()
    assert {p.name for p in root.iterdir()} == {"cli"}
    assert {p.name for p in (root / "cli").iterdir()} == {"sushistack.deps.toml"}


def test_setup_writes_the_module_sink_without_dry_run(
        tmp_path, recording_console, provision_home, monkeypatch):
    _quiet_setup(monkeypatch, provision_home, managers=[_FakeAptManager()])
    monkeypatch.setattr(probe, "resolve_local_config", lambda cfg, gpu: {"cmake_exe": "/x/cmake"})
    root = tmp_path / "dsp"
    _write_fragment(root)

    result = CliRunner().invoke(_app(tmp_path, recording_console), ["setup"])

    assert result.exit_code == 0
    written = root / "cli" / "config.local.toml"
    assert written.is_file()
    assert 'cmake_exe = "/x/cmake"' in written.read_text(encoding="utf-8")


def test_setup_exits_one_when_the_lock_is_held(
        tmp_path, recording_console, provision_home, monkeypatch):
    _quiet_setup(monkeypatch, provision_home, managers=[])
    monkeypatch.setattr(commands, "_LOCK_TIMEOUT", 0.2)
    root = tmp_path / "dsp"
    _write_fragment(root)

    holder = ProvisionLock(provision_home / ".lock")
    with holder:
        result = CliRunner().invoke(_app(tmp_path, recording_console), ["setup", "--dry-run"])

    assert result.exit_code == 1
    errors = [args[0] for name, args in recording_console.calls if name == "error"]
    assert any(str(os.getpid()) in message for message in errors)


def test_setup_exits_one_when_a_step_fails(
        tmp_path, recording_console, provision_home, monkeypatch):
    # No linux package manager is available, so InstallDepsStep reports StepResult.FAILED.
    _quiet_setup(monkeypatch, provision_home, managers=[])
    root = tmp_path / "dsp"
    _write_fragment(root)

    result = CliRunner().invoke(_app(tmp_path, recording_console), ["setup"])

    assert result.exit_code == 1
