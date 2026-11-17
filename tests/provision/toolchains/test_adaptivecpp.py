# test_adaptivecpp.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The AdaptiveCpp installer reuses a build, finds its dependencies and explains why it skips."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.proc_memory import RecordingRunner
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.llvm_plans import windows as llvm_windows
from sushicore.provision.packages import winget as winget_module
from sushicore.provision.packages.linux import AptManager
from sushicore.provision.packages.winget import WingetManager
from sushicore.provision.packages.base_memory import (
    InMemoryLinuxPackageManager,
    InMemoryPackageManager,
)
from sushicore.provision.toolchains import adaptivecpp
from sushicore.provision.toolchains.stamp import toolchains_dir

_SDK_NEWEST = "C:/Program Files/Windows Kits/10/bin/10.0.22000.0/x64"
_SDK_OLDER = "C:/Program Files/Windows Kits/10/bin/10.0.19041.0/x64"


class _Commands:
    """Records each command the installer runs and answers the scripted exit codes, then 0."""

    def __init__(self, *exit_codes: int) -> None:
        """Script the exit codes, in call order."""
        self._exit_codes = list(exit_codes)
        self.commands: list[list[str]] = []

    def __call__(self, cmd: list[str], dry_run: bool, *, check: bool = False) -> int:
        """Record *cmd* and answer the next scripted exit code."""
        self.commands.append(cmd)
        return self._exit_codes.pop(0) if self._exit_codes else 0


class _Configure:
    """Records the configure command and answers a fixed success flag."""

    def __init__(self, ok: bool = False) -> None:
        """Answer *ok* to every configure."""
        self._ok = ok
        self.commands: list[list[str]] = []

    def __call__(self, cmd: list[str], dry_run: bool) -> bool:
        """Record *cmd* and answer the flag."""
        self.commands.append(cmd)
        return self._ok


def _on_path(name: str) -> str:
    """Answer a search-path lookup as if every tool sat in ``/usr/bin``."""
    return f"/usr/bin/{name}"


def _not_on_path(_name: str) -> None:
    """Answer a search-path lookup as if no tool were installed."""
    return None


def _no_sdk(_pattern: str) -> list[str]:
    """Answer a glob as if no Windows SDK were installed."""
    return []


def _two_sdks(pattern: str) -> list[str]:
    """Answer the 64-bit Program Files glob with two SDK versions, the others with none."""
    if "Program Files/Windows" not in pattern:
        return []
    return [f"{_SDK_OLDER}/rc.exe", f"{_SDK_NEWEST}/rc.exe"]


def _linux_cfg() -> ProvisionSettings:
    """Build the configuration of a Linux host."""
    return ProvisionSettings(platform="linux")


def _windows_cfg() -> ProvisionSettings:
    """Build the configuration of a Windows host."""
    return ProvisionSettings(platform="windows")


def _make_llvm_tree(base: Path) -> Path:
    """Create the LLVM cmake folder under *base* and return it."""
    cmake_dir = base / "lib" / "cmake" / "llvm"
    cmake_dir.mkdir(parents=True)
    return cmake_dir


def _infos(console: RecordingConsole) -> str:
    """Join every information line the console recorded."""
    return " ".join(console.texts("info"))


@pytest.mark.medium
def test_install_adaptivecpp_reuses_an_existing_binary(provision_home, recording_console):
    """Check that an installed acpp is returned without a build."""
    acpp = toolchains_dir() / "adaptivecpp" / "bin" / "acpp"
    acpp.parent.mkdir(parents=True)
    acpp.touch()
    commands = _Commands()

    result = adaptivecpp.install_adaptivecpp(
        _linux_cfg(), None, None, dry_run=False, which=_on_path, run_command=commands)

    assert result == str(acpp)
    assert commands.commands == []


@pytest.mark.medium
def test_install_adaptivecpp_skips_without_git_or_cmake(provision_home, recording_console):
    """Check that a missing git or cmake skips the build with a warning."""
    commands = _Commands()

    result = adaptivecpp.install_adaptivecpp(
        _linux_cfg(), None, None, dry_run=False, which=_not_on_path, run_command=commands)

    assert result is None
    assert recording_console.texts("warn") == ["AdaptiveCpp build needs git and cmake; skipping."]
    assert commands.commands == []


@pytest.mark.medium
def test_install_adaptivecpp_dry_run_reports_without_building(provision_home, recording_console):
    """Check that a dry run names the executable it would build and runs nothing."""
    commands = _Commands()

    result = adaptivecpp.install_adaptivecpp(
        _linux_cfg(), None, None, dry_run=True, which=_on_path, run_command=commands)

    assert result == str(toolchains_dir() / "adaptivecpp" / "bin" / "acpp")
    assert commands.commands == []
    assert recording_console.has_call("info")


@pytest.mark.medium
def test_install_adaptivecpp_adds_no_resource_compiler_folder_without_a_windows_sdk(
        provision_home, recording_console, tmp_path):
    """Check that a Windows build with no SDK leaves the search path as it was."""
    llvm = tmp_path / "llvm"
    _make_llvm_tree(llvm)
    environ = {"PATH": "base"}

    adaptivecpp.install_adaptivecpp(
        _windows_cfg(), None, None, dry_run=False, which=_on_path, glob=_no_sdk,
        llvm_bases=[llvm], environ=environ, run_command=_Commands(), configure=_Configure())

    assert environ["PATH"] == "base"


@pytest.mark.medium
def test_install_adaptivecpp_puts_the_newest_sdk_resource_compiler_on_the_path(
        provision_home, recording_console, tmp_path):
    """Check that a Windows build puts the highest-sorting SDK's folder first on the path."""
    llvm = tmp_path / "llvm"
    _make_llvm_tree(llvm)
    environ = {"PATH": "base"}

    adaptivecpp.install_adaptivecpp(
        _windows_cfg(), None, None, dry_run=False, which=_on_path, glob=_two_sdks,
        llvm_bases=[llvm], environ=environ, run_command=_Commands(), configure=_Configure())

    assert environ["PATH"].startswith(str(Path(_SDK_NEWEST)))


@pytest.mark.medium
def test_install_adaptivecpp_configures_against_a_vendored_llvm_tree(
        provision_home, recording_console):
    """Check that the LLVM tree vendored under the tools folder is the one cmake is pointed at."""
    llvm = provision_home / "tools" / "llvm"
    cmake_dir = _make_llvm_tree(llvm)
    configure = _Configure()

    adaptivecpp.install_adaptivecpp(
        _windows_cfg(), None, None, dry_run=False, which=_on_path, glob=_no_sdk,
        environ={}, run_command=_Commands(), configure=configure)

    assert f"-DLLVM_DIR={cmake_dir}" in configure.commands[0]
    assert f"-DCLANG_INSTALL_PREFIX={llvm}" in configure.commands[0]


@pytest.mark.medium
def test_install_adaptivecpp_skips_on_windows_when_no_llvm_is_installed(
        provision_home, recording_console):
    """Check that without an LLVM and without consent a Windows build skips and says how to enable it."""
    commands = _Commands()

    result = adaptivecpp.install_adaptivecpp(
        _windows_cfg(), None, None, dry_run=False, which=_on_path, llvm_bases=[],
        run_command=commands)

    assert result is None
    assert commands.commands == []
    assert "sr setup acpp" in _infos(recording_console)


@pytest.mark.medium
def test_adaptivecpp_installs_no_llvm_through_winget_without_consent(
        provision_home, recording_console, monkeypatch):
    """Check that a run whose user accepted no winget agreements installs no LLVM through winget."""
    runner = RecordingRunner(recording_console)
    winget = WingetManager(show=lambda command: "", runner=runner)
    monkeypatch.setattr(llvm_windows, "vendor_llvm_windows", lambda: None)
    monkeypatch.setattr(winget_module.shutil, "which", lambda name: "C:/winget.exe")

    result = adaptivecpp.install_adaptivecpp(
        _windows_cfg(), None, None, dry_run=False, assume_yes=True, winget=winget,
        which=_on_path, llvm_bases=[], run_command=_Commands())

    assert (result, runner.commands) == (None, [])


@pytest.mark.medium
def test_install_adaptivecpp_on_windows_installs_boost_and_reuses_an_existing_llvm(
        provision_home, recording_console, tmp_path):
    """Check that a Windows build asks vcpkg for boost and builds against the LLVM it found."""
    llvm = tmp_path / "llvm"
    cmake_dir = _make_llvm_tree(llvm)
    vcpkg = InMemoryPackageManager("vcpkg")
    configure = _Configure()

    adaptivecpp.install_adaptivecpp(
        _windows_cfg(), None, vcpkg, dry_run=False, which=_on_path, glob=_no_sdk,
        llvm_bases=[llvm], environ={}, run_command=_Commands(), configure=configure)

    assert vcpkg.installs == [["boost-context", "boost-fiber"]]
    assert f"-DLLVM_DIR={cmake_dir}" in configure.commands[0]


@pytest.mark.medium
def test_install_adaptivecpp_on_linux_without_a_manager_skips_the_build(
        provision_home, recording_console):
    """Check that a Linux build with no package manager skips before any command runs."""
    commands = _Commands()

    result = adaptivecpp.install_adaptivecpp(
        _linux_cfg(), None, None, dry_run=False, which=_on_path, run_command=commands)

    assert result is None
    assert commands.commands == []


@pytest.mark.medium
def test_install_adaptivecpp_on_linux_names_the_dev_packages_when_it_skips(
        provision_home, recording_console):
    """Check that the Linux skip note names the LLVM dev packages to install."""
    adaptivecpp.install_adaptivecpp(
        _linux_cfg(), None, None, dry_run=False, which=_on_path, run_command=_Commands())

    assert "llvm-17-dev" in _infos(recording_console)


@pytest.mark.medium
def test_install_adaptivecpp_on_apt_installs_the_pinned_llvm_packages(
        provision_home, recording_console):
    """Check that an apt host is asked for the pinned LLVM, clang, lld and boost packages."""
    runner = RecordingRunner(recording_console)
    manager = AptManager(runner)
    llvm = adaptivecpp.ACPP_LLVM

    adaptivecpp.install_adaptivecpp(
        _linux_cfg(), manager, None, dry_run=False, which=_on_path,
        run_command=_Commands(1), configure=_Configure())

    installs = [list(c.argv) for c in runner.commands if "install" in c.argv]
    assert [argv[-6:] for argv in installs] == [[
        f"clang-{llvm}", f"llvm-{llvm}-dev", f"libclang-{llvm}-dev", f"lld-{llvm}",
        "libboost-context-dev", "libboost-fiber-dev",
    ]]


@pytest.mark.medium
def test_install_adaptivecpp_on_another_manager_translates_the_generic_packages(
        provision_home, recording_console):
    """Check that a non-apt host is asked for the generic packages and a default LLVM."""
    manager = InMemoryLinuxPackageManager("pacman")
    configure = _Configure()

    adaptivecpp.install_adaptivecpp(
        _linux_cfg(), manager, None, dry_run=False, which=_on_path,
        run_command=_Commands(), configure=configure)

    assert manager.installs == [[
        "clang", "llvm", "libboost-context-dev", "libboost-fiber-dev",
    ]]
    assert "-DLLVM_DIR=" in configure.commands[0]
    assert not any(arg.startswith("-DCLANG_INSTALL_PREFIX") for arg in configure.commands[0])
