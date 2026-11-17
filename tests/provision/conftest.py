# conftest.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Fixtures shared by the provision tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.output_memory import MemoryConsole

from .migration_fakes import build_roots


@pytest.fixture
def recording_console() -> MemoryConsole:
    """Return a fresh in-memory console for the test to pass to what prints."""
    return MemoryConsole()


@pytest.fixture
def roots(tmp_path) -> tuple[Path, Path]:
    """Build the old tree of a migration and name the new root."""
    return build_roots(tmp_path)
