# test_errors.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the errors the backlog commands report."""

from __future__ import annotations

import pytest

from sushicore.backlog.errors import BacklogError, EntryNotFoundError, RefusedChangeError, RowError
from sushicore.errors import SushiCoreError

pytestmark = pytest.mark.small


@pytest.mark.parametrize("kind", [EntryNotFoundError, RefusedChangeError, RowError])
def test_every_backlog_error_reaches_the_entry_point_as_a_sushicore_error(kind):
    """The CLI's entry point catches each one and prints it as one line."""
    assert issubclass(kind, BacklogError)
    assert issubclass(kind, SushiCoreError)
