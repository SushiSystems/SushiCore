# run_program.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Runs one built program of a build tree: the one a CLI's `run` command resolves.

The reasoning is in docs/architecture/OVERVIEW.md, section `run_program`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Protocol

from .discovery import ConsoleLike, ExecutableIndex
from .example_catalog import ExampleCatalog
from .proc import CommandRunner


class RunConsole(ConsoleLike, Protocol):
    """The console lines `run_program` prints beyond the picker's own."""

    def info(self, text: str) -> None:
        """Prints an information line."""


def run_program(
    index: ExecutableIndex, console: RunConsole, runner: CommandRunner, *,
    build_dir: Path, project_root: Path, env: Mapping[str, str],
    target: str | None = None, pick: bool = False, list_all: bool = False,
    default: str = "", app_args: Sequence[str] = (),
) -> int:
    """Resolves a program under *build_dir*, runs it from *project_root* and returns its exit code.

    The program is the one *target* names, the one the user picks, or *default*. A pick lists the
    built examples of *project_root*, or every program when *list_all* is set. A resolution that
    fails prints its reason and returns 1.

    Args:
        index: The walk over the tree, with the directories its CLI skips.
        env: The environment the program runs under.
        app_args: The arguments handed to the program unchanged.
    """
    program = index.resolve(
        build_dir, console, target=target, sort=pick, default=default,
        examples=ExampleCatalog.in_project(project_root), list_all=list_all)
    if program is None:
        return 1
    console.info(f"Executing: {program.name}")
    return runner.run([str(program), *app_args], project_root, dict(env))
