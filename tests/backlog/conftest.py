# conftest.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Fixtures shared by the backlog tests: a repository with an empty store, on disk and in memory, and a command runner."""

from __future__ import annotations

import datetime
from collections.abc import Callable
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from sushicore.backlog import BacklogEditor, BacklogError, BacklogStore, register_backlog_commands
from sushicore.console_memory import RecordingConsole
from sushicore.files_memory import MemoryFiles

K_TODAY = datetime.date(2026, 10, 28)


@pytest.fixture
def invoke() -> Callable[..., tuple[int, list[str]]]:
    """Returns a function that runs one command of an application named `sx` and returns its code and its lines.

    The function takes the repository root, the arguments after `backlog`, and *unverified*, which
    stands for the stamp; by default a stamp exists and names nothing. A BacklogError reaches the
    caller, as it reaches a CLI's entry point.
    """

    def run(root: Path, *arguments: str, unverified=lambda _root: frozenset()) -> tuple[int, list[str]]:
        console = RecordingConsole()
        app = typer.Typer(name="sx", no_args_is_help=True, add_completion=False)

        @app.command("build")
        def build() -> None:
            """Build."""

        register_backlog_commands(
            app, program="sx", panel="Project", project_root=lambda: root, report=console.info,
            unverified=unverified,
        )
        result = CliRunner().invoke(app, ["backlog", *arguments])
        if result.exception and not isinstance(result.exception, SystemExit):
            raise result.exception
        return result.exit_code, console.texts("info")

    return run


@pytest.fixture
def store(tmp_path: Path) -> BacklogStore:
    """Returns the store of a repository with the areas BUILD and PHYSICS and nothing in them."""
    root = tmp_path / "repo"
    (root / "docs" / "design").mkdir(parents=True)
    (root / "modules" / "physics").mkdir(parents=True)
    current = BacklogStore(root, lambda: K_TODAY)
    editor = BacklogEditor(current)
    editor.add_area("PHYSICS")
    editor.add_area("BUILD")
    return current


@pytest.fixture
def editor(store: BacklogStore) -> BacklogEditor:
    """Returns the editor of the fixture store."""
    return BacklogEditor(store)


@pytest.fixture
def memory_store() -> BacklogStore:
    """Returns the store of a repository held in memory, with the areas BUILD and PHYSICS."""
    current = BacklogStore(Path("repo"), lambda: K_TODAY, MemoryFiles())
    editor = BacklogEditor(current)
    editor.add_area("PHYSICS")
    editor.add_area("BUILD")
    return current


@pytest.fixture
def memory_editor(memory_store: BacklogStore) -> BacklogEditor:
    """Returns the editor of the in-memory store."""
    return BacklogEditor(memory_store)
