# test_cuda_selection.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The newest release the driver runs and the compiler builds every card for is chosen."""

from __future__ import annotations

from sushicore.provision.gpu.cuda_hardware import NvidiaHardware
from sushicore.provision.gpu.cuda_selection import select_release

K_VERSIONS = [(12, 6, 3), (12, 9, 1), (13, 0, 2), (13, 1, 2), (13, 4, 3)]
K_ARCHS = {12: frozenset({"61", "75", "89"}), 13: frozenset({"75", "89", "120"})}


class _Probe:
    """Answers per major and records which releases were asked."""

    def __init__(self) -> None:
        """Start with no questions asked."""
        self.asked: list[tuple[int, ...]] = []

    def __call__(self, version):
        """Return the architectures of the release's major."""
        self.asked.append(version)
        return K_ARCHS[version[0]]


def test_the_driver_ceiling_excludes_newer_releases():
    """Check that a 13.1 driver gets 13.1.2, not 13.4.3."""
    probe = _Probe()

    chosen = select_release(NvidiaHardware(("89",), (13, 1)), K_VERSIONS, probe)

    assert chosen == (13, 1, 2)
    assert probe.asked == [(13, 1, 2)]


def test_a_pascal_card_walks_back_one_major():
    """Check that sm_61 skips 13.x after one question and lands on the newest 12.x."""
    probe = _Probe()

    chosen = select_release(NvidiaHardware(("61", "89"), (13, 4)), K_VERSIONS, probe)

    assert chosen == (12, 9, 1)
    assert probe.asked == [(13, 4, 3), (12, 9, 1)]


def test_an_old_driver_gets_an_old_release():
    """Check that a 12.6 driver is never given a 12.9 compiler."""
    chosen = select_release(NvidiaHardware(("89",), (12, 6)), K_VERSIONS, _Probe())

    assert chosen == (12, 6, 3)


def test_no_fitting_release_is_none():
    """Check that a card no compiler builds for yields no release."""
    assert select_release(NvidiaHardware(("35",), (13, 4)), K_VERSIONS, _Probe()) is None
