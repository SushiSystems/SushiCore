# process_run.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The process runner the package managers and the git client share."""

from __future__ import annotations

import subprocess

from ._output import console


def run(cmd: list[str], dry_run: bool, *, check: bool = False) -> int:
    """Run *cmd*, streaming its output through the console; return its exit code."""
    console.command(subprocess.list2cmdline(cmd))
    if dry_run:
        console.info("(dry-run) not executed")
        return 0
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )
    if process.stdout:
        for line in iter(process.stdout.readline, ""):
            console.console.print(line.rstrip("\n"), markup=False, highlight=False)
    process.wait()
    if check and process.returncode != 0:
        console.error(f"Command failed ({process.returncode}).")
    return process.returncode
