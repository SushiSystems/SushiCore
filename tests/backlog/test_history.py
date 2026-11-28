# test_history.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the reading of the backlog's history: when each entry opened and closed, and what each commit changed."""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest

from sushicore.backlog import GitHistory, Recorded
from sushicore.backlog.history import PathChange, changes_after, parse_backlog_log, parse_path_log

pytestmark = pytest.mark.small

K_ROW_1 = "| RW-1 | P2 | open | Fix the step | it passes |  | `src/step.cpp` | 2026-11-01 |"
K_ROW_1_EDITED = "| RW-1 | P1 | open | Fix the step | it passes |  | `src/step.cpp` | 2026-11-01 |"
K_ROW_2 = "| RW-2 | P2 | open | Fix the gate | it passes |  | `src/gate.cpp` | 2026-11-02 |"
K_ISSUE = "| KI-1 | own | It drifts | restart | none, by design | `src/step.cpp` | 2026-11-02 |"
K_LOG = (
    "\x1e2026-11-01\n\ndiff --git a/docs/backlog/PHYSICS.md b/docs/backlog/PHYSICS.md\n"
    f"@@ -5,0 +6 @@\n+{K_ROW_1}\n"
    "\x1e2026-11-02\n\n"
    f"@@ -6 +6 @@\n-{K_ROW_1}\n+{K_ROW_1_EDITED}\n+{K_ROW_2}\n+{K_ISSUE}\n"
    "\x1e2026-11-05\n\n"
    f"@@ -6 +5,0 @@\n-{K_ROW_1_EDITED}\n"
)


def _day(text: str) -> datetime.date:
    """Returns the date an ISO text names."""
    return datetime.date.fromisoformat(text)


def test_parse_backlog_log_dates_each_entry_by_the_commits_that_wrote_and_removed_its_row():
    """A row written opens an entry; a row removed alone closes it; a row removed and rewritten stays open."""
    lives = parse_backlog_log(K_LOG)
    found = [(life.ident, life.opened, life.closed) for life in lives]
    assert found == [
        ("RW-1", _day("2026-11-01"), _day("2026-11-05")),
        ("RW-2", _day("2026-11-02"), None),
        ("KI-1", _day("2026-11-02"), None),
    ]


def test_parse_backlog_log_keeps_the_source_cell_of_both_kinds():
    """The Source is the cell before Opened, in a work row and in an issue row."""
    sources = [life.source for life in parse_backlog_log(K_LOG)]
    assert sources == ["`src/step.cpp`", "`src/gate.cpp`", "`src/step.cpp`"]


def test_parse_backlog_log_leaves_out_a_header_row():
    """A table header written with the first entry is not an entry."""
    log = "\x1e2026-11-01\n+| ID | Pri | State |\n+| --- | --- | --- |\n" f"+{K_ROW_1}\n"
    assert [life.ident for life in parse_backlog_log(log)] == ["RW-1"]


def test_parse_path_log_reads_the_date_and_paths_of_each_commit():
    """Each record holds one commit's date and the paths it changed."""
    log = "\x1e2026-11-03\n\nsrc/step.cpp\nsrc/gate.cpp\n\x1e2026-11-04\n\ndocs/README.md\n"
    assert parse_path_log(log) == [
        PathChange(_day("2026-11-03"), ("src/step.cpp", "src/gate.cpp")),
        PathChange(_day("2026-11-04"), ("docs/README.md",)),
    ]


def test_changes_after_counts_the_later_commits_that_change_a_covered_path():
    """A commit on the day the entry opened is the one that opened it, so it is not counted."""
    changes = [
        PathChange(_day("2026-11-01"), ("src/step.cpp",)),
        PathChange(_day("2026-11-02"), ("src/physics/a.cpp",)),
        PathChange(_day("2026-11-03"), ("src/step.cpp", "src/gate.cpp")),
    ]
    assert changes_after("`src/step.cpp`", _day("2026-11-01"), changes) == 1


def test_git_history_reads_the_paths_since_the_oldest_entry():
    """The path log starts on the day the first entry opened."""
    calls: list[tuple[str, ...]] = []

    def git(_root: Path, *arguments: str) -> str:
        calls.append(arguments)
        return K_LOG if arguments[-1] == "docs/backlog" else "\x1e2026-11-03\n\nsrc/step.cpp\n"

    recorded = GitHistory(git).read(Path("repo"))
    assert (calls[1][-1], len(recorded.lives), len(recorded.changes)) == ("--since=2026-11-01", 3, 1)


def test_git_history_is_none_when_git_cannot_read_the_backlog():
    """A checkout git cannot read has no history."""
    assert GitHistory(lambda _root, *_arguments: None).read(Path("repo")) is None


def test_git_history_is_empty_for_a_backlog_with_no_entry_yet():
    """No entry means no window to read paths for."""
    assert GitHistory(lambda _root, *_arguments: "").read(Path("repo")) == Recorded()
