# test_library_node.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the record of one library of a chain."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from sushicore.provision.sushi_packages.library_node import LibraryNode

pytestmark = pytest.mark.small


def test_a_node_cannot_change():
    """Check that a node is frozen."""
    node = LibraryNode("a", Path("."), "", (), ())
    with pytest.raises(FrozenInstanceError):
        node.name = "b"  # type: ignore[misc]
