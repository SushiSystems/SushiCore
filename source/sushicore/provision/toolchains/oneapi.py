# oneapi.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Installs Intel oneAPI DPC++ (icx/icpx), the opt-in, heavy Windows toolchain."""

from __future__ import annotations

import typing
from pathlib import Path
from typing import Any, Callable

from sushicore.proc import CommandRunner

from ..download_verifier import verify_download
from ..install_location import ToolkitInstall
from ..licence_consent import Licence, LicenceConsent, is_accepted
from ..pipeline import InstallContext
from ..process_run import provision_runner
from .toolchain import ToolchainEnv

if typing.TYPE_CHECKING:
    from ..config import ProvisionConfig

__all__ = [
    "K_ONEAPI_LICENCE",
    "ONEAPI",
    "OneApiToolchain",
    "download_oneapi_installer",
    "install_oneapi",
    "oneapi_licences",
    "run_oneapi_installer",
]

#: The licence the oneAPI installer asks to accept.
K_ONEAPI_LICENCE = Licence(
    "Intel End User License Agreement for Developer Tools",
    "https://www.intel.com/content/www/us/en/developer/articles/license/end-user-license-agreement.html",
)

#: Intel's offline Windows installer for the oneAPI base toolkit.
_ONEAPI_URL = (
    "https://registrationcenter-download.intel.com/akdlm/IRC_NAS/"
    "bae85ab1-cfcd-4251-8d42-a0c27949ea33/"
    "intel-oneapi-toolkit-2026.0.0.193_offline.exe"
)
#: WinError raised when starting a process that needs elevation.
_ELEVATION_REQUIRED = 740


@typing.final
class OneApiToolchain:
    """Intel oneAPI DPC++, the opt-in heavy toolchain: an offline installer, or the distro's apt repository."""

    key = "oneapi"
    selection_field = "oneapi"

    def locate(self, cfg: "ProvisionConfig") -> ToolkitInstall | None:
        """Return the configured oneAPI root when it is a folder, or None."""
        root = cfg.expand(cfg.oneapi_root) if cfg.oneapi_root else ""
        if not (root and Path(root).is_dir()):
            return None
        return ToolkitInstall(root=Path(root), version=None)

    def licences(self, ctx: InstallContext) -> list[Licence]:
        """Return the EULA when the offline installer will run for *ctx*; empty otherwise."""
        return oneapi_licences(ctx)

    def install(self, ctx: InstallContext, env: ToolchainEnv) -> bool:
        """Install oneAPI through the distro manager when the run has one, else the offline installer.

        Returns:
            False only when the offline installer fails; a distro install that fails or is not
            automated warns and lets the run go on with the other toolchains.
        """
        if env.mgr is None:
            return env.install_oneapi(ctx)
        if not ctx.selection.oneapi:
            return True
        if env.mgr.automates_oneapi:
            env.console.info("oneAPI: configuring the Intel apt repository and installing "
                             "intel-oneapi-compiler-dpcpp-cpp.")
            if not env.mgr.install_oneapi(ctx.dry_run):
                env.console.warn("oneAPI compiler install failed; continuing "
                                 "(intel-llvm/AdaptiveCpp remain available).")
        else:
            env.console.warn(f"oneAPI on {env.mgr.name} is not automated; install the "
                             "Intel oneAPI DPC++ compiler manually.")
        return True


ONEAPI = OneApiToolchain()


def install_oneapi(ctx: "InstallContext", *, console: Any,
                   download_installer: Callable[[], Path | None] | None = None,
                   run_installer: Callable[[Path], bool] | None = None) -> bool:
    """Download and silently install Intel oneAPI DPC++, when selected and needed.

    A no-op when oneAPI was not selected for this run, a SYCL compiler was
    already detected, or the run is a dry run.

    Args:
        ctx: The shared install context; reads ``selection.oneapi``, ``detected``
            and ``dry_run``.
        console: The console the install prints through.
        download_installer: Fetches the offline installer and returns its path, or None on
            failure; :func:`download_oneapi_installer` when omitted.
        run_installer: Runs the installer at a path and reports success;
            :func:`run_oneapi_installer` with the run's consent when omitted.

    Returns:
        True on success or when nothing needed doing; False on failure.
    """
    if not oneapi_licences(ctx):
        return True
    if ctx.dry_run:
        console.info("(dry-run) skipping Intel oneAPI install.")
        return True

    installer = (download_installer or (lambda: download_oneapi_installer(console=console)))()
    if installer is None:
        return False
    run = run_installer or (
        lambda path: run_oneapi_installer(path, consent=ctx.consent, console=console))
    return run(installer)


def oneapi_licences(ctx: "InstallContext") -> list[Licence]:
    """Returns the licences :func:`install_oneapi` needs for *ctx*; empty when it installs nothing."""
    needed = ctx.selection.oneapi and not ctx.detected.get("sycl_compiler", False)
    return [K_ONEAPI_LICENCE] if needed else []


def download_oneapi_installer(*, console: Any, directory: Path | None = None,
                              runner: CommandRunner | None = None) -> Path | None:
    """Download the Intel oneAPI offline installer into the user's home directory.

    Args:
        console: The console the download prints through.
        directory: Where the installer is kept; the user's home directory when omitted.
        runner: Runs the curl command; the provision runner on *console* when ``None``.

    Returns:
        The downloaded (or already-present) installer path, or None on failure.

    Raises:
        DigestMismatchError: The installer's SHA-256 is not the one its manifest entry
            pins, whether it was downloaded now or left by an earlier run.
    """
    installer = (directory or Path.home()) / "intel-oneapi-toolkit-offline.exe"
    if not installer.is_file():
        console.info("Downloading Intel oneAPI Installer (~4 GB) from Intel servers ...")
        dl_rc = (runner or provision_runner(console)).run(
            ["curl", "-L", "-o", str(installer), _ONEAPI_URL], Path.cwd())
        if dl_rc != 0:
            console.error("Failed to download Intel oneAPI installer.")
            return None
    verify_download("oneapi", installer)
    return installer


def run_oneapi_installer(installer: Path, *, consent: LicenceConsent | None, console: Any,
                         runner: CommandRunner | None = None) -> bool:
    """Run the Intel oneAPI installer silently, elevating on demand.

    Args:
        installer: Path of the downloaded offline installer executable.
        consent: The run's licence consent; the installer launches only when it covers
            :data:`K_ONEAPI_LICENCE`.
        console: The console the install prints through.
        runner: Runs the installer, and the elevated PowerShell launch stopped after 1200
            seconds; the provision runner on *console* when ``None``.

    Returns:
        True when the installer reports success; False without consent to
        :data:`K_ONEAPI_LICENCE`, and nothing runs then.
    """
    if not is_accepted(consent, K_ONEAPI_LICENCE):
        console.error(f"Intel oneAPI needs consent to {K_ONEAPI_LICENCE.name}: "
                      f"{K_ONEAPI_LICENCE.link}")
        return False
    runner = runner or provision_runner(console)
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
            rc = runner.run(oneapi_cmd, Path.cwd())
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
                rc, _stdout, _stderr = runner.capture(
                    ["powershell", "-Command", ps_cmd], timeout=1200)
            except Exception as exc2:
                console.error(f"Elevated oneAPI launch failed: {exc2}")
                return False
    if rc != 0:
        console.warn("Intel oneAPI Toolkit installation failed.")
        return False
    console.success("Intel oneAPI Toolkit installed.")
    return True
