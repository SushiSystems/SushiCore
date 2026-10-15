# test_winget.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the winget package manager."""

import subprocess

import pytest

from sushicore.provision.packages import winget

pytestmark = pytest.mark.small


def _recorder(calls, failing=""):
    def run(command, dry_run, check=False):
        calls.append(command)
        return 1 if failing and failing in command else 0
    return run


def test_available_follows_the_path(monkeypatch):
    monkeypatch.setattr(winget.shutil, "which", lambda name: None)
    assert not winget.WingetManager().available()


def test_is_installed_needs_the_id_in_the_listing(monkeypatch):
    listing = subprocess.CompletedProcess([], 0, "Name Id\nGit Git.Git 2.4\n", "")
    monkeypatch.setattr(winget.subprocess, "run", lambda *args, **kwargs: listing)
    assert winget.WingetManager().is_installed("git.git")
    assert not winget.WingetManager().is_installed("Kitware.CMake")


def test_is_installed_is_false_when_winget_cannot_run(monkeypatch):
    def broken(*args, **kwargs):
        raise OSError("gone")
    monkeypatch.setattr(winget.subprocess, "run", broken)
    assert not winget.WingetManager().is_installed("Git.Git")


def test_install_runs_one_silent_command_per_package_and_reports_failure(monkeypatch):
    calls = []
    monkeypatch.setattr(winget, "run", _recorder(calls, failing="B"))
    assert not winget.WingetManager().install(["A", "B"], dry_run=False)
    assert [command[3] for command in calls] == ["A", "B"]
    assert all("--silent" in command for command in calls)


def test_remove_uninstalls_each_package(monkeypatch):
    calls = []
    monkeypatch.setattr(winget, "run", _recorder(calls))
    assert winget.WingetManager().remove(["A"], dry_run=True)
    assert calls == [["winget", "uninstall", "--id", "A", "-e", "--silent"]]
