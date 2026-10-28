# conftest.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Fixtures shared by the backlog tests: a repository with an empty store and a fixed clock."""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest

from sushicore.backlog import BacklogEditor, BacklogStore

K_TODAY = datetime.date(2026, 10, 28)


@pytest.fixture
def store(tmp_path: Path) -> BacklogStore:
    """Returns the store of a repository with the areas BUILD and PHYSICS and nothing in them."""
    root = tmp_path / "repo"
    (root / "docs" / "design").mkdir(parents=True)
    (root / "modules" / "physics").mkdir(parents=True)
    current = BacklogStore(root, lambda: K_TODAY)
    editor = BacklogEditor(current)
    editor.add_area("PHYSICS")
    editor.add_area("BUILD")
    return current


@pytest.fixture
def editor(store: BacklogStore) -> BacklogEditor:
    """Returns the editor of the fixture store."""
    return BacklogEditor(store)
