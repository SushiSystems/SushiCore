# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Installs the intel/llvm nightly SYCL bundle (clang++ -fsycl)."""

from __future__ import annotations

import shutil
import tarfile
import tempfile
import typing
from pathlib import Path

from .._output import console
from ..packages import _download, _gh_latest_release_asset
from .stamp import (
    has_sanitizer_runtime, read_toolchain_stamp, toolchains_dir, write_toolchain_stamp)

if typing.TYPE_CHECKING:
    from ..config import ProvisionConfig

__all__ = ["install_intel_llvm"]


def install_intel_llvm(cfg: "ProvisionConfig", dry_run: bool,
                       refresh: bool = False) -> str | None:
    """Download and extract the intel/llvm SYCL bundle; return its root directory.

    Args:
        cfg: Resolved configuration; selects the platform's asset.
        dry_run: Report the action without touching the filesystem.
        refresh: Re-download over an existing install.

    Returns:
        The bundle root on success, None when it could not be installed.
    """
    root = toolchains_dir() / "llvm-sycl"
    clang = root / "bin" / ("clang++.exe" if cfg.is_windows else "clang++")
    asset = "sycl_windows.tar.gz" if cfg.is_windows else "sycl_linux.tar.gz"

    if clang.is_file() and not refresh:
        stamp = read_toolchain_stamp(root)
        known = stamp.get("tag") or "an unrecorded release"
        console.info(f"intel/llvm bundle already present ({known}): {root}")
        if not has_sanitizer_runtime(root):
            console.warn(
                "This bundle ships no compiler-rt sanitizer runtimes, so "
                "`sr build --type asan` cannot link. Current bundles do carry "
                "them — run [cmd]hub install --refresh-toolchains[/cmd] "
                "to replace it. (A newer bundle is the fix; a separate LLVM "
                "install is not.)")
        return str(root)

    if dry_run:
        verb = "would refresh" if clang.is_file() else "would download"
        console.info(f"(dry-run) {verb} intel/llvm '{asset}' at {root}")
        return str(root)

    try:
        # intel/llvm ships every SYCL build as a GitHub pre-release (nightly-*).
        tag, url = _gh_latest_release_asset("intel/llvm", asset)
    except Exception as exc:
        console.error(f"Could not resolve intel/llvm release asset: {exc}")
        return None

    if refresh and clang.is_file():
        current = read_toolchain_stamp(root).get("tag")
        if current == tag:
            console.info(f"intel/llvm bundle is already {tag}; nothing to refresh.")
            return str(root)
        console.info(f"Refreshing intel/llvm bundle: {current or 'unrecorded'} -> {tag}")

    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / asset
        try:
            console.info(f"Downloading intel/llvm SYCL bundle {tag} (~300-500 MB) ...")
            _download(url, archive)
            _extract_tar_gz(archive, root)
        except Exception as exc:
            console.error(f"intel/llvm bundle install failed: {exc}")
            # Only wipe a tree this call was creating; a refresh leaves the prior install intact.
            if not refresh:
                shutil.rmtree(root, ignore_errors=True)
            return None

    if clang.is_file():
        write_toolchain_stamp(root, "intel/llvm", tag)
        console.success(f"intel/llvm bundle installed ({tag}): {root}")
        if not has_sanitizer_runtime(root):
            console.warn("This bundle ships no compiler-rt sanitizer runtimes; "
                         "`sr build --type asan` will not link against it.")
        return str(root)
    console.error(f"intel/llvm bundle extracted but {clang.name} is missing.")
    return None


def _extract_tar_gz(archive: Path, dest: Path) -> None:
    """Extract *archive* into *dest*, collapsing a single top-level wrapper directory.

    Args:
        archive: A ``.tar.gz`` archive.
        dest: Directory to receive the archive's contents at its root.
    """
    dest.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as staging:
        stage = Path(staging)
        with tarfile.open(archive, "r:gz") as tf:
            try:
                tf.extractall(stage, filter="data")  # py3.12+: path-traversal safe
            except TypeError:
                tf.extractall(stage)  # older Python: no filter kwarg
        entries = list(stage.iterdir())
        srcroot = entries[0] if len(entries) == 1 and entries[0].is_dir() else stage
        for item in srcroot.iterdir():
            target = dest / item.name
            if target.exists():
                shutil.rmtree(target) if target.is_dir() else target.unlink()
            shutil.move(str(item), str(target))


def _extract_tarball(archive: Path, dest: Path) -> None:
    """Extract any tar archive into *dest*, autodetecting its compression.

    Args:
        archive: A tar archive of any compression tarfile can autodetect.
        dest: Directory to receive the archive's contents at its root.
    """
    dest.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as staging:
        stage = Path(staging)
        with tarfile.open(archive, "r:*") as tf:
            try:
                tf.extractall(stage, filter="data")
            except TypeError:
                tf.extractall(stage)
        entries = list(stage.iterdir())
        srcroot = entries[0] if len(entries) == 1 and entries[0].is_dir() else stage
        for item in srcroot.iterdir():
            target = dest / item.name
            if target.exists():
                shutil.rmtree(target) if target.is_dir() else target.unlink()
            shutil.move(str(item), str(target))
