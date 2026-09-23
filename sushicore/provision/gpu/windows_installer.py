# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Download, elevated launch and machine-environment helpers for vendor Windows installers."""

from __future__ import annotations

import dataclasses
import hashlib
import http.client
import os
import subprocess
import typing
import urllib.request
from pathlib import Path

from .. import home
from .._output import console

#: Exit code reported when the user declines the UAC prompt (Win32 ERROR_CANCELLED).
ELEVATION_DECLINED = 1223

#: Exit code reported when PowerShell could not start the installer for any other reason.
LAUNCH_FAILED = 1

_MACHINE_ENVIRONMENT_KEY = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"

#: Errors a download, a digest or a rename can raise; none of them may escape a fetch.
_FETCH_ERRORS = (OSError, http.client.HTTPException, ValueError)


@dataclasses.dataclass(frozen=True)
class InstallerDownload:
    """One vendor installer file and the digest the vendor publishes for it.

    :param url: Where the vendor serves the installer.
    :param file_name: The name the file is stored under.
    :param md5: The lower-case MD5 hex digest the vendor publishes.
    """

    url: str
    file_name: str
    md5: str


@dataclasses.dataclass(frozen=True)
class ElevatedResult:
    """The outcome of one elevated run.

    :param code: The installer's exit code, or ELEVATION_DECLINED or LAUNCH_FAILED.
    :param message: The launch error PowerShell reported; empty when the installer ran.
    """

    code: int
    message: str = ""


def installers_dir() -> Path:
    """Return the folder under the dependencies tree that holds vendor installers."""
    return home.root() / "installers"


class Downloader(typing.Protocol):
    """Fetches an installer and proves it matches its published digest."""

    def fetch(self, download: InstallerDownload, dest_dir: Path) -> Path | None:
        """Return the verified local file, or None when the fetch or the check failed."""
        ...


class ElevatedRunner(typing.Protocol):
    """Runs an executable with administrator rights and waits for it."""

    def command(self, exe: Path, args: typing.Sequence[str]) -> list[str]:
        """Return the exact command line that would run *exe* elevated."""
        ...

    def run(self, exe: Path, args: typing.Sequence[str]) -> ElevatedResult:
        """Run *exe* elevated, wait, and return its outcome."""
        ...


class MachineEnvironment(typing.Protocol):
    """Reads a machine-wide environment variable as stored, not as inherited."""

    def read(self, name: str) -> str | None:
        """Return the variable's current machine value, or None when it is unset."""
        ...


def _md5_of(path: Path) -> str:
    """Return the lower-case MD5 hex digest of the file at *path*."""
    digest = hashlib.md5()
    with open(path, "rb") as fh:
        while chunk := fh.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


class HttpDownloader:
    """Downloads over HTTPS to a ``.part`` file and renames it only when its MD5 matches."""

    def fetch(self, download: InstallerDownload, dest_dir: Path) -> Path | None:
        """Reuse a verified copy in *dest_dir*, else download and verify a fresh one."""
        dest = dest_dir / download.file_name
        try:
            if self._reusable(dest, download):
                console.info(f"Using the verified {dest.name} already in {dest_dir}.")
                return dest
            return self._download(download, dest)
        except _FETCH_ERRORS as exc:
            console.warn(f"Download of {download.file_name} failed: {exc}")
            return None

    def _reusable(self, dest: Path, download: InstallerDownload) -> bool:
        """Return True for a copy whose MD5 matches; delete a copy whose MD5 does not."""
        if not dest.is_file():
            return False
        if _md5_of(dest) == download.md5:
            return True
        console.info(f"{dest.name} does not match its published MD5; downloading it again.")
        dest.unlink()
        return False

    def _download(self, download: InstallerDownload, dest: Path) -> Path | None:
        """Download to ``<file>.part``, verify it and rename it to *dest*."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        part = dest.with_name(dest.name + ".part")
        console.info(f"Downloading {download.url} ...")
        try:
            request = urllib.request.Request(download.url,
                                             headers={"User-Agent": "sushicore-installer"})
            with urllib.request.urlopen(request, timeout=300) as resp, open(part, "wb") as fh:
                while chunk := resp.read(1 << 16):
                    fh.write(chunk)
            actual = _md5_of(part)
            if actual != download.md5:
                console.warn(f"{download.file_name} has MD5 {actual}, expected "
                             f"{download.md5}; deleted it.")
                return None
            os.replace(part, dest)
            return dest
        finally:
            part.unlink(missing_ok=True)


def _ps_quote(text: str) -> str:
    """Quote *text* as a PowerShell single-quoted string literal."""
    return "'" + text.replace("'", "''") + "'"


class PowerShellElevatedRunner:
    """Starts a process through ``Start-Process -Verb RunAs``, showing one UAC prompt."""

    def command(self, exe: Path, args: typing.Sequence[str]) -> list[str]:
        """Return the PowerShell command line that runs *exe* elevated and exits with its code."""
        script = (
            f"try {{ $p = Start-Process -FilePath {_ps_quote(str(exe))} "
            f"-ArgumentList {_ps_quote(' '.join(args))} -Verb RunAs -Wait -PassThru "
            f"-ErrorAction Stop; exit $p.ExitCode }} "
            f"catch {{ $e = $_.Exception; while ($e) {{ "
            f"if ($e.NativeErrorCode -eq {ELEVATION_DECLINED}) {{ exit {ELEVATION_DECLINED} }}; "
            f"$e = $e.InnerException }}; "
            f"[Console]::Error.WriteLine($_.Exception.Message); exit {LAUNCH_FAILED} }}"
        )
        return ["powershell", "-NoProfile", "-NonInteractive", "-Command", script]

    def run(self, exe: Path, args: typing.Sequence[str]) -> ElevatedResult:
        """Run the elevated command and return its exit code and any launch error."""
        try:
            done = subprocess.run(self.command(exe, args), stderr=subprocess.PIPE, text=True)
        except OSError as exc:
            return ElevatedResult(LAUNCH_FAILED, str(exc))
        return ElevatedResult(done.returncode, (done.stderr or "").strip())


class RegistryMachineEnvironment:
    """Reads the machine environment block under HKLM, expanding embedded variables."""

    def read(self, name: str) -> str | None:
        """Return the expanded machine value of *name*, or None when absent or unreadable."""
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _MACHINE_ENVIRONMENT_KEY) as key:
                value, _kind = winreg.QueryValueEx(key, name)
        except (ImportError, OSError):
            return None
        return os.path.expandvars(str(value)) if value else None


def adopt_machine_variable(environment: MachineEnvironment, name: str) -> str | None:
    """Copy the machine value of *name* into this process and return it, or None when unset."""
    value = environment.read(name)
    if value:
        os.environ[name] = value
    return value


def prepend_machine_path(environment: MachineEnvironment) -> None:
    """Prepend the machine PATH entries this process's PATH does not already hold."""
    current = os.environ.get("PATH", "")
    known = {entry.lower() for entry in current.split(os.pathsep) if entry}
    fresh = [entry for entry in (environment.read("Path") or "").split(os.pathsep)
             if entry and entry.lower() not in known]
    if fresh:
        os.environ["PATH"] = os.pathsep.join([*fresh, current] if current else fresh)


@dataclasses.dataclass(frozen=True)
class WindowsInstallerTools:
    """The three helpers a Windows toolkit installer needs, injected as one bundle.

    :param downloader: Fetches and verifies the installer.
    :param runner: Runs the installer elevated.
    :param environment: Reads machine environment variables.
    :param dest_dir: Returns the folder the installer is stored in.
    """

    downloader: Downloader = dataclasses.field(default_factory=HttpDownloader)
    runner: ElevatedRunner = dataclasses.field(default_factory=PowerShellElevatedRunner)
    environment: MachineEnvironment = dataclasses.field(
        default_factory=RegistryMachineEnvironment)
    dest_dir: typing.Callable[[], Path] = installers_dir
