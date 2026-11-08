# test_commands.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the setup/doctor/link/unlink commands."""

from __future__ import annotations

import os

import pytest
import typer
import typer.main
from typer.testing import CliRunner

from sushicore.console_memory import RecordingConsole
from sushicore.profile import ModuleProfile
from sushicore.provision.commands import ModuleProvision, register_provision_commands
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.doctor import CheckResult, FunctionCheck, State
from sushicore.provision.git_client_memory import InMemoryGitClient
from sushicore.provision.lock import ProvisionLock
from sushicore.provision.packages.base_memory import InMemoryLinuxPackageManager
from sushicore.provision.steps import MachineActions
from sushicore.workspace import read_link, registered_modules, write_module


#: A commit every fixture fragment pins its Sushi libraries to.
K_COMMIT = "0123456789abcdef0123456789abcdef01234567"

K_CHECK_HEADER = ["Check", "Group", "Result", "Detail", "Fix"]
K_COMPONENT_HEADER = ["Component", "Status", "Owner", "Detail"]


def _offline_git() -> InMemoryGitClient:
    """Return a git that cannot reach the network: every clone fails, every HEAD is the pin."""
    return InMemoryGitClient(clones=False, default_head=K_COMMIT)


def _no_toolchains(cfg, gpu):
    """Report a machine that has no SYCL toolchain row at all."""
    return []


def _machine() -> MachineActions:
    """Return machine calls that touch nothing and probe the single path the tests expect."""
    return MachineActions(
        refresh_path=lambda: None,
        resolve_config=lambda cfg, gpu=False: {"cmake_exe": "/x/cmake"},
        detect_vendor=lambda: "none")


def _write_fragment(root):
    """Write a minimal ``sushistack.deps.toml`` fragment under *root*'s cli/ directory."""
    fragment = root / "cli" / "sushistack.deps.toml"
    fragment.parent.mkdir(parents=True, exist_ok=True)
    fragment.write_text(
        '[widget]\ndescription = "test widget"\nlinux_apt = ["widget-dev"]\n', encoding="utf-8")
    return fragment


def _table_rows(console, header):
    """Return the rows of the first recorded ``console.table`` call with *header*."""
    for name, args in console.calls:
        if name == "table" and args and args[0] == header:
            return args[1]
    raise AssertionError(f"no table call with header {header} in {console.calls}")


def _check_rows(console):
    """Return the doctor table of *console* keyed by check name."""
    return {row[0]: row for row in _table_rows(console, K_CHECK_HEADER)}


def _errors(console):
    """Return the text of every error the recording console took."""
    return [args[0] for name, args in console.calls if name == "error"]


def _results(console):
    """Return the arguments of every ``result`` event the recording console took."""
    return [args for name, args in console.calls if name == "result"]


def _profile(name="sushidsp"):
    """Return the profile of the module under test."""
    return ModuleProfile(name=name, program="sd", env_prefix="SD", root_marker="sushidsp.marker")


def _app(tmp_path, console, *, name="sushidsp", **overrides):
    """Return an app carrying the provision commands, *overrides* passed to ModuleProvision."""
    app = typer.Typer()

    @app.callback()
    def _root():
        """Test app."""

    overrides.setdefault("git", _offline_git)
    overrides.setdefault("managers", lambda cfg: [])
    overrides.setdefault("base_checks", lambda cfg, fix: [])
    overrides.setdefault("toolchains", _no_toolchains)
    overrides.setdefault("actions", _machine())
    register_provision_commands(app, ModuleProvision(
        profile=_profile(name), project_root=lambda: tmp_path / "dsp",
        load_config=lambda: ProvisionSettings(platform="linux"),
        console=lambda: console, **overrides))
    return app


def _workspace(tmp_path):
    """Create a workspace and the module's config folder; return the workspace."""
    ws = tmp_path / "ws"
    (ws / ".sushistack").mkdir(parents=True)
    (tmp_path / "dsp" / "cli").mkdir(parents=True)
    return ws


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
    pins = "".join(f'[sushisystems.{name}]\nversion = "v1.0.0"\ncommit = "{K_COMMIT}"\n'
                   for name in depends_on)
    fragment.write_text(f"[module]\ndepends_on = [{names}]\n{pins}"
                        + fragment.read_text(encoding="utf-8"), encoding="utf-8")


def _unpinned_fragment(root, depends_on):
    """Write a fragment under *root* naming *depends_on* with no pins, and a widget."""
    fragment = _write_fragment(root)
    names = ", ".join(f'"{name}"' for name in depends_on)
    fragment.write_text(f"[module]\ndepends_on = [{names}]\n"
                        + fragment.read_text(encoding="utf-8"), encoding="utf-8")


def _two_toolchain_fragment(root):
    """Write a fragment declaring intel-llvm and adaptivecpp as members of one capability."""
    _write_fragment(root).write_text(
        '[intel-llvm]\nprovides = "sycl-toolchain"\n[adaptivecpp]\nprovides = "sycl-toolchain"\n',
        encoding="utf-8")


def _toolchain_rows(intel_present):
    """Return a toolchain reader whose intel-llvm row is *intel_present*."""
    rows = [("intel-llvm", intel_present, ""), ("adaptivecpp", False, ""), ("oneapi", False, "")]
    return lambda cfg, gpu: rows


def _option(app, command, name):
    """Return the Click option *name* of *command* in the Typer *app*."""
    return next(param for param in typer.main.get_command(app).commands[command].params
                if param.name == name)


@pytest.mark.medium
def test_link_registers_the_module_in_the_workspace(tmp_path, recording_console):
    """Check that link registers the module and links its config folder to the workspace."""
    ws = _workspace(tmp_path)
    result = CliRunner().invoke(_app(tmp_path, recording_console), ["link", "--workspace", str(ws)])
    assert result.exit_code == 0
    assert registered_modules(ws) == {"sushidsp": str(tmp_path / "dsp").replace("\\", "/")}
    assert read_link(tmp_path / "dsp" / "cli") == ws.resolve()


@pytest.mark.medium
def test_unlink_clears_the_workspace_entry_and_the_link(tmp_path, recording_console):
    """Check that unlink removes the registry entry and the link link wrote."""
    ws = _workspace(tmp_path)
    app = _app(tmp_path, recording_console)
    CliRunner().invoke(app, ["link", "--workspace", str(ws)])
    result = CliRunner().invoke(app, ["unlink", "--workspace", str(ws)])
    assert result.exit_code == 0
    assert (registered_modules(ws), read_link(tmp_path / "dsp" / "cli")) == ({}, None)


@pytest.mark.medium
def test_link_outside_a_workspace_exits_two(tmp_path, recording_console, monkeypatch):
    """Check that link outside a workspace exits two and writes no local config."""
    monkeypatch.delenv("SUSHISTACK_HOME", raising=False)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(_app(tmp_path, recording_console), ["link"])
    assert result.exit_code == 2
    assert not (tmp_path / "dsp" / "cli" / "config.local.toml").exists()


@pytest.mark.medium
def test_doctor_filters_by_group(tmp_path, recording_console):
    """Check that doctor --for lists only the checks of that group."""
    extra = [FunctionCheck("kept", "infer", True, lambda: CheckResult(State.OK, "")),
             FunctionCheck("dropped", "eval", True, lambda: CheckResult(State.OK, ""))]
    app = _app(tmp_path, recording_console, extra_checks=lambda: extra)
    result = CliRunner().invoke(app, ["doctor", "--for", "infer"])
    assert result.exit_code == 0
    assert list(_check_rows(recording_console)) == ["kept"]


@pytest.mark.medium
def test_doctor_rejects_an_unknown_group(tmp_path, recording_console):
    """Check that an unknown group exits two and names the groups."""
    result = CliRunner().invoke(_app(tmp_path, recording_console), ["doctor", "--for", "typo"])
    assert result.exit_code == 2
    assert any("build" in e and "eval" in e and "typo" in e for e in _errors(recording_console))


@pytest.mark.medium
def test_doctor_reports_the_module_fragment_and_toolchain_stamps(
        tmp_path, recording_console, provision_home):
    """Check that doctor reports a failing fragment dependency and an unstamped toolchain."""
    fragment = tmp_path / "dsp" / "cli" / "sushistack.deps.toml"
    fragment.parent.mkdir(parents=True)
    fragment.write_text(
        '[widget]\nlinux_apt = ["widget-dev"]\ncheck_cmd = ["sushi-no-such-tool-xyz"]\n',
        encoding="utf-8")
    (provision_home / "toolchains" / "llvm-sycl").mkdir(parents=True)

    result = CliRunner().invoke(_app(tmp_path, recording_console), ["doctor"])

    by_name = _check_rows(recording_console)
    assert result.exit_code == 1
    assert "widget" in by_name["dependencies"][3]
    assert "llvm-sycl" in by_name["toolchain stamps"][3]


@pytest.mark.medium
def test_setup_dry_run_detects_the_module_fragment(tmp_path, recording_console, provision_home):
    """Check that setup --dry-run lists the module's component under the module's name."""
    _write_fragment(tmp_path / "dsp")

    result = CliRunner().invoke(_app(tmp_path, recording_console), ["setup", "--dry-run"])

    rows = _table_rows(recording_console, K_COMPONENT_HEADER)
    assert result.exit_code == 0
    assert next(row for row in rows if row[0] == "widget")[2] == "sushidsp"


@pytest.mark.medium
def test_setup_dry_run_writes_nothing(tmp_path, recording_console, provision_home):
    """Check that setup --dry-run leaves the module's folder as it found it."""
    root = tmp_path / "dsp"
    _write_fragment(root)

    CliRunner().invoke(_app(tmp_path, recording_console), ["setup", "--dry-run"])

    assert {p.name for p in root.iterdir()} == {"cli"}
    assert {p.name for p in (root / "cli").iterdir()} == {"sushistack.deps.toml"}


@pytest.mark.medium
def test_setup_writes_the_module_sink_without_dry_run(tmp_path, recording_console, provision_home):
    """Check that setup writes the probed values to the module's local config."""
    root = tmp_path / "dsp"
    _write_fragment(root)
    app = _app(tmp_path, recording_console,
               managers=lambda cfg: [InMemoryLinuxPackageManager()])

    result = CliRunner().invoke(app, ["setup"])

    written = root / "cli" / "config.local.toml"
    assert result.exit_code == 0
    assert 'cmake_exe = "/x/cmake"' in written.read_text(encoding="utf-8")


@pytest.mark.medium
def test_setup_dry_run_prints_the_probed_config(tmp_path, recording_console, provision_home):
    """Check that setup --dry-run prints the config it would write."""
    _write_fragment(tmp_path / "dsp")

    result = CliRunner().invoke(_app(tmp_path, recording_console), ["setup", "--dry-run"])

    printed = [args[0] for name, args in recording_console.calls if name == "console.print"]
    assert result.exit_code == 0, result.exception
    assert any('cmake_exe = "/x/cmake"' in text for text in printed)


@pytest.mark.medium
def test_setup_creates_a_missing_dependency_root(tmp_path, recording_console, provision_home):
    """Check that setup creates the dependency root, so its lock file can exist."""
    _write_fragment(tmp_path / "dsp")
    assert not provision_home.exists()

    result = CliRunner().invoke(_app(tmp_path, recording_console), ["setup", "--dry-run"])

    assert result.exit_code == 0, result.exception
    assert (provision_home / ".lock").is_file()


@pytest.mark.medium
def test_setup_exits_one_when_the_lock_is_held(tmp_path, recording_console, provision_home):
    """Check that setup exits one and names the pid when another run holds the lock."""
    _write_fragment(tmp_path / "dsp")
    app = _app(tmp_path, recording_console, lock_timeout=0.2)

    with ProvisionLock(provision_home / ".lock"):
        result = CliRunner().invoke(app, ["setup", "--dry-run"])

    assert result.exit_code == 1
    assert any(str(os.getpid()) in message for message in _errors(recording_console))


@pytest.mark.medium
def test_setup_exits_one_when_a_step_fails(tmp_path, recording_console, provision_home):
    """Check that setup exits one when no package manager is available to install."""
    _write_fragment(tmp_path / "dsp")

    result = CliRunner().invoke(_app(tmp_path, recording_console), ["setup"])

    assert result.exit_code == 1


@pytest.mark.medium
def test_setup_builds_the_package_managers_once(tmp_path, recording_console, provision_home):
    """Check that setup builds the package managers once for the run and its doctor."""
    built = []
    _write_fragment(tmp_path / "dsp")
    app = _app(tmp_path, recording_console, managers=lambda cfg: built.append(cfg) or [])

    CliRunner().invoke(app, ["setup", "--dry-run"])

    assert len(built) == 1


@pytest.mark.medium
def test_link_records_the_lower_cased_key(tmp_path, recording_console):
    """Check that link records the module under its lower-cased key, not its display name."""
    ws = _workspace(tmp_path)
    app = _app(tmp_path, recording_console, name="SushiDSP")
    assert CliRunner().invoke(app, ["link", "--workspace", str(ws)]).exit_code == 0
    assert list(registered_modules(ws)) == ["sushidsp"]


@pytest.mark.medium
def test_unlink_removes_an_entry_written_under_the_display_name(tmp_path, recording_console):
    """Check that unlink removes an entry an older link wrote under the display name."""
    ws = _workspace(tmp_path)
    write_module(ws, "SushiDSP", tmp_path / "dsp")
    app = _app(tmp_path, recording_console, name="SushiDSP")
    assert CliRunner().invoke(app, ["unlink", "--workspace", str(ws)]).exit_code == 0
    assert registered_modules(ws) == {}


@pytest.mark.medium
def test_setup_fails_when_a_pinned_module_cannot_be_fetched(
        tmp_path, recording_console, provision_home):
    """Check that setup exits one and names the module when a pinned module cannot be cloned."""
    _depending_fragment(tmp_path / "dsp", ["sushiruntime"])
    app = _app(tmp_path, recording_console, locate=_sibling_locator(tmp_path),
               managers=lambda cfg: [InMemoryLinuxPackageManager()])

    result = CliRunner().invoke(app, ["setup"])

    assert result.exit_code == 1
    assert any("sushiruntime" in e and "failed" in e for e in _errors(recording_console))


@pytest.mark.medium
def test_setup_installs_nothing_when_a_pinned_module_cannot_be_fetched(
        tmp_path, recording_console, provision_home):
    """Check that no package is installed and no config written when a fetch fails."""
    manager = InMemoryLinuxPackageManager()
    _depending_fragment(tmp_path / "dsp", ["sushiruntime"])
    app = _app(tmp_path, recording_console, locate=_sibling_locator(tmp_path),
               managers=lambda cfg: [manager])

    CliRunner().invoke(app, ["setup"])

    assert manager.installs == []
    assert not (provision_home / "sources" / "sushiruntime" / "v1.0.0").exists()
    assert not (tmp_path / "dsp" / "cli" / "config.local.toml").exists()


def _declare_gtest(destination):
    """Write the checkout a clone makes: a fragment that declares gtest."""
    fragment = destination / "cli" / "sushistack.deps.toml"
    fragment.parent.mkdir(parents=True)
    fragment.write_text('[gtest]\nlinux_apt = ["libgtest-dev"]\n', encoding="utf-8")


@pytest.mark.medium
def test_setup_fetches_a_pinned_module_and_reads_its_fragment(
        tmp_path, recording_console, provision_home):
    """Check that setup clones a pinned module with no sibling and reports it fetched."""
    _depending_fragment(tmp_path / "dsp", ["sushiruntime"])
    git = InMemoryGitClient(default_head=K_COMMIT, materialize=_declare_gtest)
    app = _app(tmp_path, recording_console, locate=_sibling_locator(tmp_path),
               git=lambda: git, managers=lambda cfg: [InMemoryLinuxPackageManager()])

    result = CliRunner().invoke(app, ["setup"])

    assert result.exit_code == 0, recording_console.calls
    assert "fetched" in _check_rows(recording_console)["sushi sushiruntime"][3]


@pytest.mark.medium
def test_setup_reads_the_fragment_of_a_fetched_module(tmp_path, recording_console, provision_home):
    """Check that the components of a fetched module's fragment join the setup table."""
    _depending_fragment(tmp_path / "dsp", ["sushiruntime"])
    git = InMemoryGitClient(default_head=K_COMMIT, materialize=_declare_gtest)
    app = _app(tmp_path, recording_console, locate=_sibling_locator(tmp_path), git=lambda: git,
               managers=lambda cfg: [InMemoryLinuxPackageManager()])

    CliRunner().invoke(app, ["setup"])

    owners = {row[0]: row[2] for row in _table_rows(recording_console, K_COMPONENT_HEADER)}
    assert owners["gtest"] == "sushiruntime"


@pytest.mark.medium
def test_setup_reads_the_fragment_of_a_located_dependency(
        tmp_path, recording_console, provision_home):
    """Check that setup reads the fragment of a dependency found beside the module."""
    runtime = tmp_path / "sushiruntime" / "cli" / "sushistack.deps.toml"
    runtime.parent.mkdir(parents=True)
    runtime.write_text('[gadget]\ndescription = "g"\nlinux_apt = ["gadget-dev"]\n',
                       encoding="utf-8")
    _depending_fragment(tmp_path / "dsp", ["sushiruntime"])
    app = _app(tmp_path, recording_console, locate=_sibling_locator(tmp_path))

    result = CliRunner().invoke(app, ["setup", "--dry-run"])

    owners = {row[0]: row[2] for row in _table_rows(recording_console, K_COMPONENT_HEADER)}
    assert result.exit_code == 0, result.exception
    assert (owners["gadget"], owners["widget"]) == ("sushiruntime", "sushidsp")


@pytest.mark.medium
def test_setup_rejects_an_unknown_toolchain_before_the_lock(
        tmp_path, recording_console, provision_home):
    """Check that an unknown toolchain exits two before the lock file is made."""
    _write_fragment(tmp_path / "dsp")
    result = CliRunner().invoke(_app(tmp_path, recording_console),
                                ["setup", "--dry-run", "--toolchain", "typo"])
    assert result.exit_code == 2
    assert not (provision_home / ".lock").exists()


def _dry_run_downloads(console):
    """Return the dry-run lines announcing an intel/llvm download."""
    return [args[0] for name, args in console.calls
            if name == "info" and "would download intel/llvm" in args[0]]


@pytest.mark.medium
def test_setup_selects_the_first_declared_toolchain_when_none_is_present(
        tmp_path, recording_console, provision_home):
    """Check that setup installs the first declared toolchain when none is present."""
    _two_toolchain_fragment(tmp_path / "dsp")
    app = _app(tmp_path, recording_console, toolchains=_toolchain_rows(False),
               managers=lambda cfg: [InMemoryLinuxPackageManager()])

    CliRunner().invoke(app, ["setup", "--dry-run"])

    assert len(_dry_run_downloads(recording_console)) == 1


@pytest.mark.medium
def test_setup_selects_nothing_when_a_toolchain_is_present(
        tmp_path, recording_console, provision_home):
    """Check that setup installs no toolchain when one of the capability is present."""
    _two_toolchain_fragment(tmp_path / "dsp")
    app = _app(tmp_path, recording_console, toolchains=_toolchain_rows(True),
               managers=lambda cfg: [InMemoryLinuxPackageManager()])

    CliRunner().invoke(app, ["setup", "--dry-run"])

    assert _dry_run_downloads(recording_console) == []


@pytest.mark.medium
def test_uses_base_adds_the_shared_fragment(tmp_path, recording_console, provision_home):
    """Check that uses_base adds the shared fragment's components."""
    _write_fragment(tmp_path / "dsp")
    app = _app(tmp_path, recording_console, uses_base=True)

    CliRunner().invoke(app, ["setup", "--dry-run"])

    rows = _table_rows(recording_console, K_COMPONENT_HEADER)
    assert any(row[0] == "gtest" and row[2] == "shared" for row in rows)


@pytest.mark.medium
def test_doctor_reports_a_missing_module_and_keeps_running(
        tmp_path, recording_console, provision_home):
    """Check that doctor names a module with no checkout and still reports the dependencies."""
    _depending_fragment(tmp_path / "dsp", ["sushiruntime"])
    app = _app(tmp_path, recording_console, locate=_sibling_locator(tmp_path))

    result = CliRunner().invoke(app, ["doctor"])

    by_name = _check_rows(recording_console)
    assert result.exit_code == 1
    assert "sushiruntime" in by_name["modules"][3]
    assert "dependencies" in by_name


@pytest.mark.small
def test_a_binary_install_registers_doctor_alone(tmp_path):
    """Check that a binary install registers doctor alone."""
    app = _app(tmp_path, RecordingConsole(), is_binary=lambda: True)
    names = {command.callback.__name__ for command in app.registered_commands}
    assert names == {"doctor"}


@pytest.mark.small
def test_the_panel_is_set_on_every_command(tmp_path):
    """Check that the panel is set on every command."""
    app = _app(tmp_path, RecordingConsole(), panel="Environment")
    assert {command.rich_help_panel for command in app.registered_commands} == {"Environment"}


@pytest.mark.medium
def test_doctor_agrees_with_the_inventory_on_a_package_the_manager_holds(
        tmp_path, recording_console, provision_home):
    """Check that doctor passes a dependency whose check cmd fails but whose package is held."""
    fragment = tmp_path / "dsp" / "cli" / "sushistack.deps.toml"
    fragment.parent.mkdir(parents=True)
    fragment.write_text(
        '[widget]\nlinux_apt = ["widget-dev"]\ncheck_cmd = ["sushi-no-such-tool-xyz"]\n',
        encoding="utf-8")
    app = _app(tmp_path, recording_console,
               managers=lambda cfg: [InMemoryLinuxPackageManager(installed=["widget-dev"])])

    CliRunner().invoke(app, ["doctor"])

    assert "widget" not in _check_rows(recording_console)["dependencies"][3]


@pytest.mark.small
def test_every_command_help_carries_examples(tmp_path):
    """Check that each command's help ends with examples naming the module's program."""
    app = _app(tmp_path, RecordingConsole())
    assert all(f"sd {command.callback.__name__}" in command.epilog
               for command in app.registered_commands)


@pytest.mark.medium
def test_doctor_lists_the_downloads_with_no_pinned_digest(
        tmp_path, recording_console, provision_home):
    """Check that doctor carries a row naming the downloads a setup would not verify."""
    fragment = tmp_path / "dsp" / "cli" / "sushistack.deps.toml"
    fragment.parent.mkdir(parents=True)
    fragment.write_text('[intel-llvm]\ndescription = "SYCL bundle"\nrequired = false\n',
                        encoding="utf-8")

    CliRunner().invoke(_app(tmp_path, recording_console), ["doctor"])

    row = _check_rows(recording_console)["download digests"]
    assert "intel-llvm" in row[3]
    assert "warn" in row[2]


@pytest.mark.medium
def test_setup_stops_before_fetching_when_two_pins_conflict(
        tmp_path, recording_console, provision_home):
    """Check that a chain pinning one library at two versions stops setup before any clone."""
    root = tmp_path / "dsp"
    _depending_fragment(root, ["sushiruntime"])
    fragment = root / "cli" / "sushistack.deps.toml"
    text = fragment.read_text(encoding="utf-8")
    text = text.replace('depends_on = ["sushiruntime"]',
                        'depends_on = ["sushiruntime", "sushilog"]')
    fragment.write_text(
        text + f'[sushisystems.sushilog]\nversion = "v1.0.0"\ncommit = "{K_COMMIT}"\n',
        encoding="utf-8")
    runtime = tmp_path / "sushiruntime" / "cli" / "sushistack.deps.toml"
    runtime.parent.mkdir(parents=True)
    runtime.write_text(f'[module]\ndepends_on = ["sushilog"]\n[sushisystems.sushilog]\n'
                       f'version = "v1.1.0"\ncommit = "{K_COMMIT}"\n', encoding="utf-8")
    git = _offline_git()
    app = _app(tmp_path, recording_console, locate=_sibling_locator(tmp_path), git=lambda: git,
               managers=lambda cfg: [InMemoryLinuxPackageManager()])

    result = CliRunner().invoke(app, ["setup"])

    assert result.exit_code == 1
    assert git.calls == []
    assert any("sushilog" in e and "sushidsp" in e and "sushiruntime" in e
               and "v1.0.0" in e and "v1.1.0" in e for e in _errors(recording_console))


@pytest.mark.medium
def test_setup_exits_two_when_an_unpinned_module_is_missing(
        tmp_path, recording_console, provision_home):
    """Check that an unpinned module with no checkout is never fetched and setup exits two."""
    _unpinned_fragment(tmp_path / "dsp", ["sushiruntime"])
    git = _offline_git()
    app = _app(tmp_path, recording_console, locate=_sibling_locator(tmp_path), git=lambda: git)

    result = CliRunner().invoke(app, ["setup"])

    assert result.exit_code == 2
    assert any("sushiruntime" in e and "SUSHIRUNTIME_DIR" in e for e in _errors(recording_console))
    assert git.calls == []


@pytest.mark.medium
def test_setup_installs_nothing_when_an_unpinned_module_is_missing(
        tmp_path, recording_console, provision_home):
    """Check that no package is installed, no lock made and no config written then."""
    manager = InMemoryLinuxPackageManager()
    _unpinned_fragment(tmp_path / "dsp", ["sushiruntime"])
    app = _app(tmp_path, recording_console, locate=_sibling_locator(tmp_path),
               managers=lambda cfg: [manager])

    CliRunner().invoke(app, ["setup"])

    assert manager.installs == []
    assert not (provision_home / ".lock").exists()
    assert not (tmp_path / "dsp" / "cli" / "config.local.toml").exists()


@pytest.mark.medium
def test_doctor_warns_on_an_unpinned_module(tmp_path, recording_console, provision_home):
    """Check that doctor shows a warning row for a depends_on module with no pin."""
    _unpinned_fragment(tmp_path / "dsp", ["sushiruntime"])
    (tmp_path / "sushiruntime").mkdir()
    app = _app(tmp_path, recording_console, locate=_sibling_locator(tmp_path))

    CliRunner().invoke(app, ["doctor"])

    row = _check_rows(recording_console)["sushi sushiruntime"]
    assert "not pinned; pin it in [sushisystems.sushiruntime]" in row[3]


@pytest.mark.medium
def test_link_ends_with_one_result_event(tmp_path, recording_console):
    """Check that a link ends with one passing result event."""
    ws = _workspace(tmp_path)
    CliRunner().invoke(_app(tmp_path, recording_console), ["link", "--workspace", str(ws)])
    assert _results(recording_console) == [(True, {})]


@pytest.mark.medium
def test_unlink_ends_with_one_result_event(tmp_path, recording_console):
    """Check that an unlink ends with one passing result event."""
    ws = _workspace(tmp_path)
    CliRunner().invoke(_app(tmp_path, recording_console), ["unlink", "--workspace", str(ws)])
    assert _results(recording_console) == [(True, {})]


@pytest.mark.medium
def test_a_failed_link_still_ends_with_a_failing_result_event(
        tmp_path, recording_console, monkeypatch):
    """Check that a link that finds no workspace exits two with one failing result event."""
    monkeypatch.delenv("SUSHISTACK_HOME", raising=False)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(_app(tmp_path, recording_console), ["link"])
    assert result.exit_code == 2
    assert _results(recording_console) == [(False, {})]


@pytest.mark.medium
def test_setup_that_stops_early_ends_with_a_failing_result_event(
        tmp_path, recording_console, provision_home):
    """Check that a setup refused for its toolchain ends with one failing result event."""
    result = CliRunner().invoke(_app(tmp_path, recording_console),
                                ["setup", "--toolchain", "nonesuch"])
    assert result.exit_code == 2
    assert _results(recording_console) == [(False, {})]


@pytest.mark.medium
def test_doctor_ends_with_exactly_one_result_event_carrying_its_checks(
        tmp_path, recording_console, provision_home):
    """Check that doctor ends with one result event that carries the checks."""
    _write_fragment(tmp_path / "dsp")
    CliRunner().invoke(_app(tmp_path, recording_console), ["doctor"])
    results = _results(recording_console)
    assert len(results) == 1
    assert results[0][1]["checks"]


@pytest.mark.small
def test_the_doctor_help_lists_the_check_groups(tmp_path):
    """Check that the doctor option help lists the stock check groups."""
    option = _option(_app(tmp_path, RecordingConsole()), "doctor", "for_group")
    assert "build | test | infer | eval" in option.help


@pytest.mark.small
def test_a_group_a_module_contributes_is_listed(tmp_path):
    """Check that a group the module contributes is listed in the doctor option help."""
    app = _app(tmp_path, RecordingConsole(), groups=("track",))
    assert "infer | eval | track" in _option(app, "doctor", "for_group").help


@pytest.mark.medium
def test_a_group_a_module_contributes_is_accepted(tmp_path, recording_console, provision_home):
    """Check that doctor --for accepts a group the module contributes."""
    _write_fragment(tmp_path / "dsp")
    app = _app(tmp_path, recording_console, groups=("track",))
    assert CliRunner().invoke(app, ["doctor", "--for", "track"]).exit_code != 2


@pytest.mark.medium
def test_a_group_nobody_contributes_is_refused(tmp_path, recording_console, provision_home):
    """Check that doctor --for refuses a group no module contributes."""
    _write_fragment(tmp_path / "dsp")
    app = _app(tmp_path, recording_console, groups=("track",))
    assert CliRunner().invoke(app, ["doctor", "--for", "nonesuch"]).exit_code == 2


@pytest.mark.small
def test_setup_accepts_the_short_form_of_yes(tmp_path):
    """Check that setup accepts -y for --yes."""
    assert "-y" in _option(_app(tmp_path, RecordingConsole()), "setup", "yes").opts
