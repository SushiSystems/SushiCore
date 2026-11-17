# machine_actions.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The calls the install steps make that reach the machine, each replaceable by a test."""

from __future__ import annotations

import dataclasses
import shutil
from pathlib import Path
from typing import Callable, final

from .default_console import console_or_default
from ..proc import CommandRunner
from . import gpu_vendor, probe, vs_locator
from .gpu_machine import ConfigResolver
from .packages import refresh_windows_path
from .install_context import InstallContext
from .process_run import provision_runner
from .provision_console import ProvisionConsole
from .toolchains import oneapi


def run_machine_command(command: list[str], runner: CommandRunner | None = None, *,
                        console: ProvisionConsole | None = None) -> int:
    """Run *command* in the current folder through *runner* and return its exit code.

    Args:
        console: The console the command's output is shown through.
        runner: Runs the command with its output shown; the provision runner on *console*
            when ``None``.
    """
    console = console_or_default(console, "run_machine_command")
    return (runner or provision_runner(console)).run(command, Path.cwd())


@final
@dataclasses.dataclass(frozen=True)
class MachineActions:
    """The calls the steps make that reach the machine, each replaceable by a test.

    Every default looks its function up when called.

    Attributes:
        refresh_path: Reloads ``PATH`` from the registry (Windows only).
        which: Finds an executable on ``PATH``; ``None`` when absent.
        run_command: Runs a command line on the console it is given; returns its exit code.
    """

    refresh_path: Callable[[], None] = lambda: refresh_windows_path()
    which: Callable[[str], str | None] = lambda name: shutil.which(name)
    find_vcvars: Callable[[], Path | None] = lambda: vs_locator.find_vcvars()
    run_command: Callable[[list[str], ProvisionConsole], int] = (
        lambda cmd, console: run_machine_command(cmd, console=console))
    resolve_config: ConfigResolver = (
        lambda cfg, gpu=False: probe.resolve_local_config(cfg, gpu=gpu))
    install_oneapi: Callable[[InstallContext, ProvisionConsole], bool] = (
        lambda ctx, console: oneapi.install_oneapi(ctx, console=console))
    detect_vendor: Callable[[], str] = lambda: gpu_vendor.detect_gpu_vendor()
