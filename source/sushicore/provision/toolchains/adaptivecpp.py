# adaptivecpp.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Builds AdaptiveCpp (acpp) from source, the secondary open-source SYCL toolchain."""

from __future__ import annotations

import glob as _glob
import os
import shutil
import tempfile
import typing
from pathlib import Path
from typing import Callable, MutableMapping, Sequence


from .. import home
from ..probe import K_RC_GLOBS
from .._output import console
from ..process_run import run
from ..llvm_plan import LLVM_PLANS, LlvmRequest
from ..target import target_of
from ._process import _run_quiet
from .stamp import toolchains_dir

if typing.TYPE_CHECKING:
    from ..config import ProvisionConfig
    from ..packages import IPackageManager, LinuxPackageManager

__all__ = ["install_adaptivecpp"]

#: AdaptiveCpp release built from source.
ACPP_VERSION = "v24.10.0"
#: clang/llvm major version used to build acpp.
ACPP_LLVM = "17"
#: Full LLVM release vendored on Windows when no LLVM dev install exists.
LLVM_WINDOWS_VERSION = "17.0.6"


def _find_windows_sdk_rc_dir(glob: Callable[[str], list[str]] | None = None) -> str:
    """Return the directory containing rc.exe from the Windows 10/11 SDK, or ''.

    Args:
        glob: Expands a glob pattern into the matching paths; ``glob.glob`` when omitted.
    """
    for pat in K_RC_GLOBS:
        hits = sorted((glob or _glob.glob)(pat))
        if hits:
            return str(Path(hits[-1]).parent)
    return ""


def install_adaptivecpp(cfg: "ProvisionConfig", mgr: "LinuxPackageManager | None",
                        vcpkg: "IPackageManager | None", dry_run: bool,
                        assume_yes: bool = False, *,
                        winget: "IPackageManager | None" = None,
                        which: Callable[[str], str | None] | None = None,
                        glob: Callable[[str], list[str]] | None = None,
                        llvm_bases: Sequence[Path] | None = None,
                        environ: MutableMapping[str, str] | None = None,
                        run_command: Callable[..., int] | None = None,
                        configure: Callable[[list[str], bool], bool] | None = None,
                        ) -> str | None:
    """Build AdaptiveCpp from source; return the ``acpp`` executable path.

    Args:
        cfg: Resolved configuration; selects platform-specific paths and tools.
        mgr: The Linux distro package manager, or None off Linux.
        vcpkg: The vcpkg manager, or None when unavailable.
        dry_run: Report the action without touching the filesystem.
        assume_yes: Skip the Windows LLVM consent prompt.
        winget: The winget manager, or None when unavailable; it installs LLVM only when it holds
            the user's consent to winget's agreements.
        which: Finds an executable on the search path; ``shutil.which`` when omitted.
        glob: Expands a glob pattern when the Windows SDK is looked up; ``glob.glob`` when omitted.
        llvm_bases: The Windows LLVM install roots to look in; see :func:`_find_windows_llvm`.
        environ: The environment whose ``PATH`` gains the SDK resource compiler's folder;
            ``os.environ`` when omitted.
        run_command: Runs a command and returns its exit code; takes the command, the dry-run
            flag and a ``check`` keyword. ``process_run.run`` when omitted.
        configure: Runs the configure command quietly and reports success; takes the command
            and the dry-run flag. The quiet subprocess runner when omitted.

    Returns:
        The ``acpp`` executable path on success, None when it could not be built.
    """
    prefix = toolchains_dir() / "adaptivecpp"
    target = target_of(cfg)
    acpp = prefix / "bin" / target.acpp_launcher
    acpp_exe = prefix / "bin" / "acpp"
    for cand in (acpp, acpp_exe):
        if cand.is_file():
            console.info(f"AdaptiveCpp already present: {prefix}")
            return str(cand)

    # cmake/git may be off PATH (e.g. scoop), so honour the configured paths.
    find = which or shutil.which
    env = environ if environ is not None else os.environ
    cmake = cfg.expand(cfg.cmake_exe) if cfg.cmake_exe else (find("cmake") or "")
    git = find("git") or ""
    if not git or not cmake:
        console.warn("AdaptiveCpp build needs git and cmake; skipping.")
        return None

    if dry_run:
        console.info(f"(dry-run) would build AdaptiveCpp {ACPP_VERSION} -> {prefix}")
        return str(acpp_exe)

    llvm_dir, clang_prefix = LLVM_PLANS.plan_for(target).resolve(
        LlvmRequest(mgr=mgr, vcpkg=vcpkg, winget=winget, assume_yes=assume_yes,
                    llvm_bases=llvm_bases))
    if llvm_dir is None:
        _explain_acpp_skip(cfg)
        return None

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "acpp"
        build = src / "build"
        clone = (run_command or run)(
            [git, "clone", "--depth", "1", "--branch", ACPP_VERSION,
             "https://github.com/AdaptiveCpp/AdaptiveCpp.git", str(src)],
            dry_run, check=True,
        )
        if clone != 0:
            console.warn("AdaptiveCpp clone failed; skipping.")
            return None

        cfg_cmd = [
            cmake, "-S", str(src), "-B", str(build), "-G", "Ninja",
            "-DCMAKE_BUILD_TYPE=Release",
            f"-DCMAKE_INSTALL_PREFIX={prefix}",
            f"-DLLVM_DIR={llvm_dir}",
            "-DCMAKE_POLICY_VERSION_MINIMUM=3.5",
        ]
        if clang_prefix:
            cfg_cmd.append(f"-DCLANG_INSTALL_PREFIX={clang_prefix}")
            cfg_cmd.extend(target.acpp_configure_args(
                home.root() / "vcpkg" / "scripts" / "buildsystems" / "vcpkg.cmake"))
        if cfg.ninja_exe:
            cfg_cmd.append(f"-DCMAKE_MAKE_PROGRAM={cfg.expand(cfg.ninja_exe)}")

        # clang-cl needs rc.exe (Windows SDK Resource Compiler) on PATH for the manifest embed.
        target.prepare_acpp_environment(env, lambda: _find_windows_sdk_rc_dir(glob))

        configure_ok = (configure or _run_quiet)(cfg_cmd, dry_run)
        if not configure_ok:
            console.warn("AdaptiveCpp configure failed; skipping. "
                         "intel-llvm is installed and selected.")
            return None
        if (run_command or run)([cmake, "--build", str(build), "--target", "install"],
                dry_run, check=True) != 0:
            console.warn("AdaptiveCpp build failed; skipping. "
                         "intel-llvm is installed and selected.")
            return None

    result = next((c for c in (acpp, acpp_exe) if c.is_file()), None)
    if result:
        console.success(f"AdaptiveCpp installed: {prefix}")
        return str(result)
    console.warn("AdaptiveCpp build completed but acpp binary not found.")
    return None


def _explain_acpp_skip(cfg: "ProvisionConfig") -> None:
    """Explain why the acpp build was skipped and how to enable it later.

    Args:
        cfg: Resolved configuration; selects the platform-specific message.
    """
    console.warn("AdaptiveCpp (acpp) was skipped — it builds from source and its "
                 "LLVM development dependency is not available.")
    for note in target_of(cfg).acpp_skip_notes(LLVM_WINDOWS_VERSION):
        console.info(note)
    console.info("This is non-fatal: intel-llvm is installed and selected, so you "
                 "can build and run now. acpp is the secondary toolchain.")
