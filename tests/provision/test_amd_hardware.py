# test_amd_hardware.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The amdgpu topology becomes the ISA name of each card."""

from __future__ import annotations

import pytest

from sushicore.provision.gpu.amd_hardware import (
    AmdHardware,
    parse_targets,
    query_hardware,
    target_name,
)


pytestmark = pytest.mark.medium


@pytest.mark.parametrize(("version", "name"), [
    (90010, "gfx90a"), (110003, "gfx1103"), (100300, "gfx1030"), (120001, "gfx1201"),
    (90008, "gfx908"),
])
def test_target_name_spells_minor_and_stepping_in_hex(version, name):
    """Check the packed version against the ISA names AMD uses."""
    assert target_name(version) == name


def test_parse_targets_skips_the_cpu_and_collapses_twins():
    """Check that the CPU's 0 is dropped and two equal cards count once."""
    nodes = ["cpu_cores_count 12\ngfx_target_version 0\n",
             "gfx_target_version 110003\nsimd_count 4\n",
             "gfx_target_version 110003\n",
             "gfx_target_version 100300\n"]

    assert parse_targets(nodes) == AmdHardware(("gfx1030", "gfx1103"))


def test_parse_targets_without_a_card_is_none():
    """Check that a CPU-only topology yields no record."""
    assert parse_targets(["gfx_target_version 0\n"]) is None


def test_query_hardware_reads_the_node_files(tmp_path):
    """Check that each node folder's properties file is read."""
    for index, version in enumerate((0, 110003)):
        node = tmp_path / str(index)
        node.mkdir()
        (node / "properties").write_text(f"gfx_target_version {version}\n", encoding="utf-8")

    assert query_hardware(tmp_path) == AmdHardware(("gfx1103",))


def test_query_hardware_without_the_driver_is_none(tmp_path):
    """Check that a missing topology folder means no AMD card."""
    assert query_hardware(tmp_path / "absent") is None


def test_fingerprint_changes_with_the_cards():
    """Check that adding a card changes the fingerprint."""
    assert (AmdHardware(("gfx1103",)).fingerprint()
            != AmdHardware(("gfx1030", "gfx1103")).fingerprint())
