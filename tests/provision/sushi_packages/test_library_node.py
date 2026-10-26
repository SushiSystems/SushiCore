# test_library_node.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the record of one library of a chain."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from sushicore.provision.sushi_packages.library_node import LibraryNode

pytestmark = pytest.mark.small


def test_a_node_keeps_what_the_walk_gave_it():
    """Check that the fields come back as given."""
    node = LibraryNode("sushiblas", Path("/ws/sushiblas"), "sb", ("bench/",), ("sushilog",))
    assert (node.name, node.cli, node.package_exclude, node.depends_on) == (
        "sushiblas", "sb", ("bench/",), ("sushilog",))


def test_a_node_cannot_change():
    """Check that a node is frozen."""
    node = LibraryNode("a", Path("."), "", (), ())
    with pytest.raises(FrozenInstanceError):
        node.name = "b"  # type: ignore[misc]
