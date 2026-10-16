# test_git_client.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the git client, with git replaced by recorded processes."""

from __future__ import annotations

import subprocess

import pytest

from sushicore.provision import git_client
from sushicore.provision.git_client import GitClient

pytestmark = pytest.mark.small


def test_clone_tag_runs_a_shallow_single_tag_clone(monkeypatch, tmp_path):
    """Check that the clone asks git for the tag only, at depth one."""
    seen = []
    monkeypatch.setattr(git_client, "run", lambda cmd, dry_run, check: seen.append(cmd) or 0)

    assert GitClient().clone_tag("https://x/y.git", "v1.0.0", tmp_path / "y", False)

    assert seen == [["git", "clone", "--depth", "1", "--branch", "v1.0.0", "--single-branch",
                     "https://x/y.git", str(tmp_path / "y")]]


def test_clone_tag_reports_a_failed_clone(monkeypatch, tmp_path):
    """Check that a nonzero exit is a failed clone."""
    monkeypatch.setattr(git_client, "run", lambda cmd, dry_run, check: 128)
    assert not GitClient().clone_tag("https://x/y.git", "v1.0.0", tmp_path / "y", False)


def test_head_returns_the_lower_case_commit(monkeypatch, tmp_path):
    """Check that HEAD is git rev-parse's output, stripped and lower-cased."""
    done = subprocess.CompletedProcess([], 0, stdout="ABCDEF\n", stderr="")
    monkeypatch.setattr(git_client.subprocess, "run", lambda *a, **k: done)
    assert GitClient().head(tmp_path) == "abcdef"


def test_head_is_empty_when_git_fails_or_is_missing(monkeypatch, tmp_path):
    """Check that a failing or absent git gives ''."""
    failed = subprocess.CompletedProcess([], 128, stdout="", stderr="not a repository")
    monkeypatch.setattr(git_client.subprocess, "run", lambda *a, **k: failed)
    assert GitClient().head(tmp_path) == ""

    def missing(*args, **kwargs):
        """Raise as a missing git does."""
        raise OSError("no git")
    monkeypatch.setattr(git_client.subprocess, "run", missing)
    assert GitClient().head(tmp_path) == ""
