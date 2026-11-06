# test_cuda_selection.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The newest release the driver runs and the compiler builds every card for is chosen."""

from __future__ import annotations

import pytest

from sushicore.provision.gpu.cuda_hardware import NvidiaHardware
from sushicore.provision.gpu.cuda_selection import select_release
from sushicore.provision.gpu.cuda_selection_memory import TableArchitectureProbe


pytestmark = pytest.mark.small

K_VERSIONS = [(12, 6, 3), (12, 9, 1), (13, 0, 2), (13, 1, 2), (13, 4, 3)]
K_ARCHS = {12: frozenset({"61", "75", "89"}), 13: frozenset({"75", "89", "120"})}


_PROBE = TableArchitectureProbe(K_ARCHS)


@pytest.mark.parametrize(("ceiling", "expected"), [
    ((13, 1), (13, 1, 2)),
    ((12, 6), (12, 6, 3)),
], ids=["13.1-driver", "12.6-driver"])
def test_the_driver_ceiling_excludes_newer_releases(ceiling, expected):
    """Check that a driver is never given a release newer than its CUDA version."""
    assert select_release(NvidiaHardware(("89",), ceiling), K_VERSIONS, _PROBE) == expected


def test_a_pascal_card_walks_back_one_major():
    """Check that sm_61 skips 13.x and lands on the newest 12.x."""
    assert select_release(NvidiaHardware(("61", "89"), (13, 4)), K_VERSIONS, _PROBE) == (12, 9, 1)


def test_no_fitting_release_is_none():
    """Check that a card no compiler builds for yields no release."""
    assert select_release(NvidiaHardware(("35",), (13, 4)), K_VERSIONS, _PROBE) is None
