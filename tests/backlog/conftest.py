# conftest.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Fixtures shared by the backlog tests: a repository with an empty store, on disk and in memory."""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest

from sushicore.backlog import BacklogEditor, BacklogStore
from sushicore.files_memory import MemoryFiles

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


@pytest.fixture
def memory_store() -> BacklogStore:
    """Returns the store of a repository held in memory, with the areas BUILD and PHYSICS."""
    current = BacklogStore(Path("repo"), lambda: K_TODAY, MemoryFiles())
    editor = BacklogEditor(current)
    editor.add_area("PHYSICS")
    editor.add_area("BUILD")
    return current


@pytest.fixture
def memory_editor(memory_store: BacklogStore) -> BacklogEditor:
    """Returns the editor of the in-memory store."""
    return BacklogEditor(memory_store)
