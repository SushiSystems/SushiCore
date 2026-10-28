# conftest.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Fixtures shared by the design tests: a repository with two modules and a fixed clock."""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest

from sushicore.design import DesignStore

K_TODAY = datetime.date(2026, 10, 28)


@pytest.fixture
def store(tmp_path: Path) -> DesignStore:
    """Returns the design store of a repository with the modules atmosphere and clouds."""
    root = tmp_path / "repo"
    for module in ("modules/atmosphere", "modules/clouds", "modules/atmosphere/sky"):
        (root / module).mkdir(parents=True, exist_ok=True)
    (root / "docs" / "design").mkdir(parents=True)
    return DesignStore(root, lambda: K_TODAY)
