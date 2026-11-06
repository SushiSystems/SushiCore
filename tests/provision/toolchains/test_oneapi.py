# test_oneapi.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The oneAPI installer installs when selected and needed, and reports each way it can fail."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from sushicore.provision.config import ProvisionSettings
from sushicore.provision.pipeline import InstallContext, ToolchainSelection
from sushicore.provision.toolchains import oneapi

#: ``ERROR_ELEVATION_REQUIRED``, the WinError a launch raises when the program needs elevation.
K_ELEVATION_REQUIRED = 740


class _Launcher:
    """Answers each launch with the next scripted outcome and records the command it was given.

    An outcome that is an exception is raised; an integer is the exit code of the completed process.
    """

    def __init__(self, *outcomes: int | Exception) -> None:
        """Script the outcomes, in call order."""
        self._outcomes = list(outcomes)
        self.commands: list[list[str]] = []

    def __call__(self, cmd: list[str], **_options: object) -> subprocess.CompletedProcess:
        """Record *cmd* and play the next outcome."""
        self.commands.append(cmd)
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return subprocess.CompletedProcess(cmd, outcome)


def _needs_elevation() -> OSError:
    """Build the error a launch raises when the program needs elevation."""
    error = OSError("needs elevation")
    error.winerror = K_ELEVATION_REQUIRED
    return error


def _ctx(oneapi_selected: bool, dry_run: bool = False, detected: dict | None = None
         ) -> InstallContext:
    """Build the install context of a run."""
    return InstallContext(
        cfg=ProvisionSettings(),
        selection=ToolchainSelection(oneapi=oneapi_selected),
        dry_run=dry_run,
        detected=detected or {},
    )


@pytest.mark.small
def test_install_oneapi_noop_when_not_selected(recording_console):
    """Check that nothing is downloaded or printed when oneAPI was not selected."""
    assert oneapi.install_oneapi(_ctx(oneapi_selected=False)) is True
    assert recording_console.calls == []


@pytest.mark.small
def test_install_oneapi_noop_when_a_sycl_compiler_is_already_detected(recording_console):
    """Check that nothing is downloaded or printed when a SYCL compiler is already detected."""
    ctx = _ctx(oneapi_selected=True, detected={"sycl_compiler": True})

    assert oneapi.install_oneapi(ctx) is True
    assert recording_console.calls == []


@pytest.mark.small
def test_install_oneapi_dry_run_skips_the_download(recording_console):
    """Check that a dry run reports the skip and fetches nothing."""
    fetched: list[str] = []
    ctx = _ctx(oneapi_selected=True, dry_run=True)

    assert oneapi.install_oneapi(ctx, download_installer=lambda: fetched.append("x")) is True
    assert fetched == []
    assert recording_console.texts("info") == ["(dry-run) skipping Intel oneAPI install."]


@pytest.mark.small
def test_install_oneapi_fails_when_the_download_fails(recording_console):
    """Check that a failed download fails the install and runs no installer."""
    ran: list[Path] = []

    result = oneapi.install_oneapi(
        _ctx(oneapi_selected=True),
        download_installer=lambda: None,
        run_installer=lambda installer: ran.append(installer) or True)

    assert result is False
    assert ran == []


@pytest.mark.small
def test_install_oneapi_runs_the_installer_after_a_successful_download(recording_console):
    """Check that the downloaded installer is the one that runs."""
    ran: list[Path] = []

    result = oneapi.install_oneapi(
        _ctx(oneapi_selected=True),
        download_installer=lambda: Path("fake.exe"),
        run_installer=lambda installer: ran.append(installer) or True)

    assert result is True
    assert ran == [Path("fake.exe")]


@pytest.mark.medium
def test_download_oneapi_installer_reuses_an_existing_file(tmp_path, recording_console):
    """Check that an installer already on disk is returned without a download."""
    existing = tmp_path / "intel-oneapi-toolkit-offline.exe"
    existing.touch()
    launcher = _Launcher()

    result = oneapi.download_oneapi_installer(directory=tmp_path, launch=launcher)

    assert result == existing
    assert launcher.commands == []


@pytest.mark.medium
def test_download_oneapi_installer_downloads_with_curl(tmp_path, recording_console):
    """Check that a missing installer is fetched with curl into the directory."""
    launcher = _Launcher(0)

    result = oneapi.download_oneapi_installer(directory=tmp_path, launch=launcher)

    assert result == tmp_path / "intel-oneapi-toolkit-offline.exe"
    assert launcher.commands[0][0] == "curl"
    assert str(result) in launcher.commands[0]


@pytest.mark.medium
def test_download_oneapi_installer_returns_none_on_curl_failure(tmp_path, recording_console):
    """Check that a curl failure returns None and reports an error."""
    result = oneapi.download_oneapi_installer(directory=tmp_path, launch=_Launcher(1))

    assert result is None
    assert recording_console.texts("error") == ["Failed to download Intel oneAPI installer."]


@pytest.mark.small
def test_run_oneapi_installer_reports_success(recording_console):
    """Check that a zero exit code reports success."""
    assert oneapi.run_oneapi_installer(Path("installer.exe"), launch=_Launcher(0)) is True
    assert recording_console.texts("success") == ["Intel oneAPI Toolkit installed."]


@pytest.mark.small
def test_run_oneapi_installer_reports_failure(recording_console):
    """Check that a non-zero exit code reports failure."""
    assert oneapi.run_oneapi_installer(Path("installer.exe"), launch=_Launcher(1)) is False
    assert recording_console.texts("warn") == ["Intel oneAPI Toolkit installation failed."]


@pytest.mark.small
def test_run_oneapi_installer_elevates_on_uac_required(recording_console):
    """Check that a launch that needs elevation is retried through PowerShell."""
    launcher = _Launcher(_needs_elevation(), 0)

    result = oneapi.run_oneapi_installer(Path("installer.exe"), launch=launcher)

    assert result is True
    assert [cmd[0] for cmd in launcher.commands] == ["installer.exe", "powershell"]


@pytest.mark.small
def test_run_oneapi_installer_reports_a_non_elevation_launch_failure(recording_console):
    """Check that a launch error other than elevation fails with a warning and no retry."""
    launcher = _Launcher(OSError("no such file"))

    result = oneapi.run_oneapi_installer(Path("installer.exe"), launch=launcher)

    assert result is False
    assert len(launcher.commands) == 1
    assert recording_console.texts("warn") == [
        "Intel oneAPI installer failed to launch: no such file"]


@pytest.mark.small
def test_run_oneapi_installer_reports_an_elevated_launch_exception(recording_console):
    """Check that a failure of the elevated launch fails with an error."""
    launcher = _Launcher(_needs_elevation(), RuntimeError("powershell missing"))

    result = oneapi.run_oneapi_installer(Path("installer.exe"), launch=launcher)

    assert result is False
    assert recording_console.texts("error") == [
        "Elevated oneAPI launch failed: powershell missing"]
