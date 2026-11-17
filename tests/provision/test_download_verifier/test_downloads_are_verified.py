# test_downloads_are_verified.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Regression: no download path extracts or runs a file whose pinned SHA-256 does not match."""

from __future__ import annotations

import hashlib
import io
import tarfile
import types
import zipfile
from pathlib import Path

import pytest

from sushicore.deps_fragment import Download
from sushicore.errors import DigestMismatchError
from sushicore.proc_memory import RecordingRunner
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.download_verifier import DownloadVerifier, bind_verifier
from sushicore.provision.packages import direct_download as dd
from sushicore.provision.llvm_plans import windows as llvm_windows
from sushicore.provision.toolchains import intel_llvm, oneapi
from sushicore.provision.toolchains.stamp import toolchains_dir


pytestmark = pytest.mark.medium

K_WRONG_DIGEST = "0" * 64
K_URL = "https://example.invalid/asset"
K_ONEAPI_INSTALLER = "intel-oneapi-toolkit-offline.exe"


def _digest(payload: bytes) -> str:
    """Return the SHA-256 of *payload* as the manifest pins it."""
    return hashlib.sha256(payload).hexdigest()


def _zip_bytes(member: str) -> bytes:
    """Return a zip archive holding one empty entry named *member*."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(member, b"")
    return buffer.getvalue()


def _bundle_bytes() -> bytes:
    """Return a ``.tar.gz`` holding the compiler the intel/llvm installer looks for."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        info = tarfile.TarInfo("llvm-sycl/bin/clang++")
        archive.addfile(info, io.BytesIO(b""))
    return buffer.getvalue()


K_INSTALLER_BYTES = b"installer bytes"


class _Fetch:
    """A download transport that writes a fixed payload and remembers where."""

    def __init__(self, payload: bytes) -> None:
        """Serve *payload* for every URL."""
        self.payload = payload
        self.written: list[Path] = []

    def __call__(self, url: str, dest: Path) -> None:
        """Write the payload to *dest* in place of fetching *url*."""
        del url
        Path(dest).write_bytes(self.payload)
        self.written.append(Path(dest))


class _CurlWritesPayload(RecordingRunner):
    """A runner that records each command and, for curl, writes the payload where ``-o`` points."""

    def __init__(self, console, payload: bytes) -> None:
        """Serve *payload* for every download."""
        super().__init__(console)
        self.payload = payload

    def run(self, cmd: list[str], cwd: Path | None, env: dict[str, str] | None = None) -> int:
        """Write the payload to the path after ``-o``, then record the command."""
        Path(cmd[cmd.index("-o") + 1]).write_bytes(self.payload)
        return super().run(cmd, cwd, env)


def _resolve_tagged_asset(repo: str, tag: str, asset: str) -> str:
    """Return a fixed URL for any tagged GitHub asset lookup."""
    del repo, tag, asset
    return K_URL


def _pin(name: str) -> Download:
    """Return a pinned download for the entry *name* with a fixed URL."""
    return Download(name, "v1", K_URL, "0" * 64)


def _no_cmake_on_system() -> str:
    """Report that no cmake is installed, so the installer proceeds."""
    return ""


def _ignore_path(directory: str) -> None:
    """Take a directory the installer would put on the user's PATH and leave PATH alone."""
    del directory


K_ZIP_INSTALLS = [
    (dd._install_cmake_direct, "cmake", _zip_bytes("cmake-1.0/bin/cmake.exe"),
     ("cmake", "bin", "cmake.exe"), {"cmake_on_system": _no_cmake_on_system, "pin": _pin}),
    (dd._install_ninja_direct, "ninja", _zip_bytes("ninja.exe"), ("ninja.exe",), {"pin": _pin}),
    (dd._install_doxygen_direct, "doxygen", _zip_bytes("doxygen-1.0/doxygen.exe"),
     ("doxygen", "doxygen.exe"), {"pin": _pin}),
]


@pytest.fixture
def pins():
    """Bind a verifier over the digests a test stores, then unbind it."""
    digests: dict[str, str] = {}
    verifier = DownloadVerifier(digests)
    bind_verifier(verifier)
    yield types.SimpleNamespace(digests=digests, verifier=verifier)
    bind_verifier(None)


@pytest.mark.parametrize(("installer", "name", "payload", "installed", "extra"), K_ZIP_INSTALLS)
def test_a_tool_archive_with_the_wrong_digest_is_not_extracted(
        installer, name, payload, installed, extra, provision_home, recording_console, pins):
    """Check that a mismatching archive stops the install and leaves nothing extracted."""
    fetch = _Fetch(payload)
    pins.digests[name] = K_WRONG_DIGEST

    with pytest.raises(DigestMismatchError):
        installer(fetch=fetch, on_path=_ignore_path, **extra)

    assert not dd.tools_dir().joinpath(*installed).exists()
    assert not fetch.written[0].exists()


@pytest.mark.parametrize(("installer", "name", "payload", "installed", "extra"), K_ZIP_INSTALLS)
def test_a_tool_archive_with_the_pinned_digest_installs(
        installer, name, payload, installed, extra, provision_home, recording_console, pins):
    """Check that a matching archive installs and is not reported as unverified."""
    pins.digests[name] = _digest(payload)

    done = installer(fetch=_Fetch(payload), on_path=_ignore_path,
                     **extra)

    assert done is True
    assert dd.tools_dir().joinpath(*installed).exists()
    assert pins.verifier.unverified() == ()


@pytest.mark.parametrize(("installer", "name", "payload", "installed", "extra"), K_ZIP_INSTALLS)
def test_a_tool_archive_with_no_digest_installs_and_is_named(
        installer, name, payload, installed, extra, provision_home, recording_console, pins):
    """Check that an unpinned archive installs as before and is recorded by name."""
    done = installer(fetch=_Fetch(payload), on_path=_ignore_path,
                     **extra)

    assert done is True
    assert dd.tools_dir().joinpath(*installed).exists()
    assert pins.verifier.unverified() == (name,)


def test_a_git_installer_with_the_wrong_digest_is_not_run(recording_console, pins):
    """Check that a mismatching Git installer stops the install before it is launched."""
    runner = RecordingRunner(recording_console)
    pins.digests["git"] = K_WRONG_DIGEST

    with pytest.raises(DigestMismatchError):
        dd._install_git_direct(pin=_pin,
                               fetch=_Fetch(K_INSTALLER_BYTES), runner=runner)

    assert runner.commands == []


def test_a_git_installer_with_the_pinned_digest_is_run(recording_console, pins):
    """Check that a matching Git installer is launched once."""
    runner = RecordingRunner(recording_console)
    pins.digests["git"] = _digest(K_INSTALLER_BYTES)

    installed = dd._install_git_direct(pin=_pin,
                                       fetch=_Fetch(K_INSTALLER_BYTES), runner=runner)

    assert installed is True
    assert len(runner.commands) == 1
    assert pins.verifier.unverified() == ()


def test_an_intel_llvm_bundle_with_the_wrong_digest_is_not_extracted(
        provision_home, recording_console, pins):
    """Check that a mismatching bundle stops the install before extraction."""
    pins.digests["intel-llvm"] = K_WRONG_DIGEST

    with pytest.raises(DigestMismatchError):
        intel_llvm.install_intel_llvm(
            ProvisionSettings(platform="linux"), dry_run=False,
            pin=_pin, fetch=_Fetch(_bundle_bytes()))

    assert not (toolchains_dir() / "llvm-sycl" / "bin" / "clang++").exists()


def test_an_intel_llvm_bundle_with_the_pinned_digest_is_extracted(
        provision_home, recording_console, pins):
    """Check that a matching bundle is extracted and not reported as unverified."""
    bundle = _bundle_bytes()
    pins.digests["intel-llvm"] = _digest(bundle)

    root = intel_llvm.install_intel_llvm(
        ProvisionSettings(platform="linux"), dry_run=False,
        pin=_pin, fetch=_Fetch(bundle))

    assert (Path(root) / "bin" / "clang++").is_file()
    assert pins.verifier.unverified() == ()


def test_an_llvm_installer_with_the_wrong_digest_is_not_run(
        provision_home, recording_console, pins):
    """Check that a mismatching LLVM installer stops the install before it is launched."""
    runner = RecordingRunner(recording_console)
    pins.digests["adaptivecpp"] = K_WRONG_DIGEST

    with pytest.raises(DigestMismatchError):
        llvm_windows.vendor_llvm_windows(
            resolve_asset=_resolve_tagged_asset, fetch=_Fetch(K_INSTALLER_BYTES),
            runner=runner)

    assert runner.commands == []


def test_an_llvm_installer_with_the_pinned_digest_is_run(
        provision_home, recording_console, pins):
    """Check that a matching LLVM installer is launched once."""
    runner = RecordingRunner(recording_console)
    pins.digests["adaptivecpp"] = _digest(K_INSTALLER_BYTES)

    llvm_windows.vendor_llvm_windows(
        resolve_asset=_resolve_tagged_asset, fetch=_Fetch(K_INSTALLER_BYTES), runner=runner)

    assert len(runner.commands) == 1
    assert pins.verifier.unverified() == ()


def test_a_oneapi_installer_with_the_wrong_digest_is_not_returned(
        tmp_path, recording_console, pins):
    """Check that a mismatching oneAPI installer stops the install and is deleted."""
    pins.digests["oneapi"] = K_WRONG_DIGEST

    with pytest.raises(DigestMismatchError):
        oneapi.download_oneapi_installer(
            directory=tmp_path, runner=_CurlWritesPayload(recording_console, K_INSTALLER_BYTES))

    assert not (tmp_path / K_ONEAPI_INSTALLER).exists()


def test_a_oneapi_installer_left_by_an_earlier_run_is_verified_too(
        tmp_path, recording_console, pins):
    """Check that an installer already on disk is checked before it is reused."""
    installer = tmp_path / K_ONEAPI_INSTALLER
    installer.write_bytes(b"left by an earlier run")
    pins.digests["oneapi"] = _digest(K_INSTALLER_BYTES)

    with pytest.raises(DigestMismatchError):
        oneapi.download_oneapi_installer(
            directory=tmp_path, runner=_CurlWritesPayload(recording_console, K_INSTALLER_BYTES))

    assert not installer.exists()


def test_a_oneapi_installer_with_the_pinned_digest_is_returned(
        tmp_path, recording_console, pins):
    """Check that a matching oneAPI installer is handed on to be run."""
    pins.digests["oneapi"] = _digest(K_INSTALLER_BYTES)

    returned = oneapi.download_oneapi_installer(
        directory=tmp_path, runner=_CurlWritesPayload(recording_console, K_INSTALLER_BYTES))

    assert returned == tmp_path / K_ONEAPI_INSTALLER
    assert pins.verifier.unverified() == ()
