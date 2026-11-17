# test_report_console.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that a diagnostic report runs against a console with only the report calls."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from sushicore.diag import Diagnostics
from sushicore.diag_memory import InMemoryConfigModule
from sushicore.profile import ModuleProfile


@dataclass
class _Settings:
    cxx: str = ""


class _ReportCalls:
    """A console holding a header, an info line, an error and a table, and nothing else."""

    def __init__(self) -> None:
        """Start with no error."""
        self.errors: list[str] = []

    def header(self, title: str, /) -> None:
        """Ignore a section title."""

    def info(self, msg: str, /) -> None:
        """Ignore an informational line."""

    def error(self, msg: str, /) -> None:
        """Record an error."""
        self.errors.append(msg)

    def table(self, columns: list[str], rows: list[list[str]], title: str = "") -> None:
        """Ignore a table."""


@pytest.mark.small
def test_env_dump_without_a_build_environment_says_so_through_the_report_calls():
    """Check that a module with no build environment gets one error line and a non-zero exit."""
    console = _ReportCalls()
    diagnostics = Diagnostics(
        profile=ModuleProfile(name="SushiTest", program="st", env_prefix="ST"), console=console,
        config=InMemoryConfigModule(Path("module"), _Settings, {}), build_env=None)
    assert diagnostics.env_dump() != 0
    assert console.errors == ["st has no build environment to dump."]
