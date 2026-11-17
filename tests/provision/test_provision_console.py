# test_provision_console.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that the install steps run against a console holding only the provision calls."""

from __future__ import annotations

import pytest

from sushicore.provision.config import ProvisionSettings
from sushicore.provision.install_context import InstallContext
from sushicore.provision.pipeline import InstallPipeline
from sushicore.provision.step import Step
from sushicore.provision.step_result import StepResult


class _Calls:
    """A console holding the calls the provision pipeline makes, recording their names."""

    is_machine_value = False

    def __init__(self) -> None:
        """Start with no call."""
        self.names: list[str] = []
        self.console = self

    def print(self, *objects: object, **kwargs: object) -> None:
        """Record a Rich print."""
        self.names.append("print")

    def command(self, text: str) -> None:
        """Record a command line."""
        self.names.append("command")

    def info(self, text: str) -> None:
        """Record an informational message."""
        self.names.append("info")

    def error(self, text: str) -> None:
        """Record an error."""
        self.names.append("error")

    def warn(self, text: str) -> None:
        """Record a warning."""
        self.names.append("warn")

    def is_machine(self) -> bool:
        """Report that the console prints for a person."""
        return False

    def success(self, text: str) -> None:
        """Record a success message."""
        self.names.append("success")

    def header(self, title: str) -> None:
        """Record a section title."""
        self.names.append("header")

    def progress(self, label: str, index: int, count: int, fraction: float | None = None) -> None:
        """Record a progress line."""
        self.names.append("progress")

    def table(self, columns: list[str], rows: list[list[str]], title: str = "") -> None:
        """Record a table."""
        self.names.append("table")

    def result(self, ok: bool, payload: dict | None = None) -> None:
        """Record a result event."""
        self.names.append("result")


class _Done(Step):
    """A step that reports success."""

    name = "done"

    def run(self, ctx: InstallContext) -> StepResult:
        """Report success."""
        return StepResult.OK


@pytest.mark.small
def test_a_pipeline_runs_over_a_console_holding_only_those_calls():
    """Check that a header, a progress line and a success line are all a done step needs."""
    console = _Calls()
    assert InstallPipeline([_Done()], console).run(InstallContext(cfg=ProvisionSettings())) is True
    assert console.names == ["header", "progress", "success"]
