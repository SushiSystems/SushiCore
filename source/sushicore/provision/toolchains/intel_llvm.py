# intel_llvm.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Installs the intel/llvm nightly SYCL bundle (clang++ -fsycl)."""

from __future__ import annotations

import shutil
import tarfile
import tempfile
import typing
from pathlib import Path
from typing import Callable

from sushicore.deps_fragment import Download
from sushicore.errors import ConfigError, DigestMismatchError

from .._output import console
from ..download_verifier import pinned_download, verify_download
from ..packages import download
from .stamp import (
    has_sanitizer_runtime, read_toolchain_stamp, toolchains_dir, write_toolchain_stamp)

if typing.TYPE_CHECKING:
    from ..config import ProvisionConfig

__all__ = ["install_intel_llvm"]


def install_intel_llvm(cfg: "ProvisionConfig", dry_run: bool,
                       refresh: bool = False, refresh_command: str = "", *,
                       pin: Callable[[str], Download] | None = None,
                       fetch: Callable[[str, Path], None] | None = None) -> str | None:
    """Download and extract the intel/llvm SYCL bundle; return its root directory.

    Args:
        cfg: Resolved configuration; selects the platform's asset.
        dry_run: Report the action without touching the filesystem.
        refresh: Re-download over an existing install.
        refresh_command: The command the consumer offers for a refresh; named in the note about a stale bundle.
        pin: Maps an entry name to its pinned download; the bound verifier's when ``None``.
        fetch: Downloads a URL into a file; the download transport.

    Returns:
        The bundle root on success, None when it could not be installed.

    Raises:
        DigestMismatchError: The bundle's SHA-256 is not the one its manifest entry pins.
        ConfigError: No fragment pins the ``intel-llvm`` download for this platform.
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
                "a sanitizer build cannot link. Current bundles do carry "
                f"them — run [cmd]{refresh_command or 'setup with the refresh option'}[/cmd] "
                "to replace it. (A newer bundle is the fix; a separate LLVM "
                "install is not.)")
        return str(root)

    if dry_run:
        verb = "would refresh" if clang.is_file() else "would download"
        console.info(f"(dry-run) {verb} intel/llvm '{asset}' at {root}")
        return str(root)

    pinned = (pin or pinned_download)("intel-llvm")
    tag, url = pinned.version, pinned.url

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
            (fetch or download)(url, archive)
            verify_download("intel-llvm", archive)
            _extract_tar_gz(archive, root)
        except (DigestMismatchError, ConfigError):
            raise
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
