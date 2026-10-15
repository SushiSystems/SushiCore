# rocm_toolkit_installer.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Installs a ROCm SDK tarball into a folder the user owns, with no package manager and no
root rights. The tarball's top level is the ROCm root itself; releases sit side by side under
``<home>/rocm/<release>-<family>``.
"""

from __future__ import annotations

import os
import shutil
import tarfile
import typing
import urllib.request
from pathlib import Path

from .. import home
from .._output import console
from ..system import USER_AGENT
from .rocm_package import RocmPackage
from .toolkit_vendor import ToolkitSourceError

#: A header every ROCm root carries, used to recognise one.
K_HIP_RUNTIME_HEADER = Path("include") / "hip" / "hip_runtime.h"


class RocmInstallError(ToolkitSourceError):
    """A tarball could not be downloaded or unpacked."""


def is_rocm_root(root: Path) -> bool:
    """Report whether *root* holds a ROCm install."""
    return (root / K_HIP_RUNTIME_HEADER).is_file()


@typing.final
class RocmTarballInstaller:
    """Downloads and unpacks ROCm SDK tarballs under one folder.

    AMD publishes no digest for these tarballs, so a download is trusted on HTTPS alone; the
    gap is recorded in docs/reference/KNOWN_ISSUES.md.

    Args:
        target_dir: The folder releases are installed under; ``<home>/rocm`` when None.
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
        return self._target_dir or home.root() / "rocm"

    def root_of(self, label: str) -> Path:
        """Return where the release labelled *label* is, or would be, installed."""
        return self.base_dir / label

    def is_installed(self, label: str) -> bool:
        """Report whether the release was unpacked to the end."""
        return is_rocm_root(self.root_of(label))

    def install(self, package: RocmPackage) -> Path:
        """Install *package* and return its root; an installed release is returned as is.

        Raises:
            RocmInstallError: The tarball could not be downloaded or unpacked.
        """
        root = self.root_of(package.label)
        if self.is_installed(package.label):
            return root
        archive = self._fetch(package)
        staging = self.base_dir / f".{package.label}"
        _remove_tree(staging)
        try:
            _extract(archive, staging)
        except (OSError, tarfile.TarError) as error:
            _remove_tree(staging)
            raise RocmInstallError(f"{archive.name} could not be unpacked: {error}") from error
        if not is_rocm_root(staging):
            _remove_tree(staging)
            raise RocmInstallError(f"{archive.name} holds no {K_HIP_RUNTIME_HEADER}")
        _remove_tree(root)
        os.replace(staging, root)
        self.discard_downloads()
        return root

    def discard_downloads(self) -> None:
        """Delete tarballs kept from an install that did not finish."""
        _remove_tree(self.base_dir / "downloads")

    def _fetch(self, package: RocmPackage) -> Path:
        """Download the tarball, resuming nothing: a partial file is fetched again."""
        dest = self.base_dir / "downloads" / package.url.rsplit("/", 1)[-1]
        if dest.is_file():
            return dest
        dest.parent.mkdir(parents=True, exist_ok=True)
        part = dest.with_name(dest.name + ".part")
        console.info(f"Downloading {dest.name}; ROCm SDK tarballs are several gigabytes ...")
        try:
            self._download(package.url, part)
            os.replace(part, dest)
        except OSError as error:
            raise RocmInstallError(f"{package.url} could not be downloaded: {error}") from error
        finally:
            part.unlink(missing_ok=True)
        return dest


def _extract(archive: Path, dest: Path) -> None:
    """Unpack a ``.tar.gz`` into *dest*, refusing members that leave it."""
    dest.mkdir(parents=True)
    with tarfile.open(archive) as bundle:
        data_filter = getattr(tarfile, "data_filter", None)
        if data_filter is not None:
            bundle.extractall(dest, filter=data_filter)
            return
        for member in bundle.getmembers():
            if not (dest / member.name).resolve().is_relative_to(dest.resolve()):
                raise RocmInstallError(f"{archive.name} holds an unsafe path {member.name}")
        bundle.extractall(dest)


def _remove_tree(path: Path) -> None:
    """Delete the folder at *path* when it exists."""
    if path.exists():
        shutil.rmtree(path)


def _download(url: str, dest: Path) -> None:
    """Stream the body at *url* into *dest*."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=300) as response, open(dest, "wb") as handle:
        while chunk := response.read(1 << 20):
            handle.write(chunk)
