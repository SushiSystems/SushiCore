# _process.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The quiet process runner the toolchain installers share."""

from __future__ import annotations

from ..process_run import provision_runner


def _run_quiet(cmd: list[str], dry_run: bool) -> bool:
    """Run *cmd* silently; show its last 20 output lines only on failure.

    Args:
        cmd: The argv to run.
        dry_run: Report the command without executing it.

    Returns:
        True on a zero exit code, or always on a dry run.
    """
    return provision_runner().run_quiet(cmd, dry_run=dry_run)
