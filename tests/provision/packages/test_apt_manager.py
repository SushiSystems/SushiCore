# test_apt_manager.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the apt package manager."""

from __future__ import annotations

import os

import pytest

from sushicore.proc_memory import RecordingRunner
from sushicore.provision.packages.apt_manager import AptManager


@pytest.fixture
def runner(recording_console) -> RecordingRunner:
    """Build the runner that records the commands of a manager and starts none."""
    return RecordingRunner(recording_console)


def _argv(runner: RecordingRunner) -> list[list[str]]:
    """Return the commands *runner* was asked to run, as lists."""
    return [list(command.argv) for command in runner.commands]


@pytest.mark.small
def test_apt_keeps_its_own_names(recording_console):
    """Check that apt names are apt's own."""
    apt = AptManager(console=recording_console)
    assert apt.translate_apt(["pkg-config"]) == ["pkg-config"]


@pytest.mark.small
def test_apt_is_installed_reads_the_dpkg_status(runner, recording_console):
    """Check that a dpkg status of installed reads as installed."""
    runner.script(0, ("install ok installed",))
    assert AptManager(runner, console=recording_console).is_installed("cmake")


@pytest.mark.small
def test_apt_install_updates_then_installs_without_sudo_as_root(
        monkeypatch, runner, recording_console):
    """Check that as root apt updates its cache and then installs, with no sudo."""
    monkeypatch.setattr(os, "geteuid", lambda: 0, raising=False)
    assert AptManager(runner, console=recording_console).install(["cmake"], dry_run=False)
    assert _argv(runner) == [["apt-get", "update"], ["apt-get", "install", "-y", "cmake"]]


@pytest.mark.small
def test_apt_install_of_nothing_runs_nothing(runner, recording_console):
    """Check that an empty list starts no process and succeeds."""
    assert AptManager(runner, console=recording_console).install([], dry_run=False)
    assert _argv(runner) == []
