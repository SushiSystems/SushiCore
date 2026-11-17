# process_run.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The process runner the package managers, the git client and the toolchain installers share."""

from __future__ import annotations

from typing import Any

from .default_console import console_or_default
from ..proc import Runner

K_PROGRAM = "sushicore"
"""The command name the runner's not-found guidance names."""


def provision_runner(console: Any = None) -> Runner:
    """Return the runner that prints through *console*."""
    console = console_or_default(console, "provision_runner")
    return Runner(console, K_PROGRAM)


def run(cmd: list[str], dry_run: bool, *, console: Any = None, check: bool = False) -> int:
    """Run *cmd*, streaming its output through *console*; return its exit code."""
    console = console_or_default(console, "run")
    return provision_runner(console).run_drained(cmd, None, dry_run=dry_run, check=check)
