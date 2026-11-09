# test_machine_seams.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the seams a module replaces to provision a machine it does not run on."""

from __future__ import annotations

import pytest

from sushicore.provision.machine_seams import MachineSeams


@pytest.mark.small
@pytest.mark.parametrize("field", ["managers", "base_checks", "toolchains"])
def test_a_seam_left_unset_is_none_so_the_real_machine_is_read(field):
    """Check that a default seam asks the commands for the real read."""
    assert getattr(MachineSeams(), field) is None
