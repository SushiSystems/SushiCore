# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Fake-backed tests for the intel/llvm, AdaptiveCpp and oneAPI installers."""

from __future__ import annotations

import ast
import io
import re
import tarfile
from pathlib import Path

import pytest

from sushicore import provision
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.pipeline import InstallContext, ToolchainSelection
from sushicore.provision.toolchains import adaptivecpp, intel_llvm, oneapi
from sushicore.provision.toolchains.stamp import read_toolchain_stamp, toolchains_dir


# --------------------------------------------------------------------------- #
# Shared fakes
# --------------------------------------------------------------------------- #

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


# --------------------------------------------------------------------------- #
# intel_llvm
# --------------------------------------------------------------------------- #

def test_install_intel_llvm_reuses_an_existing_bundle(provision_home, fake_console, monkeypatch):
    """Check that install intel llvm reuses an existing bundle."""
    root = toolchains_dir() / "llvm-sycl"
    (root / "bin").mkdir(parents=True)
    (root / "bin" / "clang++").touch()
    monkeypatch.setattr(intel_llvm, "gh_latest_release_asset",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no network")))

    result = intel_llvm.install_intel_llvm(_linux_cfg(), dry_run=False)

    assert result == str(root)
    assert fake_console.has_call("warn")  # no sanitizer runtime in the fake tree


def test_install_intel_llvm_dry_run_reports_without_downloading(provision_home, fake_console):
    """Check that install intel llvm dry run reports without downloading."""
    root = toolchains_dir() / "llvm-sycl"

    result = intel_llvm.install_intel_llvm(_linux_cfg(), dry_run=True)

    assert result == str(root)
    assert not root.exists()
    assert fake_console.has_call("info")


def test_install_intel_llvm_refresh_skips_when_tag_unchanged(provision_home, fake_console,
                                                              monkeypatch):
    """Check that install intel llvm refresh skips when tag unchanged."""
    root = toolchains_dir() / "llvm-sycl"
    (root / "bin").mkdir(parents=True)
    (root / "bin" / "clang++").touch()
    from sushicore.provision.toolchains.stamp import write_toolchain_stamp
    write_toolchain_stamp(root, "intel/llvm", "nightly-1")
    monkeypatch.setattr(intel_llvm, "gh_latest_release_asset",
                        lambda *a, **k: ("nightly-1", "http://example.invalid/a"))
    monkeypatch.setattr(intel_llvm, "download",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no download")))

    result = intel_llvm.install_intel_llvm(_linux_cfg(), dry_run=False, refresh=True)

    assert result == str(root)


def test_install_intel_llvm_downloads_and_extracts_on_first_install(provision_home, fake_console,
                                                                     monkeypatch):
    """Check that install intel llvm downloads and extracts on first install."""
    root = toolchains_dir() / "llvm-sycl"
    clang = root / "bin" / "clang++"
    monkeypatch.setattr(intel_llvm, "gh_latest_release_asset",
                        lambda *a, **k: ("nightly-2", "http://example.invalid/a"))
    monkeypatch.setattr(intel_llvm, "download", lambda *a, **k: None)

    def fake_extract(archive, dest):
        """Check that fake extract."""
        (dest / "bin").mkdir(parents=True, exist_ok=True)
        (dest / "bin" / "clang++").touch()

    monkeypatch.setattr(intel_llvm, "_extract_tar_gz", fake_extract)

    result = intel_llvm.install_intel_llvm(_linux_cfg(), dry_run=False)

    assert result == str(root)
    assert clang.is_file()
    assert read_toolchain_stamp(root)["tag"] == "nightly-2"


def test_install_intel_llvm_returns_none_when_asset_resolution_fails(provision_home, fake_console,
                                                                      monkeypatch):
    """Check that install intel llvm returns none when asset resolution fails."""
    monkeypatch.setattr(intel_llvm, "gh_latest_release_asset",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no asset")))

    result = intel_llvm.install_intel_llvm(_linux_cfg(), dry_run=False)

    assert result is None
    assert fake_console.has_call("error")


def test_install_intel_llvm_cleans_up_on_download_failure_without_refresh(
        provision_home, fake_console, monkeypatch):
    """Check that install intel llvm cleans up on download failure without refresh."""
    root = toolchains_dir() / "llvm-sycl"
    monkeypatch.setattr(intel_llvm, "gh_latest_release_asset",
                        lambda *a, **k: ("nightly-2", "http://example.invalid/a"))
    monkeypatch.setattr(intel_llvm, "download",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("network down")))
    root.mkdir(parents=True)
    (root / "stray-file").touch()

    result = intel_llvm.install_intel_llvm(_linux_cfg(), dry_run=False)

    assert result is None
    assert not root.exists()


def _make_tar_gz(tmp_path: Path, wrapped: bool) -> Path:
    """Check that make tar gz."""
    archive = tmp_path / "bundle.tar.gz"
    names = (["wrap/bin/clang++"] if wrapped
             else ["bin/clang++", "lib/libsomething.so"])
    with tarfile.open(archive, "w:gz") as tf:
        data = b"binary"
        for name in names:
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return archive


def test_extract_tar_gz_collapses_a_single_top_level_wrapper_dir(tmp_path):
    """Check that extract tar gz collapses a single top level wrapper dir."""
    archive = _make_tar_gz(tmp_path, wrapped=True)
    dest = tmp_path / "dest"

    intel_llvm._extract_tar_gz(archive, dest)

    assert (dest / "bin" / "clang++").is_file()


def test_extract_tar_gz_leaves_an_unwrapped_layout_alone(tmp_path):
    """Check that extract tar gz leaves an unwrapped layout alone."""
    archive = _make_tar_gz(tmp_path, wrapped=False)
    dest = tmp_path / "dest"

    intel_llvm._extract_tar_gz(archive, dest)

    assert (dest / "bin" / "clang++").is_file()


# --------------------------------------------------------------------------- #
# adaptivecpp
# --------------------------------------------------------------------------- #

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


# --------------------------------------------------------------------------- #
# oneapi
# --------------------------------------------------------------------------- #

def _ctx(oneapi_selected: bool, dry_run: bool = False, detected: dict | None = None
         ) -> InstallContext:
    """Check that ctx."""
    return InstallContext(
        cfg=ProvisionSettings(),
        selection=ToolchainSelection(oneapi=oneapi_selected),
        dry_run=dry_run,
        detected=detected or {},
    )


def test_install_oneapi_noop_when_not_selected(fake_console):
    """Check that install oneapi noop when not selected."""
    assert oneapi.install_oneapi(_ctx(oneapi_selected=False)) is True
    assert fake_console.calls == []


def test_install_oneapi_noop_when_a_sycl_compiler_is_already_detected(fake_console):
    """Check that install oneapi noop when a sycl compiler is already detected."""
    ctx = _ctx(oneapi_selected=True, detected={"sycl_compiler": True})

    assert oneapi.install_oneapi(ctx) is True
    assert fake_console.calls == []


def test_install_oneapi_dry_run_skips_the_download(fake_console):
    """Check that install oneapi dry run skips the download."""
    ctx = _ctx(oneapi_selected=True, dry_run=True)

    assert oneapi.install_oneapi(ctx) is True
    assert fake_console.has_call("info")


def test_install_oneapi_fails_when_the_download_fails(monkeypatch, fake_console):
    """Check that install oneapi fails when the download fails."""
    monkeypatch.setattr(oneapi, "download_oneapi_installer", lambda: None)

    assert oneapi.install_oneapi(_ctx(oneapi_selected=True)) is False


def test_install_oneapi_runs_the_installer_after_a_successful_download(monkeypatch, fake_console):
    """Check that install oneapi runs the installer after a successful download."""
    seen = {}
    monkeypatch.setattr(oneapi, "download_oneapi_installer", lambda: Path("fake.exe"))

    def fake_run(installer):
        """Check that fake run."""
        seen["installer"] = installer
        return True

    monkeypatch.setattr(oneapi, "run_oneapi_installer", fake_run)

    assert oneapi.install_oneapi(_ctx(oneapi_selected=True)) is True
    assert seen["installer"] == Path("fake.exe")


def test_download_oneapi_installer_reuses_an_existing_file(tmp_path, monkeypatch, fake_console):
    """Check that download oneapi installer reuses an existing file."""
    monkeypatch.setattr(oneapi.Path, "home", classmethod(lambda cls: tmp_path))
    existing = tmp_path / "intel-oneapi-toolkit-offline.exe"
    existing.touch()
    monkeypatch.setattr(oneapi.subprocess, "run",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no curl")))

    assert oneapi.download_oneapi_installer() == existing


class _FakeCompletedProcess:
    """Fake FakeCompletedProcess for testing."""
    def __init__(self, returncode: int) -> None:
        """Perform  init  ."""
        self.returncode = returncode


def test_download_oneapi_installer_downloads_with_curl(tmp_path, monkeypatch, fake_console):
    """Check that download oneapi installer downloads with curl."""
    monkeypatch.setattr(oneapi.Path, "home", classmethod(lambda cls: tmp_path))
    calls = []

    def fake_run(cmd):
        """Check that fake run."""
        calls.append(cmd)
        return _FakeCompletedProcess(0)

    monkeypatch.setattr(oneapi.subprocess, "run", fake_run)

    result = oneapi.download_oneapi_installer()

    assert result == tmp_path / "intel-oneapi-toolkit-offline.exe"
    assert calls[0][0] == "curl"


def test_download_oneapi_installer_returns_none_on_curl_failure(tmp_path, monkeypatch,
                                                                 fake_console):
    """Check that download oneapi installer returns none on curl failure."""
    monkeypatch.setattr(oneapi.Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.setattr(oneapi.subprocess, "run", lambda cmd: _FakeCompletedProcess(1))

    result = oneapi.download_oneapi_installer()

    assert result is None
    assert fake_console.has_call("error")


def test_run_oneapi_installer_reports_success(monkeypatch, fake_console):
    """Check that run oneapi installer reports success."""
    monkeypatch.setattr(oneapi.subprocess, "run", lambda cmd: _FakeCompletedProcess(0))

    assert oneapi.run_oneapi_installer(Path("installer.exe")) is True
    assert fake_console.has_call("success")


def test_run_oneapi_installer_reports_failure(monkeypatch, fake_console):
    """Check that run oneapi installer reports failure."""
    monkeypatch.setattr(oneapi.subprocess, "run", lambda cmd: _FakeCompletedProcess(1))

    assert oneapi.run_oneapi_installer(Path("installer.exe")) is False
    assert fake_console.has_call("warn")


def test_run_oneapi_installer_elevates_on_uac_required(monkeypatch, fake_console):
    """Check that run oneapi installer elevates on uac required."""
    calls = []

    def fake_run(cmd, **kwargs):
        """Check that fake run."""
        calls.append(cmd)
        if len(calls) == 1:
            err = OSError("needs elevation")
            err.winerror = oneapi._ELEVATION_REQUIRED
            raise err
        return _FakeCompletedProcess(0)

    monkeypatch.setattr(oneapi.subprocess, "run", fake_run)

    result = oneapi.run_oneapi_installer(Path("installer.exe"))

    assert result is True
    assert len(calls) == 2
    assert calls[1][0] == "powershell"


def test_run_oneapi_installer_reports_a_non_elevation_launch_failure(monkeypatch, fake_console):
    """Check that run oneapi installer reports a non elevation launch failure."""
    def fake_run(cmd, **kwargs):
        """Check that fake run."""
        raise OSError("no such file")

    monkeypatch.setattr(oneapi.subprocess, "run", fake_run)

    result = oneapi.run_oneapi_installer(Path("installer.exe"))

    assert result is False
    assert fake_console.has_call("warn")


def test_run_oneapi_installer_reports_an_elevated_launch_exception(monkeypatch, fake_console):
    """Check that run oneapi installer reports an elevated launch exception."""
    calls = []

    def fake_run(cmd, **kwargs):
        """Check that fake run."""
        calls.append(cmd)
        if len(calls) == 1:
            err = OSError("needs elevation")
            err.winerror = oneapi._ELEVATION_REQUIRED
            raise err
        raise RuntimeError("powershell missing")

    monkeypatch.setattr(oneapi.subprocess, "run", fake_run)

    result = oneapi.run_oneapi_installer(Path("installer.exe"))

    assert result is False
    assert fake_console.has_call("error")


def test_intel_llvm_defines_no_unused_private_function():
    """Check that intel llvm defines no unused private function."""
    source = Path(intel_llvm.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    private = [node.name for node in tree.body
               if isinstance(node, ast.FunctionDef) and node.name.startswith("_")]
    unused = [name for name in private if len(re.findall(rf"\b{name}\b", source)) < 2]
    assert unused == []
