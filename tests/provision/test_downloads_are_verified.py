# test_downloads_are_verified.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026 Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Regression: no download path extracts or runs a file whose pinned SHA-256 does not match."""

from __future__ import annotations

import hashlib
import types
import zipfile
from pathlib import Path

import pytest

from sushicore.errors import DigestMismatchError
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.download_verifier import DownloadVerifier, bind_verifier
from sushicore.provision.gpu import windows_installer as wi
from sushicore.provision.gpu.cuda import WindowsCudaLocator
from sushicore.provision.packages import direct_download as dd
from sushicore.provision.toolchains import adaptivecpp, intel_llvm, oneapi

K_WRONG_DIGEST = "0" * 64
K_PAYLOAD = b"downloaded bytes"
K_PAYLOAD_DIGEST = hashlib.sha256(K_PAYLOAD).hexdigest()

K_ZIP_INSTALLS = [
    ("_install_cmake_direct", "cmake", "cmake-1.0/bin/cmake.exe", ("cmake",)),
    ("_install_ninja_direct", "ninja", "ninja.exe", ("ninja.exe",)),
    ("_install_doxygen_direct", "doxygen", "doxygen-1.0/doxygen.exe", ("doxygen",)),
]


@pytest.fixture
def pins():
    """Bind a verifier over the digests a test stores, then unbind it."""
    digests: dict[str, str] = {}
    verifier = DownloadVerifier(digests)
    bind_verifier(verifier)
    yield types.SimpleNamespace(digests=digests, verifier=verifier)
    bind_verifier(None)


def _write_payload(dest: Path) -> None:
    """Write the fixed payload to *dest*, as a download would."""
    Path(dest).write_bytes(K_PAYLOAD)


def _write_zip(dest: Path, member: str) -> None:
    """Write a single-entry zip archive to *dest*."""
    with zipfile.ZipFile(dest, "w") as archive:
        archive.writestr(member, b"")


def _stub_zip_download(monkeypatch, member: str) -> list[Path]:
    """Make the direct-download manager fetch a one-member zip; return where it was written."""
    written: list[Path] = []

    def download(url, dest):
        """Write the archive in place of fetching *url*."""
        del url
        _write_zip(dest, member)
        written.append(Path(dest))

    monkeypatch.setattr(dd, "_cmake_on_system", lambda: "")
    monkeypatch.setattr(dd, "gh_latest_asset", lambda repo, glob: "https://example.invalid/a.zip")
    monkeypatch.setattr(dd, "download", download)
    monkeypatch.setattr(dd, "_add_to_user_path_windows", lambda directory: True)
    return written


@pytest.mark.parametrize(("installer", "name", "member", "installed"), K_ZIP_INSTALLS)
def test_a_tool_archive_with_the_wrong_digest_is_not_extracted(
        installer, name, member, installed, monkeypatch, provision_home, recording_console, pins):
    """Check that a mismatching archive stops the install and leaves nothing extracted."""
    written = _stub_zip_download(monkeypatch, member)
    pins.digests[name] = K_WRONG_DIGEST

    with pytest.raises(DigestMismatchError):
        getattr(dd, installer)()

    assert not dd.tools_dir().joinpath(*installed).exists()
    assert not written[0].exists()


@pytest.mark.parametrize(("installer", "name", "member", "installed"), K_ZIP_INSTALLS)
def test_a_tool_archive_with_the_pinned_digest_installs(
        installer, name, member, installed, monkeypatch, provision_home, recording_console, pins):
    """Check that a matching archive installs and is not reported as unverified."""
    written = _stub_zip_download(monkeypatch, member)
    real_download = dd.download

    def download_and_pin(url, dest):
        """Write the archive, then pin the digest it turned out to have."""
        real_download(url, dest)
        pins.digests[name] = hashlib.sha256(Path(dest).read_bytes()).hexdigest()

    monkeypatch.setattr(dd, "download", download_and_pin)

    assert getattr(dd, installer)() is True
    assert written and dd.tools_dir().joinpath(*installed).exists()
    assert pins.verifier.unverified() == ()


@pytest.mark.parametrize(("installer", "name", "member", "installed"), K_ZIP_INSTALLS)
def test_a_tool_archive_with_no_digest_installs_and_is_named(
        installer, name, member, installed, monkeypatch, provision_home, recording_console, pins):
    """Check that an unpinned archive installs as before and is recorded by name."""
    _stub_zip_download(monkeypatch, member)

    assert getattr(dd, installer)() is True
    assert dd.tools_dir().joinpath(*installed).exists()
    assert pins.verifier.unverified() == (name,)


def _stub_git_download(monkeypatch) -> list[list[str]]:
    """Make the git installer download the payload; return the commands it then runs."""
    runs: list[list[str]] = []

    def run(command, **_kwargs):
        """Record the installer command and report success."""
        runs.append(command)
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(dd, "gh_latest_asset", lambda repo, glob: "https://example.invalid/g.exe")
    monkeypatch.setattr(dd, "download", lambda url, dest: _write_payload(dest))
    monkeypatch.setattr(dd.subprocess, "run", run)
    return runs


def test_a_git_installer_with_the_wrong_digest_is_not_run(monkeypatch, recording_console, pins):
    """Check that a mismatching Git installer stops the install before it is launched."""
    runs = _stub_git_download(monkeypatch)
    pins.digests["git"] = K_WRONG_DIGEST

    with pytest.raises(DigestMismatchError):
        dd._install_git_direct()

    assert runs == []


def test_a_git_installer_with_the_pinned_digest_is_run(monkeypatch, recording_console, pins):
    """Check that a matching Git installer is launched."""
    runs = _stub_git_download(monkeypatch)
    pins.digests["git"] = K_PAYLOAD_DIGEST

    assert dd._install_git_direct() is True
    assert len(runs) == 1
    assert pins.verifier.unverified() == ()


def _stub_intel_llvm(monkeypatch) -> list[Path]:
    """Make the intel/llvm installer download the payload; return the archives it extracts."""
    extracted: list[Path] = []

    def extract(archive, dest):
        """Record the archive and lay down the compiler the installer looks for."""
        extracted.append(archive)
        (dest / "bin").mkdir(parents=True, exist_ok=True)
        (dest / "bin" / "clang++").touch()

    monkeypatch.setattr(intel_llvm, "gh_latest_release_asset",
                        lambda *a, **k: ("nightly-2", "https://example.invalid/a"))
    monkeypatch.setattr(intel_llvm, "download", lambda url, dest: _write_payload(dest))
    monkeypatch.setattr(intel_llvm, "_extract_tar_gz", extract)
    return extracted


def test_an_intel_llvm_bundle_with_the_wrong_digest_is_not_extracted(
        monkeypatch, provision_home, recording_console, pins):
    """Check that a mismatching bundle stops the install before extraction."""
    extracted = _stub_intel_llvm(monkeypatch)
    pins.digests["intel-llvm"] = K_WRONG_DIGEST

    with pytest.raises(DigestMismatchError):
        intel_llvm.install_intel_llvm(ProvisionSettings(platform="linux"), dry_run=False)

    assert extracted == []


def test_an_intel_llvm_bundle_with_the_pinned_digest_is_extracted(
        monkeypatch, provision_home, recording_console, pins):
    """Check that a matching bundle is extracted."""
    extracted = _stub_intel_llvm(monkeypatch)
    pins.digests["intel-llvm"] = K_PAYLOAD_DIGEST

    assert intel_llvm.install_intel_llvm(ProvisionSettings(platform="linux"), dry_run=False)
    assert len(extracted) == 1
    assert pins.verifier.unverified() == ()


def _stub_llvm_vendor(monkeypatch) -> list[list[str]]:
    """Make the LLVM vendor step download the payload; return the commands it then runs."""
    runs: list[list[str]] = []

    def run(command, **_kwargs):
        """Record the installer launch and report success."""
        runs.append(command)
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(adaptivecpp, "gh_tagged_asset",
                        lambda repo, tag, asset: "https://example.invalid/llvm.exe")
    monkeypatch.setattr(adaptivecpp, "download", lambda url, dest: _write_payload(dest))
    monkeypatch.setattr(adaptivecpp.subprocess, "run", run)
    return runs


def test_an_llvm_installer_with_the_wrong_digest_is_not_run(
        monkeypatch, provision_home, recording_console, pins):
    """Check that a mismatching LLVM installer stops the install before it is launched."""
    runs = _stub_llvm_vendor(monkeypatch)
    pins.digests["adaptivecpp"] = K_WRONG_DIGEST

    with pytest.raises(DigestMismatchError):
        adaptivecpp._vendor_llvm_windows()

    assert runs == []


def test_an_llvm_installer_with_the_pinned_digest_is_run(
        monkeypatch, provision_home, recording_console, pins):
    """Check that a matching LLVM installer is launched."""
    runs = _stub_llvm_vendor(monkeypatch)
    pins.digests["adaptivecpp"] = K_PAYLOAD_DIGEST

    adaptivecpp._vendor_llvm_windows()

    assert len(runs) == 1
    assert pins.verifier.unverified() == ()


def _stub_oneapi_curl(monkeypatch, tmp_path) -> Path:
    """Make curl write the payload into a temporary home; return the installer path."""
    def run(command, **_kwargs):
        """Write the payload where curl's ``-o`` points."""
        Path(command[command.index("-o") + 1]).write_bytes(K_PAYLOAD)
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(oneapi.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(oneapi.subprocess, "run", run)
    return tmp_path / "intel-oneapi-toolkit-offline.exe"


def test_a_oneapi_installer_with_the_wrong_digest_is_not_returned(
        monkeypatch, tmp_path, recording_console, pins):
    """Check that a mismatching oneAPI installer stops the install and is deleted."""
    installer = _stub_oneapi_curl(monkeypatch, tmp_path)
    pins.digests["oneapi"] = K_WRONG_DIGEST

    with pytest.raises(DigestMismatchError):
        oneapi.download_oneapi_installer()

    assert not installer.exists()


def test_a_oneapi_installer_left_by_an_earlier_run_is_verified_too(
        monkeypatch, tmp_path, recording_console, pins):
    """Check that an installer already on disk is checked before it is reused."""
    installer = _stub_oneapi_curl(monkeypatch, tmp_path)
    installer.write_bytes(b"left by an earlier run")
    pins.digests["oneapi"] = K_PAYLOAD_DIGEST

    with pytest.raises(DigestMismatchError):
        oneapi.download_oneapi_installer()

    assert not installer.exists()


def test_a_oneapi_installer_with_the_pinned_digest_is_returned(
        monkeypatch, tmp_path, recording_console, pins):
    """Check that a matching oneAPI installer is handed on to be run."""
    installer = _stub_oneapi_curl(monkeypatch, tmp_path)
    pins.digests["oneapi"] = K_PAYLOAD_DIGEST

    assert oneapi.download_oneapi_installer() == installer
    assert pins.verifier.unverified() == ()


class _FixedDownloader:
    """Returns one installer file for every fetch."""

    def __init__(self, result: Path) -> None:
        """Store the path every fetch returns."""
        self._result = result

    def fetch(self, download, dest_dir):
        """Return the stored path."""
        del download, dest_dir
        return self._result


class _RecordingRunner:
    """Records elevated runs and reports success."""

    def __init__(self) -> None:
        """Start with no recorded runs."""
        self.runs: list[Path] = []

    def command(self, exe, args):
        """Return a recognisable command line."""
        return ["elevate", str(exe), *args]

    def run(self, exe, args):
        """Record the run."""
        del args
        self.runs.append(exe)
        return wi.ElevatedResult(0)


class _EmptyEnvironment:
    """Reports every machine variable as unset."""

    def read(self, name):
        """Return None for *name*."""
        del name
        return None


def _cuda_locator(tmp_path) -> tuple[WindowsCudaLocator, _RecordingRunner]:
    """Return a CUDA locator whose download is the payload, and the runner it would launch."""
    exe = tmp_path / "installers" / "cuda.exe"
    exe.parent.mkdir(parents=True)
    exe.write_bytes(K_PAYLOAD)
    runner = _RecordingRunner()
    tools = wi.WindowsInstallerTools(downloader=_FixedDownloader(exe), runner=runner,
                                     environment=_EmptyEnvironment(),
                                     dest_dir=lambda: tmp_path / "installers")
    return WindowsCudaLocator(tools), runner


def test_a_cuda_installer_with_the_wrong_digest_is_not_run(
        monkeypatch, tmp_path, recording_console, pins):
    """Check that a mismatching CUDA installer stops the install before the elevated run."""
    monkeypatch.delenv("CUDA_PATH", raising=False)
    locator, runner = _cuda_locator(tmp_path)
    pins.digests["cuda"] = K_WRONG_DIGEST

    with pytest.raises(DigestMismatchError):
        locator.provision(types.SimpleNamespace(platform="windows"), False)

    assert runner.runs == []


def test_a_cuda_installer_with_the_pinned_digest_is_run(
        monkeypatch, tmp_path, recording_console, pins):
    """Check that a matching CUDA installer reaches the elevated run."""
    monkeypatch.delenv("CUDA_PATH", raising=False)
    locator, runner = _cuda_locator(tmp_path)
    pins.digests["cuda"] = K_PAYLOAD_DIGEST

    locator.provision(types.SimpleNamespace(platform="windows"), False)

    assert len(runner.runs) == 1
    assert pins.verifier.unverified() == ()
