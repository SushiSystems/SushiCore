# machine_actions.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The calls the install steps make that reach the machine, each replaceable by a test."""

from __future__ import annotations

import dataclasses
import shutil
from pathlib import Path
from typing import Callable

from ..proc import CommandRunner
from . import probe
from .packages import refresh_windows_path
from .pipeline import InstallContext
from .process_run import provision_runner
from .toolchains import oneapi


def run_machine_command(command: list[str], runner: CommandRunner | None = None) -> int:
    """Run *command* in the current folder through *runner* and return its exit code.

    Args:
        runner: Runs the command with its output shown; the provision runner when ``None``.
    """
    return (runner or provision_runner()).run(command, Path.cwd())


@dataclasses.dataclass(frozen=True)
class MachineActions:
    """The calls the steps make that reach the machine, each replaceable by a test.

    Every default looks its function up when called, so a replacement made on the
    module that owns the function still takes effect.

    Attributes:
        refresh_path: Reloads ``PATH`` from the registry (Windows only).
        which: Finds an executable on ``PATH``; ``None`` when absent.
        find_vcvars: Finds the Visual Studio C++ tools script; ``None`` when absent.
        run_command: Runs a command line through the process brick and returns its exit code.
        resolve_config: Probes the machine-specific tool paths of a configuration.
        install_oneapi: Installs Intel oneAPI for a run; returns whether it succeeded.
        detect_vendor: Reads the discrete-GPU vendor off the machine.
    """

    refresh_path: Callable[[], None] = lambda: refresh_windows_path()
    which: Callable[[str], str | None] = lambda name: shutil.which(name)
    find_vcvars: Callable[[], Path | None] = lambda: probe.find_vcvars()
    run_command: Callable[..., int] = lambda cmd: run_machine_command(cmd)
    resolve_config: Callable[..., dict[str, str]] = (
        lambda cfg, gpu=False: probe.resolve_local_config(cfg, gpu=gpu))
    install_oneapi: Callable[[InstallContext], bool] = lambda ctx: oneapi.install_oneapi(ctx)
    detect_vendor: Callable[[], str] = lambda: probe.detect_gpu_vendor()
