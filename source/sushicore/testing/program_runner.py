# program_runner.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Runs a test program of a build tree by the name its shards carry."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Callable, final

from ..files import DiskFiles, Files
from ..proc import CommandRunner
from ..quiet_runner import quiet_runner
from .shards import program_executable


def run_with_timeout(command: list[str], cwd: Path, env: dict[str, str] | None, timeout: float,
                     runner: CommandRunner | None = None) -> int:
    """Run *command* in *cwd* under *env*, stopping it after *timeout* seconds, and return its exit code.

    A command that is stopped returns ``K_TIMEOUT_EXIT_CODE``; one that cannot start returns 1.
    *runner* spawns it; the real one when None.
    """
    return (runner if runner is not None else quiet_runner()).run(command, cwd, env, timeout=timeout)


@final
class ProgramRunner:
    """Runs one test program of a build tree, with the environment the module runs its tests under.

    A CLI hands an instance to ``ModuleTests`` as ``run_program``, so a failed shard reruns only
    its failing cases.

    Args:
        tree: The built tree whose test files name the programs.
        env: The environment the program runs under; None for the caller's own.
    """

    def __init__(self, tree: Path, run: Callable[..., int], env: dict[str, str] | None = None,
                 files: Files | None = None,
                 run_timed: Callable[..., int] | None = None,
                 runner: CommandRunner | None = None) -> None:
        self._tree = tree
        self._run = run
        self._env = env
        self._files = files if files is not None else DiskFiles()
        self._runner = runner if runner is not None else quiet_runner()
        self._run_timed = run_timed if run_timed is not None else self._run_with_timeout

    def __call__(self, program: str, arguments: Sequence[str], *, env: Mapping[str, str] | None = None,
                 timeout: float | None = None) -> int:
        """Run *program* with *arguments* and return its exit code; 1 when the tree holds no such program.

        Args:
            program: The program by the name its shards carry.
            arguments: The command-line arguments.
            env: Variables added to the runner's environment for this run, such as a shard's.
            timeout: Seconds after which the program is stopped; it runs to its end when None.
        """
        executable = program_executable(self._tree, program, self._files)
        if executable is None:
            return 1
        environment = self._env
        if env:
            environment = {**(self._env if self._env is not None else os.environ), **env}
        command = [str(executable), *arguments]
        if timeout is None:
            return self._run(command, self._tree, environment)
        return self._run_timed(command, self._tree, environment, timeout)

    def _run_with_timeout(self, command: list[str], cwd: Path, env: dict[str, str] | None,
                          timeout: float) -> int:
        """Run *command* through the runner, stopped after *timeout* seconds."""
        return run_with_timeout(command, cwd, env, timeout, self._runner)
