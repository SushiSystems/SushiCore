# conftest.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Fixtures shared by the documentation bundle tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from .sample_repository import build_sample, commit_all


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    """Returns the root of a freshly written sample repository."""
    return build_sample(tmp_path / "sample")


@pytest.fixture
def checkout(repository: Path) -> Path:
    """Returns the sample repository as a git checkout with one commit."""
    commit_all(repository)
    return repository
