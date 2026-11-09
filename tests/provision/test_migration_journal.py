# test_migration_journal.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the journal a migration appends to."""

from __future__ import annotations

import pytest

from sushicore.provision.migration_journal import JOURNAL, MigrationJournal


@pytest.mark.medium
def test_journal_leaves_out_a_line_cut_short(tmp_path):
    """Check that a journal line that is not whole JSON is not returned."""
    journal = MigrationJournal(tmp_path)
    journal.append("moved", name="tools")
    with (tmp_path / JOURNAL).open("a", encoding="utf-8") as stream:
        stream.write('{"step": "mov')
    assert journal.entries() == [{"step": "moved", "name": "tools"}]
    assert journal.names("moved") == {"tools"}
