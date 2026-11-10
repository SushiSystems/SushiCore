# program_runner.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Runs a test program of a build tree by the name its shards carry."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Callable

from ..files import DiskFiles, Files
from .shards import program_executable


class ProgramRunner:
    """Runs one test program of a build tree, with the environment the module runs its tests under.

    A CLI hands an instance to ``ModuleTests`` as ``run_program``, so a failed shard reruns only its
    failing cases. The executable is the one the tree's shard registrations name, so the CLI states
    no path of its own.

    Args:
        tree: The built tree whose test files name the programs.
        run: Runs a command in a folder under an environment and returns its exit code.
        env: The environment the program runs under; None for the caller's own.
        files: The file system the tree's test files are read from; the disk when None.
    """

    def __init__(self, tree: Path, run: Callable[..., int], env: dict[str, str] | None = None,
                 files: Files | None = None) -> None:
        self._tree = tree
        self._run = run
        self._env = env
        self._files = files if files is not None else DiskFiles()

    def __call__(self, program: str, arguments: Sequence[str]) -> int:
        """Run *program* with *arguments* and return its exit code; 1 when the tree holds no such program."""
        executable = program_executable(self._tree, program, self._files)
        if executable is None:
            return 1
        return self._run([str(executable), *arguments], self._tree, self._env)
