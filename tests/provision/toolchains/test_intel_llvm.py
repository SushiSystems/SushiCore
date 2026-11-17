# test_intel_llvm.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The intel/llvm installer reuses, refreshes, downloads and cleans up a bundle under the toolchains folder."""

from __future__ import annotations

import io
import tarfile
from pathlib import Path

import pytest

from sushicore.deps_fragment import Download
from sushicore.errors import ConfigError
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.toolchains import intel_llvm
from sushicore.provision.toolchains.stamp import (
    read_toolchain_stamp, toolchains_dir, write_toolchain_stamp)

pytestmark = pytest.mark.medium

_URL = "http://example.invalid/a"


class _Pinner:
    """Answers a pin lookup with a fixed tag and counts the lookups."""

    def __init__(self, tag: str = "nightly-2", error: Exception | None = None) -> None:
        """Answer *tag*, or raise *error* when one is given."""
        self._tag = tag
        self._error = error
        self.lookups = 0

    def __call__(self, name: str) -> Download:
        """Count the lookup and answer the pinned download."""
        self.lookups += 1
        if self._error is not None:
            raise self._error
        return Download(name, self._tag, _URL, "0" * 64)


class _Fetcher:
    """Writes a tar.gz of the named members as the download, or raises *error*; counts the downloads."""

    def __init__(self, members: tuple[str, ...] = (), error: Exception | None = None) -> None:
        """Download an archive holding *members*, or fail with *error*."""
        self._members = members
        self._error = error
        self.downloads = 0

    def __call__(self, url: str, dest: Path) -> None:
        """Count the download and write the archive to *dest*."""
        self.downloads += 1
        if self._error is not None:
            raise self._error
        with tarfile.open(dest, "w:gz") as archive:
            for name in self._members:
                info = tarfile.TarInfo(name=name)
                info.size = len(b"binary")
                archive.addfile(info, io.BytesIO(b"binary"))


def _linux_cfg() -> ProvisionSettings:
    """Build the configuration of a Linux host."""
    return ProvisionSettings(platform="linux")


def _install_clang(root: Path) -> None:
    """Put an empty compiler in the bundle folder, as an earlier install would have."""
    (root / "bin").mkdir(parents=True)
    (root / "bin" / "clang++").touch()


def test_install_intel_llvm_reuses_an_existing_bundle(provision_home, recording_console):
    """Check that an installed bundle is returned with a warning and no release lookup."""
    root = toolchains_dir() / "llvm-sycl"
    _install_clang(root)
    pinner = _Pinner()

    result = intel_llvm.install_intel_llvm(
        _linux_cfg(), dry_run=False, pin=pinner)

    assert result == str(root)
    assert pinner.lookups == 0
    assert recording_console.has_call("warn")  # no sanitizer runtime in the tree


def test_install_intel_llvm_dry_run_reports_without_downloading(provision_home, recording_console):
    """Check that a dry run names the bundle folder, downloads nothing and creates nothing."""
    root = toolchains_dir() / "llvm-sycl"
    fetcher = _Fetcher()

    result = intel_llvm.install_intel_llvm(_linux_cfg(), dry_run=True, fetch=fetcher)

    assert result == str(root)
    assert fetcher.downloads == 0
    assert not root.exists()
    assert recording_console.has_call("info")


def test_install_intel_llvm_refresh_skips_when_tag_unchanged(provision_home, recording_console):
    """Check that a refresh at the recorded tag downloads nothing."""
    root = toolchains_dir() / "llvm-sycl"
    _install_clang(root)
    write_toolchain_stamp(root, "intel/llvm", "nightly-1")
    fetcher = _Fetcher()

    result = intel_llvm.install_intel_llvm(
        _linux_cfg(), dry_run=False, refresh=True,
        pin=_Pinner("nightly-1"), fetch=fetcher)

    assert result == str(root)
    assert fetcher.downloads == 0


def test_install_intel_llvm_downloads_and_extracts_on_first_install(
        provision_home, recording_console):
    """Check that a first install extracts the bundle and records its tag."""
    root = toolchains_dir() / "llvm-sycl"

    result = intel_llvm.install_intel_llvm(
        _linux_cfg(), dry_run=False,
        pin=_Pinner("nightly-2"), fetch=_Fetcher(("bin/clang++", "lib/libsomething.so")))

    assert result == str(root)
    assert (root / "bin" / "clang++").is_file()
    assert read_toolchain_stamp(root)["tag"] == "nightly-2"


def test_install_intel_llvm_stops_when_no_fragment_pins_the_bundle(
        provision_home, recording_console):
    """Check that a missing pin reaches the caller as the error that names the entry."""
    with pytest.raises(ConfigError):
        intel_llvm.install_intel_llvm(
            _linux_cfg(), dry_run=False, pin=_Pinner(error=ConfigError("no pin 'intel-llvm'")))


def test_install_intel_llvm_cleans_up_on_download_failure_without_refresh(
        provision_home, recording_console):
    """Check that a failed first download removes the half-made bundle folder."""
    root = toolchains_dir() / "llvm-sycl"
    root.mkdir(parents=True)
    (root / "stray-file").touch()

    result = intel_llvm.install_intel_llvm(
        _linux_cfg(), dry_run=False,
        pin=_Pinner(), fetch=_Fetcher(error=OSError("network down")))

    assert result is None
    assert not root.exists()


def test_install_intel_llvm_collapses_a_single_top_level_wrapper_dir(
        provision_home, recording_console):
    """Check that an archive wrapped in one folder installs with its contents at the bundle root."""
    root = toolchains_dir() / "llvm-sycl"

    intel_llvm.install_intel_llvm(
        _linux_cfg(), dry_run=False,
        pin=_Pinner(), fetch=_Fetcher(("wrap/bin/clang++",)))

    assert (root / "bin" / "clang++").is_file()
    assert not (root / "wrap").exists()


def test_install_intel_llvm_leaves_an_unwrapped_layout_alone(provision_home, recording_console):
    """Check that an archive with several top-level folders installs them as they are."""
    root = toolchains_dir() / "llvm-sycl"

    intel_llvm.install_intel_llvm(
        _linux_cfg(), dry_run=False,
        pin=_Pinner(),
        fetch=_Fetcher(("bin/clang++", "lib/libsomething.so")))

    assert (root / "bin" / "clang++").is_file()
    assert (root / "lib" / "libsomething.so").is_file()
