# test_process_run.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the process runner the package managers and the git client share."""

from __future__ import annotations

import io
import sys

import pytest

from sushicore.provision.process_run import run


@pytest.mark.small
def test_a_dry_run_executes_nothing_and_returns_zero(recording_console):
    """Check that a dry run reports the command and gives exit code zero."""
    assert run([sys.executable, "-c", "raise SystemExit(5)"], True) == 0
    assert recording_console.texts("info") == ["(dry-run) not executed"]


@pytest.mark.small
def test_a_failing_command_returns_its_exit_code(recording_console, monkeypatch):
    """Check that the exit code of the child is the value returned, and a checked failure is reported."""
    class _Child:
        stdout = io.StringIO("")
        returncode = 3

        def wait(self) -> None:
            """Finish at once."""

    monkeypatch.setattr("subprocess.Popen", lambda *args, **kwargs: _Child())
    assert run(["tool"], False, check=True) == 3
    assert recording_console.texts("error") == ["Command failed (3)."]
