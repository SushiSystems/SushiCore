# _process.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The quiet process runner the toolchain installers share."""

from __future__ import annotations

from typing import Any

from ..process_run import provision_runner


def _run_quiet(cmd: list[str], dry_run: bool, *, console: Any) -> bool:
    """Run *cmd* silently; show its last 20 output lines only on failure.

    Args:
        cmd: The argv to run.
        dry_run: Report the command without executing it.
        console: The console a failed run's output tail is shown through.

    Returns:
        True on a zero exit code, or always on a dry run.
    """
    return provision_runner(console).run_quiet(cmd, dry_run=dry_run)
