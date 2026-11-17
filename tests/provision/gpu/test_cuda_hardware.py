# test_cuda_hardware.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The driver's report becomes the cards' architectures and its CUDA ceiling."""

from __future__ import annotations

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.proc_memory import RecordingRunner
from sushicore.provision.gpu.cuda_hardware import NvidiaHardware, parse_hardware, query_hardware


pytestmark = pytest.mark.small

K_BANNER = "| NVIDIA-SMI 592.82   Driver Version: 592.82   CUDA Version: 13.1     |"


def test_parse_hardware_collapses_identical_cards_and_sorts_numerically():
    """Check that two equal cards count once and 120 sorts after 89."""
    hardware = parse_hardware("12.0\n8.9\n8.9\n", K_BANNER)

    assert hardware == NvidiaHardware(("89", "120"), (13, 1))


@pytest.mark.parametrize(("capability", "banner"), [
    ("8.9\n", "NVIDIA-SMI has failed"),
    ("", K_BANNER),
], ids=["without-a-ceiling", "without-a-card"])
def test_parse_hardware_with_a_missing_part_is_none(capability, banner):
    """Check that a banner with no CUDA version, or no compute capability, yields no record."""
    assert parse_hardware(capability, banner) is None


def _runner() -> RecordingRunner:
    """Return a runner that records commands and starts no process."""
    return RecordingRunner(RecordingConsole())


@pytest.mark.parametrize("runner", [
    _runner().script_missing(),
    _runner().script(9),
], ids=["no-driver", "failing-driver"])
def test_query_hardware_with_a_driver_that_cannot_answer_is_none(runner):
    """Check that a missing nvidia-smi, or one exiting non-zero, is reported as no hardware."""
    assert query_hardware(runner) is None


def test_query_hardware_reads_both_commands():
    """Check that the capability query and the banner are combined."""
    runner = _runner().script(0, ("8.9",)).script(0, (K_BANNER,))

    assert query_hardware(runner) == NvidiaHardware(("89",), (13, 1))
    assert [c.argv for c in runner.commands] == [
        ("nvidia-smi", "--query-gpu=compute_cap", "--format=csv,noheader"), ("nvidia-smi",)]


def test_fingerprint_changes_with_the_driver_ceiling():
    """Check that a driver update alone changes the fingerprint."""
    assert (NvidiaHardware(("89",), (13, 1)).fingerprint()
            != NvidiaHardware(("89",), (13, 2)).fingerprint())
