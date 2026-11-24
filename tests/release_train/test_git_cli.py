# test_git_cli.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the git operations of the train on a real repository."""

import subprocess
from pathlib import Path

import pytest

from sushicore.quiet_runner import quiet_runner
from sushicore.release_train.errors import ReleaseTrainError
from sushicore.release_train.git_cli import GitCli
from sushicore.release_train.version import Version

pytestmark = pytest.mark.medium


def _git(repo, *arguments):
    subprocess.run(["git", *arguments], cwd=repo, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "VERSION").write_text("0.1.0\n", encoding="utf-8")
    (tmp_path / "other.txt").write_text("x\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "--no-verify", "-m", "chore(release): v0.1.0")
    _git(tmp_path, "tag", "v0.1.0")
    return tmp_path


def test_the_latest_release_and_the_files_of_the_last_release_commit_are_read(repo):
    git = GitCli(quiet_runner())
    _git(repo, "tag", "v0.1.1")
    assert git.is_clean(repo)
    assert git.latest_release(repo) == Version(0, 1, 1)
    assert sorted(git.last_release_files(repo)) == [Path("VERSION"), Path("other.txt")]


def test_a_change_makes_the_tree_dirty(repo):
    (repo / "other.txt").write_text("y\n", encoding="utf-8")
    assert not GitCli(quiet_runner()).is_clean(repo)


def test_a_failed_command_raises_naming_the_repository(repo):
    with pytest.raises(ReleaseTrainError, match=repo.name):
        GitCli(quiet_runner()).tag(repo, "v0.1.0", "HEAD")
