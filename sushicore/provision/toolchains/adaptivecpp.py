# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Builds AdaptiveCpp (acpp) from source, the secondary open-source SYCL toolchain."""

from __future__ import annotations

import glob as _glob
import os
import shutil
import subprocess
import tempfile
import typing
from pathlib import Path

from .. import home
from .._output import console
from ..packages import _download, _gh_tagged_asset, _run
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
#: Seconds to wait for consent before downloading the heavy LLVM (default: no).
_LLVM_CONSENT_TIMEOUT = 30
#: The answers that mean yes, in English and Turkish.
_YES = ("y", "yes", "e", "evet")


def _confirm_timeout(message: str, timeout: int = _LLVM_CONSENT_TIMEOUT,
                     default: bool = False) -> bool:
    """Ask a yes/no question, returning *default* if unanswered within *timeout*.

    Args:
        message: The question to print, as Rich markup.
        timeout: Seconds to wait for an answer before falling back to *default*.
        default: The answer used when the wait times out.

    Returns:
        True when the answer means yes.
    """
    import threading

    from rich.text import Text

    if console.is_machine():
        answer = console.prompt(Text.from_markup(message).plain,
                                "y" if default else "n")
        return answer.strip().lower() in _YES

    console.console.print(message)
    hint = r"\[y/n]" if default is False else r"\[Y/n]"
    console.console.print(
        f"[bold]Your choice {hint}[/bold] (auto-"
        f"{'yes' if default else 'no'} in {timeout}s): ", end="")
    result = [default]

    def _read() -> None:
        try:
            result[0] = input().strip().lower() in _YES
        except (EOFError, OSError):
            pass  # non-interactive: keep the default

    thread = threading.Thread(target=_read, daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        console.console.print()  # finish the prompt line
        console.info(f"No answer in {timeout}s — defaulting to "
                     f"{'yes' if default else 'no'}.")
    return result[0]


def _find_windows_sdk_rc_dir() -> str:
    """Return the directory containing rc.exe from the Windows 10/11 SDK, or ''."""
    for pat in [
        r"C:/Program Files (x86)/Windows Kits/10/bin/*/x64/rc.exe",
        r"C:/Program Files/Windows Kits/10/bin/*/x64/rc.exe",
    ]:
        hits = sorted(_glob.glob(pat))
        if hits:
            return str(Path(hits[-1]).parent)
    return ""


def _find_windows_llvm() -> tuple[str, str] | None:
    """Return ``(LLVM_DIR, clang_prefix)`` for an existing Windows LLVM, else None."""
    bases = [
        home.root() / "tools" / "llvm",
        Path(r"C:/Program Files/LLVM"),
        Path(r"C:/Program Files (x86)/LLVM"),
    ]
    for base in bases:
        cm = base / "lib" / "cmake" / "llvm"
        if cm.is_dir():
            return (str(cm), str(base))
    return None


def _vendor_llvm_windows() -> tuple[str, str] | None:
    """Download the official clang+llvm Windows tarball into the tools tree.

    Returns:
        ``(LLVM_DIR, clang_prefix)`` for the vendored install, or None on failure.
    """
    dest = home.root() / "tools" / "llvm"
    tag = f"llvmorg-{LLVM_WINDOWS_VERSION}"
    asset = f"LLVM-{LLVM_WINDOWS_VERSION}-win64.exe"
    try:
        url = _gh_tagged_asset("llvm/llvm-project", tag, asset)
    except Exception as exc:
        console.error(f"Could not resolve LLVM {LLVM_WINDOWS_VERSION} asset: {exc}")
        return None
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / asset
        try:
            console.info(f"Downloading LLVM {LLVM_WINDOWS_VERSION} (~1 GB) into {dest} ...")
            _download(url, archive)
            console.info("Installing LLVM silently (this takes a minute) ...")
            dest.mkdir(parents=True, exist_ok=True)
            # PowerShell triggers a UAC prompt via -Verb RunAs to install silently.
            ps_cmd = (
                f"Start-Process -FilePath '{archive}' "
                f"-ArgumentList '/S /D={dest.absolute()}' -Wait -Verb RunAs"
            )
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=True)
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
                        assume_yes: bool = False) -> str | None:
    """Build AdaptiveCpp from source; return the ``acpp`` executable path.

    Args:
        cfg: Resolved configuration; selects platform-specific paths and tools.
        mgr: The Linux distro package manager, or None off Linux.
        vcpkg: The vcpkg manager, or None when unavailable.
        dry_run: Report the action without touching the filesystem.
        assume_yes: Skip the Windows LLVM consent prompt.

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
    cmake = cfg.expand(cfg.cmake_exe) if cfg.cmake_exe else (shutil.which("cmake") or "")
    git = shutil.which("git") or ""
    if not git or not cmake:
        console.warn("AdaptiveCpp build needs git and cmake; skipping.")
        return None

    if dry_run:
        console.info(f"(dry-run) would build AdaptiveCpp {ACPP_VERSION} -> {prefix}")
        return str(acpp_exe)

    llvm_dir, clang_prefix = (
        _acpp_deps_windows(vcpkg, assume_yes=assume_yes)
        if cfg.is_windows else _acpp_deps_linux(mgr)
    )
    if llvm_dir is None:
        _explain_acpp_skip(cfg)
        return None

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "acpp"
        build = src / "build"
        clone = _run(
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
            rc_dir = _find_windows_sdk_rc_dir()
            if rc_dir and rc_dir.lower() not in os.environ.get("PATH", "").lower():
                os.environ["PATH"] = rc_dir + os.pathsep + os.environ.get("PATH", "")

        configure_ok = _run_quiet(cfg_cmd, dry_run)
        if not configure_ok:
            console.warn("AdaptiveCpp configure failed; skipping. "
                         "intel-llvm is installed and selected.")
            return None
        if _run([cmake, "--build", str(build), "--target", "install"],
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


def _acpp_deps_windows(vcpkg: "IPackageManager | None",
                       assume_yes: bool = False) -> tuple[str | None, str | None]:
    """Install acpp build deps on Windows; return ``(LLVM_DIR, clang_prefix)``.

    Args:
        vcpkg: The vcpkg manager, or None when unavailable.
        assume_yes: Skip the consent prompt for the heavy LLVM download.
    """
    if vcpkg is not None:
        vcpkg.install(["boost-context", "boost-fiber"], dry_run=False)

    existing = _find_windows_llvm()
    if existing:
        return existing

    # Consent is gathered by the caller before the progress spinner, never here.
    if not assume_yes:
        return (None, None)

    # Prefer winget when available; otherwise vendor the official tarball.
    if shutil.which("winget"):
        console.info("Installing LLVM via winget ...")
        subprocess.run(
            ["winget", "install", "--id", "LLVM.LLVM", "-e",
             "--accept-package-agreements", "--accept-source-agreements",
             "--silent"],
            check=False,
        )
        existing = _find_windows_llvm()
        if existing:
            return existing

    vendored = _vendor_llvm_windows()
    return vendored if vendored else (None, None)
