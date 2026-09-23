# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Installs Intel oneAPI DPC++ (icx/icpx), the opt-in, heavy Windows toolchain."""

from __future__ import annotations

import subprocess
import typing
from pathlib import Path

from .._output import console

if typing.TYPE_CHECKING:
    from ..pipeline import InstallContext

__all__ = ["download_oneapi_installer", "install_oneapi", "run_oneapi_installer"]

#: Intel's offline Windows installer for the oneAPI base toolkit.
_ONEAPI_URL = (
    "https://registrationcenter-download.intel.com/akdlm/IRC_NAS/"
    "bae85ab1-cfcd-4251-8d42-a0c27949ea33/"
    "intel-oneapi-toolkit-2026.0.0.193_offline.exe"
)
#: WinError raised by ``subprocess.run`` when a launched process needs elevation.
_ELEVATION_REQUIRED = 740


def install_oneapi(ctx: "InstallContext") -> bool:
    """Download and silently install Intel oneAPI DPC++, when selected and needed.

    A no-op when oneAPI was not selected for this run, a SYCL compiler was
    already detected, or the run is a dry run.

    Args:
        ctx: The shared install context; reads ``selection.oneapi``, ``detected``
            and ``dry_run``.

    Returns:
        True on success or when nothing needed doing; False on failure.
    """
    if not (ctx.selection.oneapi and not ctx.detected.get("sycl_compiler", False)):
        return True
    if ctx.dry_run:
        console.info("(dry-run) skipping Intel oneAPI install.")
        return True

    installer = download_oneapi_installer()
    if installer is None:
        return False
    return run_oneapi_installer(installer)


def download_oneapi_installer() -> Path | None:
    """Download the Intel oneAPI offline installer into the user's home directory.

    Returns:
        The downloaded (or already-present) installer path, or None on failure.
    """
    installer = Path.home() / "intel-oneapi-toolkit-offline.exe"
    if installer.is_file():
        return installer
    console.info("Downloading Intel oneAPI Installer (~4 GB) from Intel servers ...")
    dl_rc = subprocess.run(["curl", "-L", "-o", str(installer), _ONEAPI_URL]).returncode
    if dl_rc != 0:
        console.error("Failed to download Intel oneAPI installer.")
        return None
    return installer


def run_oneapi_installer(installer: Path) -> bool:
    """Run the Intel oneAPI installer silently, elevating on demand.

    Args:
        installer: Path of the downloaded offline installer executable.

    Returns:
        True when the installer reports success.
    """
    oneapi_cmd = [
        str(installer), "-s", "-a", "--silent", "--eula", "accept",
        "-p=NEED_VS2022_INTEGRATION=1",
    ]
    with console.console.status(
        "[header]Installing Intel oneAPI Toolkit silently "
        "— this may take 10–20 minutes.",
        spinner="bouncingBar",
    ):
        try:
            rc = subprocess.run(oneapi_cmd).returncode
        except OSError as exc:
            if getattr(exc, "winerror", None) != _ELEVATION_REQUIRED:
                console.warn(f"Intel oneAPI installer failed to launch: {exc}")
                return False
            console.info(
                "Intel oneAPI requires administrator privileges. "
                "A UAC prompt will appear — approve it to continue."
            )
            try:
                ps_cmd = (
                    f"$p = Start-Process -FilePath '{str(installer)}'"
                    f" -ArgumentList '-s','-a','--silent','--eula','accept'"
                    f",'-p=NEED_VS2022_INTEGRATION=1'"
                    f" -Verb RunAs -Wait -PassThru; exit $p.ExitCode"
                )
                rc = subprocess.run(
                    ["powershell", "-Command", ps_cmd], timeout=1200,
                ).returncode
            except Exception as exc2:
                console.error(f"Elevated oneAPI launch failed: {exc2}")
                return False
    if rc != 0:
        console.warn("Intel oneAPI Toolkit installation failed.")
        return False
    console.success("Intel oneAPI Toolkit installed.")
    return True
