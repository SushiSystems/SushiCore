# windows.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The LLVM plan of the Windows target."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable, Sequence, final

from sushicore.errors import DigestMismatchError, SushiCoreError
from sushicore.proc import CommandRunner

from ..default_console import console_or_default
from .. import home
from ..download_verifier import verify_download
from ..llvm_plan import LLVM_PLANS, ILlvmPlan, LlvmRequest
from ..packages import downloader, gh_tagged_asset
from ..process_run import provision_runner
from ..target import K_WINDOWS
from ..toolchains.adaptivecpp import LLVM_WINDOWS_VERSION


def llvm_missing(bases: Sequence[Path] | None = None) -> bool:
    """Report whether no Windows LLVM is found in *bases*; see :func:`find_windows_llvm`."""
    return find_windows_llvm(bases) is None


def find_windows_llvm(bases: Sequence[Path] | None = None) -> tuple[str, str] | None:
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


class _LlvmInstallerError(SushiCoreError, RuntimeError):
    """The elevated LLVM installer ended with a non-zero exit code."""


def vendor_llvm_windows(*, console: Any = None,
                        resolve_asset: Callable[[str, str, str], str] | None = None,
                        fetch: Callable[[str, Path], None] | None = None,
                        runner: CommandRunner | None = None) -> tuple[str, str] | None:
    """Download the official clang+llvm Windows tarball into the tools tree.

    Args:
        console: The console the vendoring prints through.
        resolve_asset: Maps a repository, a tag and an asset name to the asset URL.
        fetch: Downloads a URL into a file; the download transport.
        runner: Runs the installer command; the provision runner on *console* when ``None``.

    Returns:
        ``(LLVM_DIR, clang_prefix)`` for the vendored install, or None on failure.

    Raises:
        DigestMismatchError: The installer's SHA-256 is not the one its manifest entry pins.
    """
    console = console_or_default(console, "vendor_llvm_windows")
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
            (fetch or downloader(console))(url, archive)
            verify_download("adaptivecpp", archive)
            console.info("Installing LLVM silently (this takes a minute) ...")
            dest.mkdir(parents=True, exist_ok=True)
            # PowerShell triggers a UAC prompt via -Verb RunAs to install silently.
            ps_cmd = (
                f"Start-Process -FilePath '{archive}' "
                f"-ArgumentList '/S /D={dest.absolute()}' -Wait -Verb RunAs"
            )
            code = (runner or provision_runner(console)).run_drained(
                ["powershell", "-NoProfile", "-Command", ps_cmd], None)
            if code != 0:
                raise _LlvmInstallerError(f"the LLVM installer exited with {code}")
        except DigestMismatchError:
            raise
        except Exception as exc:
            console.error(f"LLVM vendor failed: {exc}")
            shutil.rmtree(dest, ignore_errors=True)
            return None
    found = find_windows_llvm()
    if found:
        console.success(f"LLVM {LLVM_WINDOWS_VERSION} vendored into {dest}")
    else:
        console.error("LLVM extracted but lib/cmake/llvm is missing.")
    return found


@final
class WindowsLlvmPlan(ILlvmPlan):
    """Installs the boost ports through vcpkg and finds, installs or vendors the LLVM."""

    def resolve(self, request: LlvmRequest) -> tuple[str | None, str | None]:
        """Install acpp build deps on Windows; return ``(LLVM_DIR, clang_prefix)``."""
        if request.vcpkg is not None:
            request.vcpkg.install(["boost-context", "boost-fiber"], dry_run=False)

        existing = find_windows_llvm(request.llvm_bases)
        if existing:
            return existing

        # Consent is gathered by the caller before the progress spinner, never here.
        if not request.assume_yes:
            return (None, None)

        # Prefer winget when available; otherwise vendor the official tarball.
        winget = request.winget
        if winget is not None and winget.available():
            request.console.info("Installing LLVM via winget ...")
            winget.install(["LLVM.LLVM"], dry_run=False)
            existing = find_windows_llvm(request.llvm_bases)
            if existing:
                return existing

        vendored = vendor_llvm_windows(console=request.console)
        return vendored if vendored else (None, None)


LLVM_PLANS.register(K_WINDOWS, WindowsLlvmPlan())
