# test_source_revision.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests how a bundle reads the commit it is built from."""

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.docs_bundle.errors import ReleaseError
from sushicore.docs_bundle.source_revision import read_head_commit
from sushicore.proc_memory import RecordingRunner

pytestmark = pytest.mark.small


def _runner() -> RecordingRunner:
    return RecordingRunner(RecordingConsole())


def test_returns_the_head_commit(tmp_path):
    runner = _runner().script(0, ("abc123",))
    assert read_head_commit(tmp_path, runner) == "abc123"
    assert [(c.argv, c.cwd) for c in runner.commands] == [(("git", "rev-parse", "HEAD"), tmp_path)]


def test_a_folder_that_is_not_a_checkout_is_a_release_error(tmp_path):
    runner = _runner().script(128, stderr="not a git repository\n")
    with pytest.raises(ReleaseError, match="not a git checkout: not a git repository"):
        read_head_commit(tmp_path, runner)


def test_a_missing_git_is_a_release_error(tmp_path):
    with pytest.raises(ReleaseError, match="git could not be run"):
        read_head_commit(tmp_path, _runner().script_missing())
