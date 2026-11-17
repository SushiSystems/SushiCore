# vs_locator.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Finds the Visual Studio C++ tools script, through vswhere and then a scan of the disk."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Callable, Sequence

from sushicore.proc import CommandRunner, did_not_run
from sushicore.provision.host import IHost, current_host
from sushicore.quiet_runner import quiet_runner

_log = logging.getLogger(__name__)

_VS_EDITIONS = ("BuildTools", "Community", "Professional", "Enterprise")
_VCVARS_REL = Path("VC") / "Auxiliary" / "Build" / "vcvars64.bat"


def vcvars_from_vswhere(program_files: str | None = None,
                        runner: CommandRunner | None = None) -> Path | None:
    """Return the vcvars64.bat of the latest VS install vswhere reports, or None.

    Args:
        program_files: The folder holding ``Microsoft Visual Studio``; the environment's when ``None``.
        runner: Runs vswhere; the quiet runner when ``None``.
    """
    program_files = program_files or os.environ.get("ProgramFiles(x86)") or os.environ.get(
        "ProgramFiles", r"C:\Program Files")
    vswhere = Path(program_files) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
    if not vswhere.is_file():
        return None
    cmd = [str(vswhere), "-latest", "-prerelease", "-products", "*",
           "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
           "-property", "installationPath"]
    code, out, err = (runner or quiet_runner()).capture(cmd, timeout=30)
    if did_not_run(cmd[0], code, err):
        _log.warning("vswhere did not run (%s); no Visual Studio install is reported", err)
        return None
    if code != 0:
        _log.warning("vswhere exited with status %d; no Visual Studio install is reported", code)
        return None
    for line in out.splitlines():
        candidate = Path(line.strip()) / _VCVARS_REL
        if line.strip() and candidate.is_file():
            return candidate
    return None


def vcvars_from_disk_scan(program_files: Sequence[Path] | None = None) -> Path | None:
    """Return the first vcvars64.bat under the Program Files VS roots, newest year first.

    Args:
        program_files: The folders holding ``Microsoft Visual Studio``; the environment's when ``None``.
    """
    if program_files is None:
        program_files = [Path(os.environ[var]) for var in ("ProgramFiles", "ProgramFiles(x86)")
                         if os.environ.get(var)]
    roots = [folder / "Microsoft Visual Studio" for folder in program_files]
    for root in roots:
        if not root.is_dir():
            continue
        years = sorted((d for d in root.iterdir() if d.is_dir()),
                       key=lambda d: d.name, reverse=True)
        for year in years:
            for edition in _VS_EDITIONS:
                candidate = year / edition / _VCVARS_REL
                if candidate.is_file():
                    return candidate
    return None


def find_vcvars(host: IHost | None = None,
                vswhere: Callable[[], Path | None] | None = None,
                program_files: Sequence[Path] | None = None) -> Path | None:
    """Return the vcvars64.bat of an installed Visual Studio, or None off Windows.

    Args:
        host: The host to judge; the running one when ``None``.
        vswhere: Gives the install vswhere reports; asks vswhere when ``None``.
        program_files: The folders the disk scan reads; the environment's when ``None``.
    """
    if not (host or current_host()).hosts_visual_studio:
        return None
    return (vswhere or vcvars_from_vswhere)() or vcvars_from_disk_scan(program_files)
