# test_cuda_toolkit_installer.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Releases are assembled from verified archives into one root, and nothing unverified lands."""

from __future__ import annotations

import hashlib
import io
import subprocess
import tarfile
import types
import zipfile
from pathlib import Path

import pytest

from sushicore.provision.gpu import cuda_toolkit_installer as installer_mod
from sushicore.provision.gpu.cuda_release import RedistArchive, RedistRelease
from sushicore.provision.gpu.cuda_toolkit_installer import (
    RedistToolkitInstaller,
    ToolkitInstallError,
    list_gpu_architectures,
    nvcc_in,
)

K_ROOT = "https://example.invalid/"
K_NVCC_NAME = nvcc_in(Path(".")).name


@pytest.fixture(autouse=True)
def _console(recording_console):
    """Give every test a console to report downloads on."""
    return recording_console


def _zip(top: str, files: dict[str, str]) -> bytes:
    """Return a zip archive holding *files* under the folder *top*."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as bundle:
        for name, text in files.items():
            bundle.writestr(f"{top}/{name}", text)
    return buffer.getvalue()


class _Server:
    """Serves archive bodies by URL and records what was downloaded."""

    def __init__(self) -> None:
        """Start with nothing served."""
        self.bodies: dict[str, bytes] = {}
        self.fetched: list[str] = []

    def add(self, name: str, files: dict[str, str], digest: str | None = None) -> RedistArchive:
        """Serve one component archive and return its index entry."""
        body = _zip(f"{name}-archive", files)
        url = f"{K_ROOT}{name}.zip"
        self.bodies[url] = body
        return RedistArchive(url, digest or hashlib.sha256(body).hexdigest())

    def download(self, url: str, dest: Path) -> None:
        """Write the body served at *url* to *dest*."""
        self.fetched.append(url)
        dest.write_bytes(self.bodies[url])


def _release(server: _Server, **overrides: RedistArchive) -> RedistRelease:
    """Return a release with the three required components and any *overrides*."""
    archives = {
        "cuda_nvcc": server.add("cuda_nvcc", {f"bin/{K_NVCC_NAME}": "nvcc"}),
        "cuda_cudart": server.add("cuda_cudart", {"include/cuda.h": "#define CUDA_VERSION"}),
        "cuda_nvml_dev": server.add("cuda_nvml_dev", {"include/nvml.h": ""}),
    }
    archives.update(overrides)
    return RedistRelease((13, 1, 2), archives)


def test_install_merges_every_component_into_one_root(tmp_path):
    """Check that the components and a published companion share one root."""
    server = _Server()
    release = _release(server, libnvvm=server.add("libnvvm", {"nvvm/libdevice/x.bc": ""}))
    installer = RedistToolkitInstaller(tmp_path, server.download)

    root = installer.install(release)

    assert root == tmp_path / "13.1.2"
    assert nvcc_in(root).is_file()
    assert (root / "include" / "cuda.h").is_file()
    assert (root / "include" / "nvml.h").is_file()
    assert (root / "nvvm" / "libdevice" / "x.bc").is_file()
    assert installer.is_installed("13.1.2")
    assert sorted(p.name for p in tmp_path.iterdir()) == ["13.1.2"]


def test_install_of_an_installed_release_downloads_nothing(tmp_path):
    """Check that a release already in place is returned untouched."""
    server = _Server()
    release = _release(server)
    installer = RedistToolkitInstaller(tmp_path, server.download)
    installer.install(release)
    server.fetched.clear()

    installer.install(release)

    assert server.fetched == []


def test_a_mismatching_archive_installs_nothing(tmp_path):
    """Check that a wrong digest stops the install and leaves no root behind."""
    server = _Server()
    bad = server.add("cuda_cudart", {"include/cuda.h": ""}, digest="0" * 64)
    installer = RedistToolkitInstaller(tmp_path, server.download)

    with pytest.raises(ToolkitInstallError):
        installer.install(_release(server, cuda_cudart=bad))

    assert not installer.is_installed("13.1.2")
    assert not list((tmp_path / "downloads").glob("*cudart*"))


def test_a_missing_required_component_installs_nothing(tmp_path):
    """Check that a release without nvml_dev is refused."""
    server = _Server()
    release = _release(server)
    del release.archives["cuda_nvml_dev"]

    with pytest.raises(ToolkitInstallError):
        RedistToolkitInstaller(tmp_path, server.download).install(release)


def test_an_archive_escaping_its_folder_is_refused(tmp_path):
    """Check that a zip member with ``..`` in its path is not extracted."""
    server = _Server()
    body = _zip("cuda_nvcc-archive", {"../../escape.txt": ""})
    server.bodies[f"{K_ROOT}evil.zip"] = body
    evil = RedistArchive(f"{K_ROOT}evil.zip", hashlib.sha256(body).hexdigest())

    with pytest.raises(ToolkitInstallError):
        RedistToolkitInstaller(tmp_path / "cuda", server.download).install(
            _release(server, cuda_nvcc=evil))

    assert not (tmp_path / "escape.txt").exists()


def test_a_tar_xz_archive_unpacks(tmp_path):
    """Check that the Linux archive format installs as the zip one does."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:xz") as bundle:
        data = b"nvcc"
        info = tarfile.TarInfo(f"cuda_nvcc-archive/bin/{K_NVCC_NAME}")
        info.size = len(data)
        bundle.addfile(info, io.BytesIO(data))
    server = _Server()
    server.bodies[f"{K_ROOT}nvcc.tar.xz"] = buffer.getvalue()
    nvcc = RedistArchive(f"{K_ROOT}nvcc.tar.xz", hashlib.sha256(buffer.getvalue()).hexdigest())

    root = RedistToolkitInstaller(tmp_path, server.download).install(
        _release(server, cuda_nvcc=nvcc))

    assert nvcc_in(root).read_bytes() == b"nvcc"


def test_probe_unpacks_only_the_compiler_and_cleans_up(tmp_path, monkeypatch):
    """Check that a probe downloads nvcc alone and leaves no probe folder."""
    server = _Server()
    release = _release(server)
    seen: list[Path] = []
    monkeypatch.setattr(installer_mod, "list_gpu_architectures",
                        lambda nvcc: seen.append(nvcc) or frozenset({"89"}))

    archs = RedistToolkitInstaller(tmp_path, server.download).probe_architectures(release)

    assert archs == frozenset({"89"})
    assert server.fetched == [f"{K_ROOT}cuda_nvcc.zip"]
    assert seen and not seen[0].exists()


def test_list_gpu_architectures_reads_the_compute_lines(monkeypatch):
    """Check that ``compute_89`` becomes ``89`` and other lines are ignored."""
    monkeypatch.setattr(installer_mod.subprocess, "run", lambda *a, **k: types.SimpleNamespace(
        stdout="compute_75\ncompute_89\nwarning: x\n"))

    assert list_gpu_architectures(Path("nvcc")) == frozenset({"75", "89"})


def test_list_gpu_architectures_of_a_broken_compiler_raises(monkeypatch):
    """Check that an nvcc that does not run is a ToolkitInstallError."""
    def fail(*args, **kwargs):
        """Fail as a missing binary does."""
        raise subprocess.CalledProcessError(1, "nvcc")

    monkeypatch.setattr(installer_mod.subprocess, "run", fail)

    with pytest.raises(ToolkitInstallError):
        list_gpu_architectures(Path("nvcc"))
