# test_zypper_manager.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the zypper package manager."""

from __future__ import annotations

import os

import pytest

from sushicore.proc_memory import RecordingRunner
from sushicore.provision.packages.zypper_manager import ZypperManager


@pytest.fixture
def runner(recording_console) -> RecordingRunner:
    """Build the runner that records the commands of a manager and starts none."""
    return RecordingRunner(recording_console)


@pytest.fixture(autouse=True)
def _root(monkeypatch):
    """Run as root so no command carries sudo."""
    monkeypatch.setattr(os, "geteuid", lambda: 0, raising=False)


@pytest.mark.small
def test_install_runs_the_zypper_install_command(runner, recording_console):
    """Check that install hands the packages to zypper."""
    assert ZypperManager(runner, console=recording_console).install(["cmake"], dry_run=False)
    assert [list(c.argv) for c in runner.commands] == [['zypper', 'install', '-y'] + ["cmake"]]


@pytest.mark.small
def test_remove_runs_the_zypper_remove_command(runner, recording_console):
    """Check that remove hands the packages to zypper."""
    assert ZypperManager(runner, console=recording_console).remove(["cmake"], dry_run=False)
    assert [list(c.argv) for c in runner.commands] == [['zypper', 'remove', '-y'] + ["cmake"]]


@pytest.mark.small
def test_installing_nothing_runs_nothing(runner, recording_console):
    """Check that an empty list starts no process and succeeds."""
    assert ZypperManager(runner, console=recording_console).install([], dry_run=False)
    assert runner.commands == []
