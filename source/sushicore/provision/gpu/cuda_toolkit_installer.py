# cuda_toolkit_installer.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Installs a CUDA release from NVIDIA's redistributable archives into a folder the user owns.

No installer runs and nothing needs administrator rights: each component archive is
downloaded, checked against the SHA-256 NVIDIA publishes, and merged into one toolkit root
laid out like a full CUDA install. Releases sit side by side under ``<home>/cuda/<version>``.
"""

from __future__ import annotations

import os
import shutil
import tarfile
import typing
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

from sushicore.errors import DigestMismatchError
from sushicore.proc import CommandRunner

from .. import home
from ..host import current_host
from ..integrity import verify_sha256
from ..licence_consent import Licence
from ...quiet_runner import quiet_runner
from ..system import USER_AGENT
from .cuda_release import RedistArchive, RedistRelease
from .toolkit_vendor import ToolkitSourceError

#: The components the SYCL toolchain and the Unified Runtime adapter build need.
K_REQUIRED_COMPONENTS = ("cuda_nvcc", "cuda_cudart", "cuda_nvml_dev")

#: Parts of the compiler that some releases publish on their own; installed when published.
K_COMPANION_COMPONENTS = ("cuda_crt", "libnvvm", "cuda_cccl")

#: The licence NVIDIA ships the CUDA redistributable archives under.
K_CUDA_LICENCE = Licence(
    "NVIDIA CUDA Toolkit End User License Agreement",
    "https://docs.nvidia.com/cuda/eula/index.html",
)

class ToolkitInstallError(ToolkitSourceError):
    """A release could not be downloaded, verified or unpacked."""


def toolkits_dir() -> Path:
    """Return ``<home>/cuda``, the folder every installed release lives under."""
    return home.root() / "cuda"


def nvcc_in(root: Path) -> Path:
    """Return the nvcc binary of the toolkit rooted at *root*."""
    return root / "bin" / current_host().nvcc_name


def list_gpu_architectures(nvcc: Path, *, runner: CommandRunner | None = None) -> frozenset[str]:
    """Return the architectures *nvcc* builds for, without the ``compute_`` prefix.

    Args:
        nvcc: The compiler to ask.
        runner: Runs the command; the quiet runner when ``None``.

    Raises:
        ToolkitInstallError: nvcc did not run or exited non-zero.
    """
    code, out, err = (runner or quiet_runner()).capture([str(nvcc), "--list-gpu-arch"],
                                                            timeout=60)
    if code != 0:
        raise ToolkitInstallError(f"{nvcc} --list-gpu-arch failed (exit {code}): {err.strip()}")
    return frozenset(line.strip()[len("compute_"):] for line in out.splitlines()
                     if line.strip().startswith("compute_"))


@typing.final
class RedistToolkitInstaller:
    """Downloads, verifies and unpacks CUDA releases under one folder.

    Args:
        target_dir: The folder releases are installed under; defaults to :func:`toolkits_dir`.
        download: Writes the body at a URL to a path; raises ``OSError`` on failure.
        list_architectures: Asks an unpacked nvcc for its architectures; defaults to
            :func:`list_gpu_architectures`.
    """

    def __init__(self, target_dir: Path | None = None,
                 download: typing.Callable[[str, Path], None] | None = None,
                 list_architectures: typing.Callable[[Path], frozenset[str]] | None = None,
                 ) -> None:
        """Store the target folder, the download function and the architecture query."""
        self._target_dir = target_dir
        self._download = download or _download
        self._list_architectures = list_architectures or list_gpu_architectures

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

    def probe_architectures(self, release: RedistRelease, console: typing.Any) -> frozenset[str]:
        """Return the architectures the release's compiler builds for, unpacking only nvcc.

        Args:
            console: The console a download is announced on.

        Raises:
            ToolkitInstallError: The compiler archive is missing, mismatching or does not run.
        """
        if self.is_installed(release.label):
            return self._list_architectures(nvcc_in(self.root_of(release.label)))
        probe_root = self._base() / f".{release.label}-probe"
        _remove_tree(probe_root)
        try:
            self._unpack(self._archive(release, "cuda_nvcc", console), probe_root)
            return self._list_architectures(nvcc_in(probe_root))
        finally:
            _remove_tree(probe_root)

    def install(self, release: RedistRelease, console: typing.Any) -> Path:
        """Install *release* and return its root; an installed release is returned as is.

        The caller holds the user's consent to :data:`K_CUDA_LICENCE`.

        Args:
            console: The console a download is announced on.

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
            self._unpack(self._archive(release, name, console), staging)
        _remove_tree(root)
        os.replace(_long_path(staging), _long_path(root))
        self.discard_downloads()
        return root

    def discard_downloads(self) -> None:
        """Delete the archives kept for releases that were probed or installed."""
        _remove_tree(self._downloads())

    def _archive(self, release: RedistRelease, name: str, console: typing.Any) -> Path:
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
                parts = PurePosixPath(member.replace("\\", "/")).parts
                if member.startswith(("/", "\\")) or ":" in member or ".." in parts:
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
    """Return *path* in the host's long-path form, which lifts the 260-character limit
    that the deepest headers of a release cross under a long home folder on Windows."""
    return current_host().long_path(path)


def _download(url: str, dest: Path) -> None:
    """Stream the body at *url* into *dest*."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=300) as response, open(dest, "wb") as handle:
        while chunk := response.read(1 << 20):
            handle.write(chunk)
