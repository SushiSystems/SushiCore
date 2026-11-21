# test_verification.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the reading of the stamp and of the commits after it, on a temporary git repository."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from sushicore.backlog.verification import GitVerification, run_git
from sushicore.console_memory import RecordingConsole
from sushicore.proc_memory import RecordingRunner

pytestmark = pytest.mark.medium


def _git(root: Path, *arguments: str) -> str:
    """Runs git in a repository and returns its output."""
    return subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *arguments],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def _commit(root: Path, name: str, message: str) -> None:
    """Commits one new file with a message."""
    (root / name).parent.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(name, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", message)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Returns a repository with one commit that names RW-1."""
    _git(tmp_path, "init", "-q")
    _commit(tmp_path, "a", "feat: a\n\nBacklog: RW-1")
    return tmp_path


def _stamp_head(root: Path) -> None:
    """Writes HEAD as the stamp."""
    stamp = root / ".git" / "sushicore" / "verified"
    stamp.parent.mkdir(parents=True)
    stamp.write_text(_git(root, "rev-parse", "HEAD") + "\n", encoding="utf-8")


def test_a_repository_with_no_stamp_marks_nothing(repo):
    """Without a stamp the answer is None, the signal to print the no-stamp line."""
    assert GitVerification().unverified(repo) is None


def test_a_folder_outside_git_marks_nothing(tmp_path):
    """A folder that is no checkout has no stamp."""
    assert GitVerification().unverified(tmp_path) is None


def test_an_id_named_after_the_stamp_is_marked_and_one_before_it_is_not(repo):
    """RW-1 was named at the stamped commit; RW-2 after it."""
    _stamp_head(repo)
    _commit(repo, "b", "feat: b\n\nBacklog: RW-2")
    assert GitVerification().unverified(repo) == {"RW-2"}


def test_a_commit_after_the_stamp_that_only_files_an_entry_marks_nothing(repo):
    """A commit that changes only `docs/backlog/` is read with its paths and leaves RW-3 unmarked."""
    _stamp_head(repo)
    _commit(repo, "docs/backlog/CODE.md", "docs(backlog): file it\n\nBacklog: RW-3")
    _commit(repo, "source/b.py", "feat: do it\n\nBacklog: RW-4")
    assert GitVerification().unverified(repo) == {"RW-4"}


def test_run_git_returns_the_output_of_a_git_that_exits_zero(tmp_path: Path):
    """Git is asked in the given folder, through the runner."""
    runner = RecordingRunner(RecordingConsole()).script(0, ("abc",))
    assert run_git(tmp_path, "rev-parse", "HEAD", runner=runner) == "abc\n"
    assert [c.argv for c in runner.commands] == [("git", "-C", str(tmp_path), "rev-parse", "HEAD")]


@pytest.mark.parametrize("answer", ["failed", "missing"])
def test_run_git_returns_none_when_git_fails_or_is_missing(tmp_path: Path, answer: str):
    """A non-zero exit and an absent git both mean there is nothing to read."""
    runner = RecordingRunner(RecordingConsole())
    runner.script(128) if answer == "failed" else runner.script_missing()
    assert run_git(tmp_path, "log", runner=runner) is None
