# captured_run.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The deprecated command helpers package_install exported before 0.17.0; use proc.CommandRunner."""

from __future__ import annotations

import warnings
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import final

from ..proc import Runner
from ..quiet_console import QuietConsole

#: The exit code the helpers answer when a command cannot start.
K_CANNOT_START = 127


@final
@dataclass(frozen=True, slots=True)
class CapturedRun:
    """The exit code and the combined output of a command run with its output held back."""

    code: int
    output: str


def _warn(name: str) -> None:
    """Warn that *name* is deprecated in favour of proc.CommandRunner."""
    warnings.warn(f"package_install.{name} is deprecated; use sushicore.proc.CommandRunner",
                  DeprecationWarning, stacklevel=3)


def _runner() -> Runner:
    """Return a quiet runner that answers K_CANNOT_START for a missing executable."""
    return Runner(QuietConsole(), "sushicore", missing_exit_code=K_CANNOT_START)


def run_command(command: list[str], cwd: Path, env: Mapping[str, str] | None = None) -> int:
    """Run *command* in *cwd* and return its exit code; deprecated."""
    _warn("run_command")
    return _runner().run(command, cwd, None if env is None else dict(env))


def capture_command(command: list[str], cwd: Path,
                    env: Mapping[str, str] | None = None) -> CapturedRun:
    """Run *command* in *cwd* and return its exit code and its stdout then stderr; deprecated."""
    _warn("capture_command")
    code, out, err = _runner().capture(command, cwd, None if env is None else dict(env))
    return CapturedRun(code, out + err)
