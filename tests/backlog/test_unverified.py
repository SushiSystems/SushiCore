# test_unverified.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests which IDs the commit messages after the verification stamp leave unverified."""

from __future__ import annotations

import pytest

from sushicore.backlog.unverified import unverified_ids

pytestmark = pytest.mark.small


def test_an_id_named_after_the_stamp_is_unverified():
    """A commit after the stamp that names RW-5 makes RW-5 unverified."""
    assert unverified_ids(["feat: a thing\n\nBacklog: RW-5\n"]) == {"RW-5"}


def test_an_id_named_before_the_stamp_is_not_unverified():
    """Only the commits after the stamp are given; RW-4 sat in an older one and is absent."""
    after_stamp = ["fix: a thing\n\nBacklog: RW-5, KI-2\n"]
    assert "RW-4" not in unverified_ids(after_stamp)


def test_no_commit_after_the_stamp_marks_nothing():
    """Nothing committed since the stamp leaves nothing unverified."""
    assert unverified_ids([]) == frozenset()


def test_an_id_in_the_body_outside_the_backlog_line_is_not_named():
    """Only the `Backlog:` line counts."""
    assert unverified_ids(["fix: RW-9 mentioned\n\nBacklog: none (docs)\n"]) == frozenset()
