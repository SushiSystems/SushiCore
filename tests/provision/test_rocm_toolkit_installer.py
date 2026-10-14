# test_rocm_toolkit_installer.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""A tarball becomes a ROCm root only when it unpacks whole and holds the HIP headers."""

from __future__ import annotations

import io
import tarfile
from pathlib import Path

import pytest

from sushicore.provision.gpu.rocm_package import RocmPackage
from sushicore.provision.gpu.rocm_toolkit_installer import (
    RocmInstallError,
    RocmTarballInstaller,
    is_rocm_root,
)

K_PACKAGE = RocmPackage((7, 13, 0), "gfx110X-all", "https://example.invalid/rocm.tar.gz")


def _tarball(files: dict[str, bytes]) -> bytes:
    """Return a ``.tar.gz`` whose top level holds *files*, as AMD's tarballs do."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as bundle:
        for name, data in files.items():
            info = tarfile.TarInfo(f"./{name}")
            info.size = len(data)
            bundle.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


class _Server:
    """Serves one body and counts the downloads."""

    def __init__(self, body: bytes) -> None:
        """Store the body."""
        self.body = body
        self.fetched = 0

    def download(self, url: str, dest: Path) -> None:
        """Write the body to *dest*."""
        self.fetched += 1
        dest.write_bytes(self.body)


@pytest.fixture(autouse=True)
def _console(recording_console):
    """Give every test a console to report downloads on."""
    return recording_console


def test_install_unpacks_the_tarball_as_the_root(tmp_path):
    """Check that the tarball's top level becomes the release folder, and nothing is kept."""
    server = _Server(_tarball({"include/hip/hip_runtime.h": b"", "bin/hipcc": b"x"}))
    installer = RocmTarballInstaller(tmp_path, server.download)

    root = installer.install(K_PACKAGE)

    assert root == tmp_path / "7.13.0-gfx110X-all"
    assert is_rocm_root(root)
    assert (root / "bin" / "hipcc").read_bytes() == b"x"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["7.13.0-gfx110X-all"]


def test_an_installed_release_is_not_downloaded_again(tmp_path):
    """Check that a second install is free."""
    server = _Server(_tarball({"include/hip/hip_runtime.h": b""}))
    installer = RocmTarballInstaller(tmp_path, server.download)
    installer.install(K_PACKAGE)

    installer.install(K_PACKAGE)

    assert server.fetched == 1


def test_a_tarball_without_hip_headers_installs_nothing(tmp_path):
    """Check that something that is not a ROCm root is refused."""
    installer = RocmTarballInstaller(tmp_path, _Server(_tarball({"README": b""})).download)

    with pytest.raises(RocmInstallError):
        installer.install(K_PACKAGE)

    assert not installer.is_installed(K_PACKAGE.label)


def test_a_corrupt_tarball_installs_nothing(tmp_path):
    """Check that a body that is not a tarball is a RocmInstallError."""
    installer = RocmTarballInstaller(tmp_path, _Server(b"not a tarball").download)

    with pytest.raises(RocmInstallError):
        installer.install(K_PACKAGE)

    assert not installer.is_installed(K_PACKAGE.label)


def test_a_failed_download_installs_nothing(tmp_path):
    """Check that a transport failure leaves no partial file."""
    def fail(url, dest):
        """Write half a file, then fail as a dropped connection does."""
        dest.write_bytes(b"half")
        raise OSError("connection reset")

    with pytest.raises(RocmInstallError):
        RocmTarballInstaller(tmp_path, fail).install(K_PACKAGE)

    assert not list((tmp_path / "downloads").iterdir())
