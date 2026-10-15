# test_toolkit_choice.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the record of one toolkit choice."""

import dataclasses

import pytest

from sushicore.provision.gpu.toolkit_choice import ToolkitChoice

pytestmark = pytest.mark.small


def test_a_choice_is_frozen_and_compares_by_value():
    choice = ToolkitChoice("sm_89", "linux-x86_64", "13.1.2")
    assert choice == ToolkitChoice("sm_89", "linux-x86_64", "13.1.2")
    with pytest.raises(dataclasses.FrozenInstanceError):
        choice.release = "12.0"
