# test_commands.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
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
from sushicore.workspace import read_link, registered_modules, write_module


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
    machine's real toolchain) and turns off the progress bar (which needs a real Rich
    console, not the recording fake).
    """
    monkeypatch.setattr(commands, "_managers_for", lambda cfg: managers)
    monkeypatch.setattr(commands, "standard_checks", lambda cfg, fix: [])
    monkeypatch.setattr(commands, "_SHOW_PROGRESS", False)


def _app(tmp_path, recording_console, **overrides):
    """Return an app carrying the provision commands, *overrides* passed to ModuleProvision."""
    profile = ModuleProfile(name="sushidsp", program="sd", env_prefix="SD",
                            root_marker="sushidsp.marker")
    app = typer.Typer()

    @app.callback()
    def _root():
        """Test app."""

    register_provision_commands(app, ModuleProvision(
        profile=profile, project_root=lambda: tmp_path / "dsp",
        load_config=lambda: ProvisionSettings(platform="linux"),
        console=lambda: recording_console, **overrides))
    return app


def test_link_and_unlink_without_hub(tmp_path, recording_console):
    """Check that link and unlink without hub."""
    ws = tmp_path / "ws"
    (ws / ".sushistack").mkdir(parents=True)
    (tmp_path / "dsp" / "cli").mkdir(parents=True)
    app = _app(tmp_path, recording_console)
    runner = CliRunner()
    assert runner.invoke(app, ["link", "--workspace", str(ws)]).exit_code == 0
    assert registered_modules(ws) == {"sushidsp": str(tmp_path / "dsp").replace("\\", "/")}
    assert read_link(tmp_path / "dsp" / "cli") == ws.resolve()
    assert runner.invoke(app, ["unlink", "--workspace", str(ws)]).exit_code == 0
    assert registered_modules(ws) == {}
    assert read_link(tmp_path / "dsp" / "cli") is None


def test_link_outside_a_workspace_exits_two(tmp_path, recording_console, monkeypatch):
    """Check that link outside a workspace exits two."""
    monkeypatch.delenv("SUSHISTACK_HOME", raising=False)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(_app(tmp_path, recording_console), ["link"])
    assert result.exit_code == 2
    assert not (tmp_path / "dsp" / "cli" / "config.local.toml").exists()


def test_doctor_filters_by_group(tmp_path, recording_console):
    """Check that doctor filters by group."""
    result = CliRunner().invoke(_app(tmp_path, recording_console), ["doctor", "--for", "infer"])
    assert result.exit_code == 0


def test_doctor_rejects_an_unknown_group(tmp_path, recording_console):
    """Check that doctor rejects an unknown group."""
    result = CliRunner().invoke(_app(tmp_path, recording_console), ["doctor", "--for", "typo"])
    assert result.exit_code == 2
    errors = [args[0] for name, args in recording_console.calls if name == "error"]
    assert any("build" in e and "eval" in e and "typo" in e for e in errors)


def test_doctor_reports_the_module_fragment_and_toolchain_stamps(
        tmp_path, recording_console, provision_home, monkeypatch):
    """Check that doctor reports the module fragment and toolchain stamps."""
    monkeypatch.setattr(commands, "standard_checks", lambda cfg, fix: [])
    fragment = tmp_path / "dsp" / "cli" / "sushistack.deps.toml"
    fragment.parent.mkdir(parents=True)
    fragment.write_text(
        '[widget]\nlinux_apt = ["widget-dev"]\ncheck_cmd = ["sushi-no-such-tool-xyz"]\n',
        encoding="utf-8")
    (provision_home / "toolchains" / "llvm-sycl").mkdir(parents=True)

    result = CliRunner().invoke(_app(tmp_path, recording_console), ["doctor"])

    assert result.exit_code == 1
    rows = _table_rows(recording_console.calls, ["Check", "Group", "Result", "Detail", "Fix"])
    by_name = {row[0]: row for row in rows}
    assert "widget" in by_name["dependencies"][3]
    assert "llvm-sycl" in by_name["toolchain stamps"][3]


def test_setup_dry_run_detects_the_module_fragment_and_writes_nothing(
        tmp_path, recording_console, provision_home, monkeypatch):
    """Check that setup dry run detects the module fragment and writes nothing."""
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
    """Check that setup writes the module sink without dry run."""
    _quiet_setup(monkeypatch, provision_home, managers=[_FakeAptManager()])
    monkeypatch.setattr(probe, "resolve_local_config", lambda cfg, gpu: {"cmake_exe": "/x/cmake"})
    root = tmp_path / "dsp"
    _write_fragment(root)

    result = CliRunner().invoke(_app(tmp_path, recording_console), ["setup"])

    assert result.exit_code == 0
    written = root / "cli" / "config.local.toml"
    assert written.is_file()
    assert 'cmake_exe = "/x/cmake"' in written.read_text(encoding="utf-8")


def test_setup_dry_run_prints_the_probed_config_and_writes_nothing(
        tmp_path, recording_console, provision_home, monkeypatch):
    """Check that setup dry run prints the probed config and writes nothing."""
    _quiet_setup(monkeypatch, provision_home, managers=[])
    monkeypatch.setattr(probe, "resolve_local_config", lambda cfg, gpu: {"cmake_exe": "/x/cmake"})
    root = tmp_path / "dsp"
    _write_fragment(root)

    result = CliRunner().invoke(_app(tmp_path, recording_console), ["setup", "--dry-run"])

    assert result.exit_code == 0, result.exception
    printed = [args[0] for name, args in recording_console.calls if name == "console.print"]
    assert any('cmake_exe = "/x/cmake"' in text for text in printed)
    assert not (root / "cli" / "config.local.toml").exists()


def test_setup_creates_a_missing_dependency_root(
        tmp_path, recording_console, provision_home, monkeypatch):
    """Check that setup creates a missing dependency root."""
    _quiet_setup(monkeypatch, provision_home, managers=[])
    root = tmp_path / "dsp"
    _write_fragment(root)
    assert not provision_home.exists()

    result = CliRunner().invoke(_app(tmp_path, recording_console), ["setup", "--dry-run"])

    assert result.exit_code == 0, result.exception
    assert (provision_home / ".lock").is_file()


def test_setup_exits_one_when_the_lock_is_held(
        tmp_path, recording_console, provision_home, monkeypatch):
    """Check that setup exits one when the lock is held."""
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
    """Check that setup exits one when a step fails."""
    # No linux package manager is available, so InstallDepsStep reports StepResult.FAILED.
    _quiet_setup(monkeypatch, provision_home, managers=[])
    root = tmp_path / "dsp"
    _write_fragment(root)

    result = CliRunner().invoke(_app(tmp_path, recording_console), ["setup"])

    assert result.exit_code == 1


def test_setup_builds_the_package_managers_once(
        tmp_path, recording_console, provision_home, monkeypatch):
    """Check that setup builds the package managers once."""
    _quiet_setup(monkeypatch, provision_home, managers=[])
    built = []
    monkeypatch.setattr(commands, "_managers_for", lambda cfg: built.append(cfg) or [])
    _write_fragment(tmp_path / "dsp")

    CliRunner().invoke(_app(tmp_path, recording_console), ["setup", "--dry-run"])

    assert len(built) == 1


def _mixed_case_app(tmp_path, recording_console):
    """Return an app whose profile carries a display name in mixed case."""
    profile = ModuleProfile(name="SushiDSP", program="sd", env_prefix="SD",
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


def test_link_records_the_lower_cased_key(tmp_path, recording_console):
    """Check that link records the lower cased key."""
    ws = tmp_path / "ws"
    (ws / ".sushistack").mkdir(parents=True)
    (tmp_path / "dsp" / "cli").mkdir(parents=True)
    app = _mixed_case_app(tmp_path, recording_console)
    assert CliRunner().invoke(app, ["link", "--workspace", str(ws)]).exit_code == 0
    assert list(registered_modules(ws)) == ["sushidsp"]


def test_unlink_removes_an_entry_written_under_the_display_name(tmp_path, recording_console):
    """Check that unlink removes an entry written under the display name."""
    ws = tmp_path / "ws"
    (ws / ".sushistack").mkdir(parents=True)
    (tmp_path / "dsp" / "cli").mkdir(parents=True)
    write_module(ws, "SushiDSP", tmp_path / "dsp")
    app = _mixed_case_app(tmp_path, recording_console)
    assert CliRunner().invoke(app, ["unlink", "--workspace", str(ws)]).exit_code == 0
    assert registered_modules(ws) == {}


def _sibling_locator(tmp_path):
    """Return a locator finding modules as directories under *tmp_path*."""
    def locate(name):
        """Return the sibling directory when it exists."""
        path = tmp_path / name
        return path if path.is_dir() else None
    return locate


def _depending_fragment(root, depends_on):
    """Write a fragment under *root* that depends on *depends_on* and declares a widget."""
    fragment = _write_fragment(root)
    names = ", ".join(f'"{name}"' for name in depends_on)
    fragment.write_text(f"[module]\ndepends_on = [{names}]\n"
                        + fragment.read_text(encoding="utf-8"), encoding="utf-8")


def test_setup_exits_two_and_installs_nothing_when_a_module_is_missing(
        tmp_path, recording_console, provision_home, monkeypatch):
    """Check that setup exits two and installs nothing when a module is missing."""
    installs = []

    class _Recording(_FakeAptManager):
        """Records every install call."""

        def install(self, pkgs, dry_run):
            """Record the call and report success."""
            installs.append(pkgs)
            return True

    _quiet_setup(monkeypatch, provision_home, managers=[_Recording()])
    _depending_fragment(tmp_path / "dsp", ["sushiruntime"])
    app = _app(tmp_path, recording_console, locate=_sibling_locator(tmp_path))

    result = CliRunner().invoke(app, ["setup"])

    assert result.exit_code == 2
    errors = [args[0] for name, args in recording_console.calls if name == "error"]
    assert any("sushiruntime" in e and "SUSHIRUNTIME_DIR" in e for e in errors)
    assert installs == []
    assert not (provision_home / ".lock").exists()
    assert not (tmp_path / "dsp" / "cli" / "config.local.toml").exists()


def test_setup_reads_the_fragment_of_a_located_dependency(
        tmp_path, recording_console, provision_home, monkeypatch):
    """Check that setup reads the fragment of a located dependency."""
    _quiet_setup(monkeypatch, provision_home, managers=[])
    runtime = tmp_path / "sushiruntime" / "cli" / "sushistack.deps.toml"
    runtime.parent.mkdir(parents=True)
    runtime.write_text('[gadget]\ndescription = "g"\nlinux_apt = ["gadget-dev"]\n',
                       encoding="utf-8")
    _depending_fragment(tmp_path / "dsp", ["sushiruntime"])
    app = _app(tmp_path, recording_console, locate=_sibling_locator(tmp_path))

    result = CliRunner().invoke(app, ["setup", "--dry-run"])

    assert result.exit_code == 0, result.exception
    rows = _table_rows(recording_console.calls, ["Component", "Status", "Owner", "Detail"])
    owners = {row[0]: row[2] for row in rows}
    assert owners["gadget"] == "sushiruntime"
    assert owners["widget"] == "sushidsp"


def test_setup_rejects_an_unknown_toolchain_before_the_lock(
        tmp_path, recording_console, provision_home, monkeypatch):
    """Check that setup rejects an unknown toolchain before the lock."""
    _quiet_setup(monkeypatch, provision_home, managers=[])
    _write_fragment(tmp_path / "dsp")
    result = CliRunner().invoke(_app(tmp_path, recording_console),
                                ["setup", "--dry-run", "--toolchain", "typo"])
    assert result.exit_code == 2
    assert not (provision_home / ".lock").exists()


def test_setup_selects_the_first_declared_toolchain_when_none_is_present(
        tmp_path, recording_console, provision_home, monkeypatch):
    """Check that setup selects the first declared toolchain when none is present."""
    _quiet_setup(monkeypatch, provision_home, managers=[])
    seen = []
    monkeypatch.setattr(commands.InstallPipeline, "run",
                        lambda self, ctx, show_progress=True: seen.append(ctx.selection) or True)
    monkeypatch.setattr(probe, "toolchain_status", lambda cfg, gpu: [
        ("intel-llvm", False, ""), ("adaptivecpp", False, ""), ("oneapi", False, "")])
    fragment = _write_fragment(tmp_path / "dsp")
    fragment.write_text(
        '[intel-llvm]\nprovides = "sycl-toolchain"\n[adaptivecpp]\nprovides = "sycl-toolchain"\n',
        encoding="utf-8")

    CliRunner().invoke(_app(tmp_path, recording_console), ["setup", "--dry-run"])

    assert (seen[0].install_intel_llvm, seen[0].install_acpp, seen[0].gpu) == (
        True, False, False)


def test_setup_selects_nothing_when_a_toolchain_is_present(
        tmp_path, recording_console, provision_home, monkeypatch):
    """Check that setup selects nothing when a toolchain is present."""
    _quiet_setup(monkeypatch, provision_home, managers=[])
    seen = []
    monkeypatch.setattr(commands.InstallPipeline, "run",
                        lambda self, ctx, show_progress=True: seen.append(ctx.selection) or True)
    monkeypatch.setattr(probe, "toolchain_status", lambda cfg, gpu: [
        ("intel-llvm", True, ""), ("adaptivecpp", False, ""), ("oneapi", False, "")])
    fragment = _write_fragment(tmp_path / "dsp")
    fragment.write_text(
        '[intel-llvm]\nprovides = "sycl-toolchain"\n[adaptivecpp]\nprovides = "sycl-toolchain"\n',
        encoding="utf-8")

    CliRunner().invoke(_app(tmp_path, recording_console), ["setup", "--dry-run"])

    assert not (seen[0].install_intel_llvm or seen[0].install_acpp)


def test_uses_base_adds_the_shared_fragment(
        tmp_path, recording_console, provision_home, monkeypatch):
    """Check that uses base adds the shared fragment."""
    _quiet_setup(monkeypatch, provision_home, managers=[])
    _write_fragment(tmp_path / "dsp")
    app = _app(tmp_path, recording_console, uses_base=True)

    CliRunner().invoke(app, ["setup", "--dry-run"])

    rows = _table_rows(recording_console.calls, ["Component", "Status", "Owner", "Detail"])
    assert any(row[0] == "gtest" and row[2] == "shared" for row in rows)


def test_doctor_reports_a_missing_module_and_keeps_running(
        tmp_path, recording_console, provision_home, monkeypatch):
    """Check that doctor reports a missing module and keeps running."""
    monkeypatch.setattr(commands, "standard_checks", lambda cfg, fix: [])
    _depending_fragment(tmp_path / "dsp", ["sushiruntime"])
    app = _app(tmp_path, recording_console, locate=_sibling_locator(tmp_path))

    result = CliRunner().invoke(app, ["doctor"])

    assert result.exit_code == 1
    rows = _table_rows(recording_console.calls, ["Check", "Group", "Result", "Detail", "Fix"])
    by_name = {row[0]: row for row in rows}
    assert "sushiruntime" in by_name["modules"][3]
    assert "dependencies" in by_name


def test_a_binary_install_registers_doctor_alone(tmp_path, recording_console):
    """Check that a binary install registers doctor alone."""
    app = _app(tmp_path, recording_console, is_binary=lambda: True)
    names = {command.callback.__name__ for command in app.registered_commands}
    assert names == {"doctor"}


def test_the_panel_is_set_on_every_command(tmp_path, recording_console):
    """Check that the panel is set on every command."""
    app = _app(tmp_path, recording_console, panel="Environment")
    assert {command.rich_help_panel for command in app.registered_commands} == {"Environment"}


def test_doctor_agrees_with_the_inventory_on_a_package_the_manager_holds(
        tmp_path, recording_console, provision_home, monkeypatch):
    """Check that doctor passes a dependency whose check cmd fails but whose package is held."""
    monkeypatch.setattr(commands, "standard_checks", lambda cfg, fix: [])
    monkeypatch.setattr(commands, "_managers_for", lambda cfg: [_FakeAptManager()])
    fragment = tmp_path / "dsp" / "cli" / "sushistack.deps.toml"
    fragment.parent.mkdir(parents=True)
    fragment.write_text(
        '[widget]\nlinux_apt = ["widget-dev"]\ncheck_cmd = ["sushi-no-such-tool-xyz"]\n',
        encoding="utf-8")

    CliRunner().invoke(_app(tmp_path, recording_console), ["doctor"])

    rows = _table_rows(recording_console.calls, ["Check", "Group", "Result", "Detail", "Fix"])
    by_name = {row[0]: row for row in rows}
    assert "widget" not in by_name["dependencies"][3]


def test_every_command_help_carries_examples(tmp_path, recording_console):
    """Check that each command's help ends with examples naming the module's program."""
    app = _app(tmp_path, recording_console)
    for command in app.registered_commands:
        name = command.callback.__name__
        assert f"sd {name}" in command.epilog


def test_doctor_lists_the_downloads_with_no_pinned_digest(
        tmp_path, recording_console, provision_home, monkeypatch):
    """Check that doctor carries a row naming the downloads a setup would not verify."""
    monkeypatch.setattr(commands, "standard_checks", lambda cfg, fix: [])
    fragment = tmp_path / "dsp" / "cli" / "sushistack.deps.toml"
    fragment.parent.mkdir(parents=True)
    fragment.write_text('[intel-llvm]\ndescription = "SYCL bundle"\nrequired = false\n',
                        encoding="utf-8")

    CliRunner().invoke(_app(tmp_path, recording_console), ["doctor"])

    rows = _table_rows(recording_console.calls, ["Check", "Group", "Result", "Detail", "Fix"])
    by_name = {row[0]: row for row in rows}
    assert "intel-llvm" in by_name["download digests"][3]
    assert "warn" in by_name["download digests"][2]
