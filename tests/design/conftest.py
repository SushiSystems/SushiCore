# conftest.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Fixtures shared by the design tests: a repository with three modules and a fixed clock."""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from sushicore.console_memory import RecordingConsole
from sushicore.design import DesignStore, register_design_commands
from sushicore.files_memory import MemoryFiles

K_TODAY = datetime.date(2026, 10, 28)


class DesignCli:
    """An application named `sx` with the design group on an in-memory repository."""

    def __init__(self, store) -> None:
        """Registers the group on the store's files and clock, reporting to a recording console."""
        self.console = RecordingConsole()
        self.app = typer.Typer(name="sx", no_args_is_help=True, add_completion=False)

        @self.app.command("build")
        def build() -> None:
            """Build."""

        register_design_commands(
            self.app, program="sx", panel="Project", project_root=lambda: store.root,
            report=self.console.info, today=lambda: K_TODAY, files=store.files,
        )

    def run(self, *arguments: str) -> int:
        """Runs one design command and returns its exit code; an error it raises is raised again."""
        result = CliRunner().invoke(self.app, ["design", *arguments])
        if result.exception and not isinstance(result.exception, SystemExit):
            raise result.exception
        return result.exit_code

    def lines(self) -> list[str]:
        """Returns every line reported so far."""
        return self.console.texts("info")


@pytest.fixture
def store(tmp_path: Path) -> DesignStore:
    """Returns the design store of a repository with the modules atmosphere and clouds."""
    root = tmp_path / "repo"
    for module in ("modules/atmosphere", "modules/clouds", "modules/atmosphere/sky"):
        (root / module).mkdir(parents=True, exist_ok=True)
    (root / "docs" / "design").mkdir(parents=True)
    return DesignStore(root, lambda: K_TODAY)


@pytest.fixture
def memory_store() -> DesignStore:
    """Returns the design store of an in-memory repository with the modules atmosphere, clouds and sky."""
    root = Path("repo")
    modules = ("modules/atmosphere", "modules/clouds", "modules/atmosphere/sky")
    files = MemoryFiles({root / module / "CMakeLists.txt": "" for module in modules})
    return DesignStore(root, lambda: K_TODAY, files)


@pytest.fixture
def cli(memory_store) -> DesignCli:
    """Returns the CLI of the in-memory repository."""
    return DesignCli(memory_store)


@pytest.fixture
def disk_cli(store) -> DesignCli:
    """Returns the CLI of the repository on disk."""
    return DesignCli(store)
