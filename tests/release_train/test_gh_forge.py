# test_gh_forge.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for waiting on the workflows of a commit through gh."""

from pathlib import Path

import pytest

from sushicore.release_train.gh_forge import K_MAX_POLLS, GhForge

pytestmark = pytest.mark.small

K_REPO = Path("/w/x")


class _Runner:
    def __init__(self, answers):
        self.answers = list(answers)
        self.commands = []

    def capture(self, cmd, cwd=None, **_options):
        self.commands.append(cmd)
        return 0, self.answers.pop(0) if self.answers else "[]", ""


def test_the_newest_run_is_waited_for_until_it_completes():
    runner = _Runner(['[{"status":"in_progress","conclusion":""}]',
                      '[{"status":"completed","conclusion":"success"}]'])
    sleeps = []
    assert GhForge(runner, sleeps.append).ci_passed(K_REPO, "abc")
    assert len(sleeps) == 1 and "ci.yml" in runner.commands[0]


def test_a_failed_run_fails():
    runner = _Runner(['[{"status":"completed","conclusion":"failure"}]'])
    assert not GhForge(runner, lambda _seconds: None).release_passed(K_REPO, "abc")
    assert "release.yml" in runner.commands[0]


def test_a_run_that_never_shows_fails_after_the_last_poll():
    sleeps = []
    assert not GhForge(_Runner([]), sleeps.append).ci_passed(K_REPO, "abc")
    assert len(sleeps) == K_MAX_POLLS
