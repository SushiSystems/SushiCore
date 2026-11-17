# process_run.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The process runner the package managers, the git client and the toolchain installers share."""

from __future__ import annotations

from ..proc import Runner
from ._output import console

K_PROGRAM = "sushicore"
"""The command name the runner's not-found guidance names."""


def provision_runner() -> Runner:
    """Return the runner that prints through the console provision is bound to."""
    return Runner(console, K_PROGRAM)


def run(cmd: list[str], dry_run: bool, *, check: bool = False) -> int:
    """Run *cmd*, streaming its output through the console; return its exit code."""
    return provision_runner().run_drained(cmd, None, dry_run=dry_run, check=check)
