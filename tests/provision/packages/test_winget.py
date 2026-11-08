# test_winget.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the winget package manager."""

import subprocess

import pytest

from sushicore.provision.packages import base, winget


class _Process:
    """Stands in for the process Popen starts: no output, a scripted exit code."""

    def __init__(self, returncode: int) -> None:
        """Store the exit code the process ends with."""
        self.stdout = None
        self.returncode = returncode

    def wait(self) -> None:
        """Do nothing, since nothing runs."""


def _started(monkeypatch, failing: str = "") -> list[list[str]]:
    """Replace the process start at the boundary; return the commands it was asked to start.

    A command holding *failing* ends with exit code 1.
    """
    commands: list[list[str]] = []

    def popen(command, **_options):
        """Record the command and answer a finished process."""
        commands.append(list(command))
        return _Process(1 if failing and failing in command else 0)

    monkeypatch.setattr(base.subprocess, "Popen", popen)
    return commands


def _listing(monkeypatch, text: str) -> None:
    """Make the winget listing say *text*."""
    done = subprocess.CompletedProcess([], 0, text, "")
    monkeypatch.setattr(winget.subprocess, "run", lambda *args, **kwargs: done)


K_LISTING = "Name Id\nGit Git.Git 2.4\n"


@pytest.mark.small
def test_available_follows_the_path(monkeypatch):
    """Check that winget is unavailable when it is not on PATH."""
    monkeypatch.setattr(winget.shutil, "which", lambda name: None)
    assert not winget.WingetManager().available()


@pytest.mark.small
def test_available_is_true_when_winget_is_on_the_path(monkeypatch):
    """Check that winget is available when it is on PATH."""
    monkeypatch.setattr(winget.shutil, "which", lambda name: "C:/winget.exe")
    assert winget.WingetManager().available()


@pytest.mark.small
@pytest.mark.parametrize(("package", "installed"), [
    ("git.git", True), ("Kitware.CMake", False), ("Git.G", False),
], ids=["the id in any case", "an id not listed", "part of an id is not the id"])
def test_is_installed_needs_the_whole_id_in_the_listing(monkeypatch, package, installed):
    """Check that a package reads as installed only when its whole id is in the listing."""
    _listing(monkeypatch, K_LISTING)
    assert winget.WingetManager().is_installed(package) is installed


@pytest.mark.small
def test_is_installed_is_false_when_winget_cannot_run(monkeypatch):
    """Check that a winget that cannot start reads as nothing installed."""
    def broken(*args, **kwargs):
        raise OSError("gone")
    monkeypatch.setattr(winget.subprocess, "run", broken)
    assert not winget.WingetManager().is_installed("Git.Git")


@pytest.mark.small
def test_install_runs_one_silent_command_per_package(monkeypatch, recording_console):
    """Check that each package gets its own silent winget command."""
    commands = _started(monkeypatch)
    winget.WingetManager().install(["A", "B"], dry_run=False)
    assert [command[3] for command in commands] == ["A", "B"]
    assert all("--silent" in command for command in commands)


@pytest.mark.small
def test_install_reports_a_failed_package(monkeypatch, recording_console):
    """Check that one failing package makes the install answer False."""
    _started(monkeypatch, failing="B")
    assert not winget.WingetManager().install(["A", "B"], dry_run=False)


@pytest.mark.small
def test_remove_uninstalls_each_package(monkeypatch, recording_console):
    """Check that remove starts one silent uninstall per package."""
    commands = _started(monkeypatch)
    assert winget.WingetManager().remove(["A"], dry_run=False)
    assert commands == [["winget", "uninstall", "--id", "A", "-e", "--silent"]]
