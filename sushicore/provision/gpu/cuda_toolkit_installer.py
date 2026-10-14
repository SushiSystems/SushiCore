# cuda_toolkit_installer.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Installs a CUDA release from NVIDIA's redistributable archives into a folder the user owns.

No installer runs and nothing needs administrator rights: each component archive is
downloaded, checked against the SHA-256 NVIDIA publishes, and merged into one toolkit root
laid out like a full CUDA install. Releases sit side by side under ``<home>/cuda/<version>``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tarfile
import typing
import urllib.request
import zipfile
from pathlib import Path

from sushicore.errors import DigestMismatchError

from .. import home
from .._output import console
from ..integrity import verify_sha256
from ..system import USER_AGENT
from .cuda_release import RedistArchive, RedistRelease
from .toolkit_vendor import ToolkitSourceError

#: The components the SYCL toolchain and the Unified Runtime adapter build need.
K_REQUIRED_COMPONENTS = ("cuda_nvcc", "cuda_cudart", "cuda_nvml_dev")

#: Parts of the compiler that some releases publish on their own; installed when published.
K_COMPANION_COMPONENTS = ("cuda_crt", "libnvvm", "cuda_cccl")

K_NVCC = "nvcc.exe" if os.name == "nt" else "nvcc"

#: The prefix that puts a Windows path in its extended-length form.
K_EXTENDED_PREFIX = "\\\\?\\"


class ToolkitInstallError(ToolkitSourceError):
    """A release could not be downloaded, verified or unpacked."""


def toolkits_dir() -> Path:
    """Return ``<home>/cuda``, the folder every installed release lives under."""
    return home.root() / "cuda"


def nvcc_in(root: Path) -> Path:
    """Return the nvcc binary of the toolkit rooted at *root*."""
    return root / "bin" / K_NVCC


def list_gpu_architectures(nvcc: Path) -> frozenset[str]:
    """Return the architectures *nvcc* builds for, without the ``compute_`` prefix.

    Raises:
        ToolkitInstallError: nvcc did not run.
    """
    try:
        done = subprocess.run([str(nvcc), "--list-gpu-arch"], capture_output=True, text=True,
                              check=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as error:
        raise ToolkitInstallError(f"{nvcc} --list-gpu-arch failed: {error}") from error
    return frozenset(line.strip()[len("compute_"):] for line in done.stdout.splitlines()
                     if line.strip().startswith("compute_"))


@typing.final
class RedistToolkitInstaller:
    """Downloads, verifies and unpacks CUDA releases under one folder.

    Args:
        target_dir: The folder releases are installed under; defaults to :func:`toolkits_dir`.
        download: Writes the body at a URL to a path; raises ``OSError`` on failure.
    """

    def __init__(self, target_dir: Path | None = None,
                 download: typing.Callable[[str, Path], None] | None = None) -> None:
        """Store the target folder and the download function."""
        self._target_dir = target_dir
        self._download = download or _download

    @property
    def base_dir(self) -> Path:
        """Return the folder releases are installed under."""
        return self._base()

    def root_of(self, release_label: str) -> Path:
        """Return where the release labelled *release_label* is, or would be, installed."""
        return self._base() / release_label

    def is_installed(self, release_label: str) -> bool:
        """Report whether the release's nvcc is in place."""
        return nvcc_in(self.root_of(release_label)).is_file()

    def probe_architectures(self, release: RedistRelease) -> frozenset[str]:
        """Return the architectures the release's compiler builds for, unpacking only nvcc.

        Raises:
            ToolkitInstallError: The compiler archive is missing, mismatching or does not run.
        """
        if self.is_installed(release.label):
            return list_gpu_architectures(nvcc_in(self.root_of(release.label)))
        probe_root = self._base() / f".{release.label}-probe"
        _remove_tree(probe_root)
        try:
            self._unpack(self._archive(release, "cuda_nvcc"), probe_root)
            return list_gpu_architectures(nvcc_in(probe_root))
        finally:
            _remove_tree(probe_root)

    def install(self, release: RedistRelease) -> Path:
        """Install *release* and return its root; an installed release is returned as is.

        Raises:
            ToolkitInstallError: A component is missing, mismatching or does not unpack.
        """
        root = self.root_of(release.label)
        if self.is_installed(release.label):
            return root
        staging = self._base() / f".{release.label}"
        _remove_tree(staging)
        names = [*K_REQUIRED_COMPONENTS,
                 *(name for name in K_COMPANION_COMPONENTS if name in release.archives)]
        for name in names:
            self._unpack(self._archive(release, name), staging)
        _remove_tree(root)
        os.replace(_long_path(staging), _long_path(root))
        self.discard_downloads()
        return root

    def discard_downloads(self) -> None:
        """Delete the archives kept for releases that were probed or installed."""
        _remove_tree(self._downloads())

    def _archive(self, release: RedistRelease, name: str) -> Path:
        """Return the verified archive of component *name*, downloading it when needed."""
        archive = release.archives.get(name)
        if archive is None:
            raise ToolkitInstallError(f"CUDA {release.label} publishes no {name} archive")
        dest = self._downloads() / archive.file_name
        if dest.is_file() and _matches(dest, archive):
            return dest
        dest.parent.mkdir(parents=True, exist_ok=True)
        part = dest.with_name(dest.name + ".part")
        console.info(f"Downloading {archive.file_name} ...")
        try:
            self._download(archive.url, part)
            verify_sha256(part, archive.sha256)
            os.replace(part, dest)
        except OSError as error:
            raise ToolkitInstallError(f"{archive.url} could not be downloaded: "
                                      f"{error}") from error
        except DigestMismatchError as error:
            raise ToolkitInstallError(str(error)) from error
        finally:
            part.unlink(missing_ok=True)
        return dest

    def _unpack(self, archive: Path, root: Path) -> None:
        """Merge the archive's single top folder into *root*."""
        scratch = self._base() / ".unpack"
        _remove_tree(scratch)
        try:
            _extract(archive, _long_path(scratch))
            tops = [entry for entry in _long_path(scratch).iterdir() if entry.is_dir()]
            if len(tops) != 1:
                raise ToolkitInstallError(f"{archive.name} does not hold one top folder")
            shutil.copytree(tops[0], _long_path(root), symlinks=True, dirs_exist_ok=True)
        except (OSError, tarfile.TarError, zipfile.BadZipFile) as error:
            raise ToolkitInstallError(f"{archive.name} could not be unpacked: "
                                      f"{error}") from error
        finally:
            _remove_tree(scratch)

    def _base(self) -> Path:
        """Return the folder releases are installed under."""
        return self._target_dir or toolkits_dir()

    def _downloads(self) -> Path:
        """Return the folder archives are kept in until their release is installed."""
        return self._base() / "downloads"


def _matches(path: Path, archive: RedistArchive) -> bool:
    """Report whether the file at *path* has the archive's published digest."""
    try:
        verify_sha256(path, archive.sha256)
    except DigestMismatchError:
        return False
    return True


def _extract(archive: Path, dest: Path) -> None:
    """Unpack a ``.zip`` or ``.tar.xz`` archive into *dest*, refusing paths that leave it."""
    dest.mkdir(parents=True)
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.namelist():
                if not (dest / member).resolve().is_relative_to(dest.resolve()):
                    raise ToolkitInstallError(f"{archive.name} holds an unsafe path {member}")
            bundle.extractall(dest)
        return
    with tarfile.open(archive) as bundle:
        data_filter = getattr(tarfile, "data_filter", None)
        if data_filter is not None:
            bundle.extractall(dest, filter=data_filter)
            return
        for member in bundle.getmembers():
            if not (dest / member.name).resolve().is_relative_to(dest.resolve()):
                raise ToolkitInstallError(f"{archive.name} holds an unsafe path {member.name}")
        bundle.extractall(dest)


def _remove_tree(path: Path) -> None:
    """Delete the folder at *path* when it exists."""
    long_path = _long_path(path)
    if long_path.exists():
        shutil.rmtree(long_path)


def _long_path(path: Path) -> Path:
    """Return *path* in the Windows extended-length form, which lifts the 260-character limit
    that the deepest headers of a release cross under a long home folder; unchanged elsewhere."""
    if os.name != "nt":
        return path
    text = str(path.resolve())
    return Path(text if text.startswith(K_EXTENDED_PREFIX) else K_EXTENDED_PREFIX + text)


def _download(url: str, dest: Path) -> None:
    """Stream the body at *url* into *dest*."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=300) as response, open(dest, "wb") as handle:
        while chunk := response.read(1 << 20):
            handle.write(chunk)
