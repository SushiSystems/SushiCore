# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The quiet subprocess runner shared by the toolchain installers."""

from __future__ import annotations

import subprocess

from .._output import console


def _run_quiet(cmd: list[str], dry_run: bool) -> bool:
    """Run *cmd* silently; print its last 20 output lines only on failure.

    Args:
        cmd: The argv to run.
        dry_run: Report the command without executing it.

    Returns:
        True on a zero exit code, or always on a dry run.
    """
    console.command(subprocess.list2cmdline(cmd))
    if dry_run:
        console.info("(dry-run) not executed")
        return True
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        lines = (result.stdout or "").splitlines()
        for line in lines[-20:]:
            console.console.print(line, markup=False, highlight=False)
    return result.returncode == 0
