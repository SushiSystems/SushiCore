# test_toolchain_selection.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the toolchain components a run selects."""

from __future__ import annotations

import pytest

from sushicore.provision.toolchain_selection import ToolchainSelection


@pytest.mark.small
def test_the_default_selection_selects_nothing():
    """Check that no component is selected by default."""
    assert ToolchainSelection().as_dict() == {
        "install_intel_llvm": False, "install_acpp": False, "oneapi": False, "gpu": False}


@pytest.mark.small
def test_merged_applies_known_names_and_ignores_unknown_ones():
    """Check that an override of a known field applies, a stray key does not, and the original stays."""
    base = ToolchainSelection(oneapi=True)
    merged = base.merged({"gpu": 1, "no_such_field": True})
    assert merged.as_dict() == {
        "install_intel_llvm": False, "install_acpp": False, "oneapi": True, "gpu": True}
    assert base.gpu is False
