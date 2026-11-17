# test_base.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the target contract."""

from __future__ import annotations

import pytest

from sushicore.provision.target import ITarget


@pytest.mark.small
def test_the_target_contract_cannot_be_instantiated():
    """Check that ITarget stays abstract, so every target implements every method."""
    with pytest.raises(TypeError):
        ITarget()  # type: ignore[abstract]
