# adaptivecpp.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Builds AdaptiveCpp (acpp) from source, the secondary open-source SYCL toolchain."""

from __future__ import annotations

import glob as _glob
import os
import shutil
import subprocess
import tempfile
import typing
from pathlib import Path
from typing import Callable, MutableMapping, Sequence

from sushicore.errors import DigestMismatchError

from .. import home
from .._output import console
from ..download_verifier import verify_download
from ..packages import download, gh_tagged_asset
from ..process_run import run
from ._process import _run_quiet
from .stamp import toolchains_dir

if typing.TYPE_CHECKING:
    from ..config import ProvisionConfig
    from ..packages import IPackageManager

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
    for pat in [
        r"C:/Program Files (x86)/Windows Kits/10/bin/*/x64/rc.exe",
        r"C:/Program Files/Windows Kits/10/bin/*/x64/rc.exe",
    ]:
        hits = sorted((glob or _glob.glob)(pat))
        if hits:
            return str(Path(hits[-1]).parent)
    return ""


def llvm_missing(bases: Sequence[Path] | None = None) -> bool:
    """Report whether no Windows LLVM is found in *bases*; see :func:`_find_windows_llvm`."""
    return _find_windows_llvm(bases) is None


def _find_windows_llvm(bases: Sequence[Path] | None = None) -> tuple[str, str] | None:
    """Return ``(LLVM_DIR, clang_prefix)`` for an existing Windows LLVM, else None.

    Args:
        bases: The LLVM install roots to look in, first match wins; the vendored tree,
            then the two Program Files folders when omitted.
    """
    roots = bases if bases is not None else [
        home.root() / "tools" / "llvm",
        Path(r"C:/Program Files/LLVM"),
        Path(r"C:/Program Files (x86)/LLVM"),
    ]
    for base in roots:
        cm = base / "lib" / "cmake" / "llvm"
        if cm.is_dir():
            return (str(cm), str(base))
    return None


def _vendor_llvm_windows(*, resolve_asset: Callable[[str, str, str], str] | None = None,
                         fetch: Callable[[str, Path], None] | None = None,
                         launch: Callable[..., subprocess.CompletedProcess] | None = None,
                         ) -> tuple[str, str] | None:
    """Download the official clang+llvm Windows tarball into the tools tree.

    Args:
        resolve_asset: Maps a repository, a tag and an asset name to the asset URL.
        fetch: Downloads a URL into a file; the download transport.
        launch: Runs the installer command; takes the command and a ``check`` keyword.

    Returns:
        ``(LLVM_DIR, clang_prefix)`` for the vendored install, or None on failure.

    Raises:
        DigestMismatchError: The installer's SHA-256 is not the one its manifest entry pins.
    """
    dest = home.root() / "tools" / "llvm"
    tag = f"llvmorg-{LLVM_WINDOWS_VERSION}"
    asset = f"LLVM-{LLVM_WINDOWS_VERSION}-win64.exe"
    try:
        url = (resolve_asset or gh_tagged_asset)("llvm/llvm-project", tag, asset)
    except Exception as exc:
        console.error(f"Could not resolve LLVM {LLVM_WINDOWS_VERSION} asset: {exc}")
        return None
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / asset
        try:
            console.info(f"Downloading LLVM {LLVM_WINDOWS_VERSION} (~1 GB) into {dest} ...")
            (fetch or download)(url, archive)
            verify_download("adaptivecpp", archive)
            console.info("Installing LLVM silently (this takes a minute) ...")
            dest.mkdir(parents=True, exist_ok=True)
            # PowerShell triggers a UAC prompt via -Verb RunAs to install silently.
            ps_cmd = (
                f"Start-Process -FilePath '{archive}' "
                f"-ArgumentList '/S /D={dest.absolute()}' -Wait -Verb RunAs"
            )
            (launch or subprocess.run)(["powershell", "-NoProfile", "-Command", ps_cmd], check=True)
        except DigestMismatchError:
            raise
        except Exception as exc:
            console.error(f"LLVM vendor failed: {exc}")
            shutil.rmtree(dest, ignore_errors=True)
            return None
    found = _find_windows_llvm()
    if found:
        console.success(f"LLVM {LLVM_WINDOWS_VERSION} vendored into {dest}")
    else:
        console.error("LLVM extracted but lib/cmake/llvm is missing.")
    return found


def install_adaptivecpp(cfg: "ProvisionConfig", mgr: "IPackageManager | None",
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
    acpp = prefix / "bin" / ("acpp.bat" if cfg.is_windows else "acpp")
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

    llvm_dir, clang_prefix = (
        _acpp_deps_windows(vcpkg, assume_yes=assume_yes, winget=winget,
                           llvm_bases=llvm_bases)
        if cfg.is_windows else _acpp_deps_linux(mgr)
    )
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
            if cfg.is_windows:
                vcpkg_tc = home.root() / "vcpkg" / "scripts" / "buildsystems" / "vcpkg.cmake"
                if vcpkg_tc.is_file():
                    cfg_cmd.append(f"-DCMAKE_TOOLCHAIN_FILE={vcpkg_tc}")
        if cfg.ninja_exe:
            cfg_cmd.append(f"-DCMAKE_MAKE_PROGRAM={cfg.expand(cfg.ninja_exe)}")

        # clang-cl needs rc.exe (Windows SDK Resource Compiler) on PATH for the manifest embed.
        if cfg.is_windows:
            rc_dir = _find_windows_sdk_rc_dir(glob)
            if rc_dir and rc_dir.lower() not in env.get("PATH", "").lower():
                env["PATH"] = rc_dir + os.pathsep + env.get("PATH", "")

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
    if cfg.is_windows:
        console.info("Install it anytime with [cmd]sr setup acpp[/cmd] — "
                     f"that downloads LLVM {LLVM_WINDOWS_VERSION} (~2-3 GB) into the "
                     "deps folder and builds acpp, no prompt.")
        console.info("Note: the intel/llvm bundle cannot supply this LLVM — it ships "
                     "a compiler, not the LLVM cmake/dev files acpp needs.")
    else:
        console.info("To enable acpp on Linux, install the LLVM dev packages, e.g. "
                     "(Debian/Ubuntu): clang-17 llvm-17-dev libclang-17-dev "
                     "libboost-context-dev libboost-fiber-dev, then re-run "
                     "`sr setup --profile normal`.")
    console.info("This is non-fatal: intel-llvm is installed and selected, so you "
                 "can build and run now. acpp is the secondary toolchain.")


def _acpp_deps_linux(mgr: "IPackageManager | None") -> tuple[str | None, str | None]:
    """Install acpp build deps via the distro manager; return ``(LLVM_DIR, clang_prefix)``.

    Args:
        mgr: The Linux distro package manager, or None when unavailable.
    """
    if mgr is None:
        return (None, None)
    if mgr.name == "apt":
        pkgs = [
            f"clang-{ACPP_LLVM}", f"llvm-{ACPP_LLVM}-dev",
            f"libclang-{ACPP_LLVM}-dev", f"lld-{ACPP_LLVM}",
            "libboost-context-dev", "libboost-fiber-dev",
        ]
        mgr.install(pkgs, dry_run=False)
        llvm_dir = f"/usr/lib/llvm-{ACPP_LLVM}/lib/cmake/llvm"
        clang_prefix = f"/usr/lib/llvm-{ACPP_LLVM}"
        return (llvm_dir if Path(llvm_dir).is_dir() else None, clang_prefix)
    # Non-apt: install generic clang/llvm-dev/boost and let find_package resolve.
    mgr.install(mgr.translate_apt(
        ["clang", "llvm", "libboost-context-dev", "libboost-fiber-dev"]),
        dry_run=False)
    return ("", None)  # empty LLVM_DIR => cmake searches default locations


def _acpp_deps_windows(vcpkg: "IPackageManager | None", assume_yes: bool = False, *,
                       winget: "IPackageManager | None" = None,
                       llvm_bases: Sequence[Path] | None = None,
                       ) -> tuple[str | None, str | None]:
    """Install acpp build deps on Windows; return ``(LLVM_DIR, clang_prefix)``.

    Args:
        vcpkg: The vcpkg manager, or None when unavailable.
        assume_yes: Skip the consent prompt for the heavy LLVM download.
        winget: The winget manager, or None when unavailable.
        llvm_bases: The LLVM install roots to look in; see :func:`_find_windows_llvm`.
    """
    if vcpkg is not None:
        vcpkg.install(["boost-context", "boost-fiber"], dry_run=False)

    existing = _find_windows_llvm(llvm_bases)
    if existing:
        return existing

    # Consent is gathered by the caller before the progress spinner, never here.
    if not assume_yes:
        return (None, None)

    # Prefer winget when available; otherwise vendor the official tarball.
    if winget is not None and winget.available():
        console.info("Installing LLVM via winget ...")
        winget.install(["LLVM.LLVM"], dry_run=False)
        existing = _find_windows_llvm(llvm_bases)
        if existing:
            return existing

    vendored = _vendor_llvm_windows()
    return vendored if vendored else (None, None)
