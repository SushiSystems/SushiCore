# test_migration_error.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the error a migration raises."""

from __future__ import annotations

import pytest

from sushicore.errors import SushiCoreError
from sushicore.provision.migration_error import MigrationError


@pytest.mark.small
def test_a_migration_error_is_caught_where_the_command_catches_sushicore_errors():
    """Check that the command line boundary, which catches SushiCoreError, catches it."""
    with pytest.raises(SushiCoreError):
        raise MigrationError("could not move")
