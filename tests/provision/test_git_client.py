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

from sushicore.provision.git_client import GitClient, IGitClient
from sushicore.provision.git_client_memory import InMemoryGitClient



@pytest.mark.small
def test_clone_tag_runs_a_shallow_single_tag_clone():
    """Check that the clone asks git for the tag only, at depth one."""
    seen = []
    client = GitClient(runner=lambda command, dry_run, check: seen.append(command) or 0)

    client.clone_tag("https://x/y.git", "v1.0.0", Path("y"), False)

    assert seen == [["git", "clone", "--depth", "1", "--branch", "v1.0.0", "--single-branch",
                     "https://x/y.git", "y"]]


@pytest.mark.small
def test_clone_tag_reports_a_failed_clone():
    """Check that a nonzero exit is a failed clone."""
    client = GitClient(runner=lambda command, dry_run, check: 128)
    assert not client.clone_tag("https://x/y.git", "v1.0.0", Path("y"), False)


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


@pytest.mark.medium
def test_head_of_a_real_checkout_is_a_lower_case_commit(tmp_path):
    """Check that head gives the 40 lower-case hex digits of the checkout's commit."""
    _git(tmp_path, "init", "-q")
    (tmp_path / "file.txt").write_text("content", encoding="utf-8")
    _git(tmp_path, "add", "file.txt")
    _git(tmp_path, "commit", "-q", "-m", "first")
    assert GitClient().head(tmp_path) == _git(tmp_path, "rev-parse", "HEAD").lower()


@pytest.mark.medium
def test_head_is_empty_when_git_is_missing(tmp_path):
    """Check that an executable that cannot start gives ''."""
    assert GitClient(git="sushi-no-such-git").head(tmp_path) == ""
