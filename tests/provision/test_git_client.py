# test_git_client.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the git client, with git replaced by recorded processes."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

from sushicore.provision import git_client
from sushicore.provision.git_client import GitClient, IGitClient
from sushicore.provision.git_client_memory import InMemoryGitClient



@pytest.mark.small
def test_clone_tag_runs_a_shallow_single_tag_clone(monkeypatch, tmp_path):
    """Check that the clone asks git for the tag only, at depth one."""
    seen = []
    monkeypatch.setattr(git_client, "run", lambda cmd, dry_run, check: seen.append(cmd) or 0)

    assert GitClient().clone_tag("https://x/y.git", "v1.0.0", tmp_path / "y", False)

    assert seen == [["git", "clone", "--depth", "1", "--branch", "v1.0.0", "--single-branch",
                     "https://x/y.git", str(tmp_path / "y")]]


@pytest.mark.small
def test_clone_tag_reports_a_failed_clone(monkeypatch, tmp_path):
    """Check that a nonzero exit is a failed clone."""
    monkeypatch.setattr(git_client, "run", lambda cmd, dry_run, check: 128)
    assert not GitClient().clone_tag("https://x/y.git", "v1.0.0", tmp_path / "y", False)


@pytest.mark.small
def test_head_returns_the_lower_case_commit(monkeypatch, tmp_path):
    """Check that HEAD is git rev-parse's output, stripped and lower-cased."""
    done = subprocess.CompletedProcess([], 0, stdout="ABCDEF\n", stderr="")
    monkeypatch.setattr(git_client.subprocess, "run", lambda *a, **k: done)
    assert GitClient().head(tmp_path) == "abcdef"


@pytest.mark.small
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


K_TAG = "v1.0.0"


@dataclass
class GitWorld:
    """A git client under test, a repository it can clone and a folder to clone into."""

    client: IGitClient
    url: str
    commit: str
    destination: Path
    elsewhere: Path


def _git(folder: Path, *arguments: str) -> str:
    """Run git in *folder* as a throwaway author and return its output."""
    done = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid",
         "-c", "commit.gpgsign=false", *arguments],
        cwd=folder, check=True, capture_output=True, text=True)
    return done.stdout.strip()


class GitClientContract:
    """The promises every :class:`IGitClient` keeps; a subclass supplies the world."""

    def test_a_known_tag_clones(self, world):
        assert world.client.clone_tag(world.url, K_TAG, world.destination, False) is True

    def test_the_head_of_a_clone_is_the_commit_of_its_tag(self, world):
        world.client.clone_tag(world.url, K_TAG, world.destination, False)
        assert world.client.head(world.destination) == world.commit

    def test_an_unknown_tag_does_not_clone(self, world):
        assert world.client.clone_tag(world.url, "v9.9.9", world.destination, False) is False

    def test_an_unknown_tag_leaves_no_checkout(self, world):
        world.client.clone_tag(world.url, "v9.9.9", world.destination, False)
        assert world.client.head(world.destination) == ""

    def test_a_dry_run_clone_leaves_no_checkout(self, world):
        world.client.clone_tag(world.url, K_TAG, world.destination, True)
        assert world.client.head(world.destination) == ""

    def test_a_folder_that_is_no_checkout_has_an_empty_head(self, world):
        assert world.client.head(world.elsewhere) == ""


@pytest.mark.small
class TestInMemoryGitClientKeepsTheGitClientContract(GitClientContract):
    """The in-memory client, which runs no git."""

    @pytest.fixture
    def world(self):
        url, commit = "https://example.invalid/lib.git", "ab" * 20
        return GitWorld(InMemoryGitClient({(url, K_TAG): commit}), url, commit,
                        Path("clone"), Path("elsewhere"))


@pytest.mark.medium
class TestGitClientKeepsTheGitClientContract(GitClientContract):
    """The git on PATH, cloning a repository made in the test's folder."""

    @pytest.fixture
    def world(self, tmp_path, recording_console):
        source = tmp_path / "source"
        source.mkdir()
        _git(source, "init", "-q")
        (source / "file.txt").write_text("content", encoding="utf-8")
        _git(source, "add", "file.txt")
        _git(source, "commit", "-q", "-m", "first")
        _git(source, "tag", K_TAG)
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        return GitWorld(GitClient(), source.as_uri(), _git(source, "rev-parse", "HEAD"),
                        tmp_path / "clone", elsewhere)
