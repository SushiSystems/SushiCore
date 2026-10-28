# test_errors.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the errors the design commands report."""

from __future__ import annotations

import pytest

from sushicore.design.errors import DesignError, OwnedModuleError, TopicNotFoundError
from sushicore.errors import SushiCoreError

pytestmark = pytest.mark.small


@pytest.mark.parametrize("kind", [OwnedModuleError, TopicNotFoundError])
def test_every_design_error_reaches_the_entry_point_as_a_sushicore_error(kind):
    """The CLI's entry point catches each one and prints it as one line."""
    assert issubclass(kind, DesignError)
    assert issubclass(kind, SushiCoreError)
