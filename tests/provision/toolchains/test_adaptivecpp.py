# test_adaptivecpp.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Fake-backed tests for the AdaptiveCpp installer and its dependencies."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore import provision

from sushicore.provision.config import ProvisionSettings

from sushicore.provision.toolchains import adaptivecpp

from sushicore.provision.toolchains.stamp import toolchains_dir



pytestmark = pytest.mark.medium



class _StatusContext:
    """A no-op stand-in for the Rich ``console.status`` context manager."""

    def __enter__(self):
        """Return this context unchanged."""
        return self

    def __exit__(self, *exc_info):
        """Swallow nothing; let any exception propagate."""
        return False



class _InnerConsole:
    """Stands in for ``Console.console``, the raw Rich console."""

    def print(self, *args, **kwargs):
        """Discard the call."""

    def status(self, *args, **kwargs):
        """Return a no-op status context."""
        return _StatusContext()



class FakeConsole:
    """Records every semantic call; answers ``is_machine``/``prompt`` on demand."""

    def __init__(self, machine: bool = False, answer: str = "n") -> None:
        """Start with no recorded calls, in interactive mode by default."""
        self.calls: list[tuple[str, tuple]] = []
        self.console = _InnerConsole()
        self._machine = machine
        self._answer = answer

    def __getattr__(self, name: str):
        """Return a recorder for any semantic console method name."""
        def record(*args, **_kwargs):
            """Check that record."""
            self.calls.append((name, args))
        return record

    def is_machine(self) -> bool:
        """Report the fixed machine-mode flag this fake was built with."""
        return self._machine

    def prompt(self, _message: str, _default: str) -> str:
        """Return the fixed answer this fake was built with."""
        return self._answer

    def has_call(self, name: str) -> bool:
        """Report whether *name* was recorded at least once."""
        return any(call[0] == name for call in self.calls)



@pytest.fixture
def fake_console():
    """Bind a :class:`FakeConsole` for the test, then unbind it."""
    fake = FakeConsole()
    provision.bind_console(lambda: fake)
    yield fake
    provision.bind_console(None)



def _linux_cfg() -> ProvisionSettings:
    """Check that linux cfg."""
    return ProvisionSettings(platform="linux")



def _windows_cfg() -> ProvisionSettings:
    """Check that windows cfg."""
    return ProvisionSettings(platform="windows")



def test_install_adaptivecpp_reuses_an_existing_binary(provision_home, fake_console):
    """Check that install adaptivecpp reuses an existing binary."""
    prefix = toolchains_dir() / "adaptivecpp"
    acpp = prefix / "bin" / "acpp"
    acpp.parent.mkdir(parents=True)
    acpp.touch()

    result = adaptivecpp.install_adaptivecpp(_linux_cfg(), None, None, dry_run=False)

    assert result == str(acpp)



def test_install_adaptivecpp_skips_without_git_or_cmake(provision_home, fake_console, monkeypatch):
    """Check that install adaptivecpp skips without git or cmake."""
    monkeypatch.setattr(adaptivecpp.shutil, "which", lambda _name: None)

    result = adaptivecpp.install_adaptivecpp(_linux_cfg(), None, None, dry_run=False)

    assert result is None
    assert fake_console.has_call("warn")



def test_install_adaptivecpp_dry_run_reports_without_building(provision_home, fake_console,
                                                               monkeypatch):
    """Check that install adaptivecpp dry run reports without building."""
    monkeypatch.setattr(adaptivecpp.shutil, "which", lambda name: f"/usr/bin/{name}")

    result = adaptivecpp.install_adaptivecpp(_linux_cfg(), None, None, dry_run=True)

    prefix = toolchains_dir() / "adaptivecpp"
    assert result == str(prefix / "bin" / "acpp")
    assert fake_console.has_call("info")



def test_find_windows_sdk_rc_dir_returns_empty_without_a_match(monkeypatch):
    """Check that find windows sdk rc dir returns empty without a match."""
    monkeypatch.setattr(adaptivecpp._glob, "glob", lambda _pat: [])

    assert adaptivecpp._find_windows_sdk_rc_dir() == ""



def test_find_windows_sdk_rc_dir_returns_the_highest_sorting_match(monkeypatch):
    """Check that find windows sdk rc dir returns the highest sorting match."""
    monkeypatch.setattr(
        adaptivecpp._glob, "glob",
        lambda pat: ([r"C:/Program Files/Windows Kits/10/bin/10.0.19041.0/x64/rc.exe",
                      r"C:/Program Files/Windows Kits/10/bin/10.0.22000.0/x64/rc.exe"]
                     if "Program Files/Windows" in pat else []))

    result = adaptivecpp._find_windows_sdk_rc_dir()

    assert Path(result) == Path(r"C:/Program Files/Windows Kits/10/bin/10.0.22000.0/x64")



def test_find_windows_llvm_finds_a_vendored_tree(provision_home):
    """Check that find windows llvm finds a vendored tree."""
    cmake_dir = provision_home / "tools" / "llvm" / "lib" / "cmake" / "llvm"
    cmake_dir.mkdir(parents=True)

    result = adaptivecpp._find_windows_llvm()

    assert result == (str(cmake_dir), str(provision_home / "tools" / "llvm"))



def test_find_windows_llvm_returns_none_when_nothing_is_installed(provision_home, monkeypatch):
    """Check that find windows llvm returns none when nothing is installed."""
    # Hermetic regardless of whether this host has its own LLVM install.
    monkeypatch.setattr(adaptivecpp.Path, "is_dir", lambda _self: False)

    assert adaptivecpp._find_windows_llvm() is None



def test_confirm_timeout_returns_the_default_when_unanswered(fake_console, monkeypatch):
    """Check that confirm timeout returns the default when unanswered."""
    # A real input() would block under -s; make it fail at once like a closed stdin.
    monkeypatch.setattr("builtins.input", lambda: (_ for _ in ()).throw(EOFError()))

    result = adaptivecpp._confirm_timeout("Proceed?", timeout=1, default=False)

    assert result is False



def test_confirm_timeout_machine_mode_uses_the_prompted_answer():
    """Check that confirm timeout machine mode uses the prompted answer."""
    fake = FakeConsole(machine=True, answer="y")
    provision.bind_console(lambda: fake)
    try:
        result = adaptivecpp._confirm_timeout("Proceed?", timeout=1, default=False)
    finally:
        provision.bind_console(None)

    assert result is True



def test_acpp_deps_linux_without_a_manager_returns_no_llvm_dir():
    """Check that acpp deps linux without a manager returns no llvm dir."""
    assert adaptivecpp._acpp_deps_linux(None) == (None, None)



class _FakeAptManager:
    """Fake FakeAptManager for testing."""
    name = "apt"

    def __init__(self) -> None:
        """Perform  init  ."""
        self.installed: list[str] = []

    def install(self, pkgs, dry_run):
        """Check that install."""
        self.installed.extend(pkgs)
        return True



def test_acpp_deps_linux_apt_installs_the_pinned_llvm_packages(fake_console, monkeypatch):
    """Check that acpp deps linux apt installs the pinned llvm packages."""
    # Hermetic regardless of whether this host has its own llvm-17 dev tree.
    monkeypatch.setattr(adaptivecpp.Path, "is_dir", lambda _self: False)
    mgr = _FakeAptManager()

    llvm_dir, clang_prefix = adaptivecpp._acpp_deps_linux(mgr)

    assert mgr.installed == [
        f"clang-{adaptivecpp.ACPP_LLVM}", f"llvm-{adaptivecpp.ACPP_LLVM}-dev",
        f"libclang-{adaptivecpp.ACPP_LLVM}-dev", f"lld-{adaptivecpp.ACPP_LLVM}",
        "libboost-context-dev", "libboost-fiber-dev",
    ]
    assert clang_prefix == f"/usr/lib/llvm-{adaptivecpp.ACPP_LLVM}"
    assert llvm_dir is None



class _FakeGenericManager:
    """Fake FakeGenericManager for testing."""
    name = "pacman"

    def __init__(self) -> None:
        """Perform  init  ."""
        self.installed: list[str] = []

    def translate_apt(self, pkgs):
        """Check that translate apt."""
        return [f"generic-{p}" for p in pkgs]

    def install(self, pkgs, dry_run):
        """Check that install."""
        self.installed.extend(pkgs)
        return True



def test_acpp_deps_linux_other_manager_translates_generic_packages(fake_console):
    """Check that acpp deps linux other manager translates generic packages."""
    mgr = _FakeGenericManager()

    result = adaptivecpp._acpp_deps_linux(mgr)

    assert result == ("", None)
    assert mgr.installed == [
        "generic-clang", "generic-llvm",
        "generic-libboost-context-dev", "generic-libboost-fiber-dev",
    ]



class _FakeVcpkgManager:
    """Fake FakeVcpkgManager for testing."""
    def __init__(self) -> None:
        """Perform  init  ."""
        self.installed: list[str] = []

    def install(self, pkgs, dry_run):
        """Check that install."""
        self.installed.extend(pkgs)
        return True



def test_acpp_deps_windows_reuses_an_existing_llvm(monkeypatch, fake_console):
    """Check that acpp deps windows reuses an existing llvm."""
    monkeypatch.setattr(adaptivecpp, "_find_windows_llvm", lambda: ("dir", "prefix"))
    vcpkg = _FakeVcpkgManager()

    result = adaptivecpp._acpp_deps_windows(vcpkg)

    assert result == ("dir", "prefix")
    assert vcpkg.installed == ["boost-context", "boost-fiber"]



def test_acpp_deps_windows_without_consent_skips_the_download(monkeypatch, fake_console):
    """Check that acpp deps windows without consent skips the download."""
    monkeypatch.setattr(adaptivecpp, "_find_windows_llvm", lambda: None)

    result = adaptivecpp._acpp_deps_windows(None, assume_yes=False)

    assert result == (None, None)



def test_explain_acpp_skip_windows_names_the_setup_command(fake_console):
    """Check that explain acpp skip windows names the setup command."""
    adaptivecpp._explain_acpp_skip(_windows_cfg())

    infos = " ".join(str(args) for name, args in fake_console.calls if name == "info")
    assert "sr setup acpp" in infos



def test_explain_acpp_skip_linux_names_the_dev_packages(fake_console):
    """Check that explain acpp skip linux names the dev packages."""
    adaptivecpp._explain_acpp_skip(_linux_cfg())

    infos = " ".join(str(args) for name, args in fake_console.calls if name == "info")
    assert "llvm-17-dev" in infos
