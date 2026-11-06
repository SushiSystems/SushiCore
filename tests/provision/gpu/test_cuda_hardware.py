# test_cuda_hardware.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The driver's report becomes the cards' architectures and its CUDA ceiling."""

from __future__ import annotations

import subprocess

import pytest

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


def _failing_with(error: Exception):
    """Return a run function that raises *error*, as a missing or broken nvidia-smi does."""
    def run(command):
        """Raise *error*."""
        raise error
    return run


@pytest.mark.parametrize("error", [
    FileNotFoundError("nvidia-smi"),
    subprocess.CalledProcessError(9, ["nvidia-smi"]),
], ids=["no-driver", "failing-driver"])
def test_query_hardware_with_a_driver_that_cannot_answer_is_none(error):
    """Check that a missing nvidia-smi, or one exiting non-zero, is reported as no hardware."""
    assert query_hardware(_failing_with(error)) is None


def test_query_hardware_reads_both_commands():
    """Check that the capability query and the banner are combined."""
    outputs = {"--query-gpu=compute_cap": "8.9\n", "": K_BANNER}

    def run(command):
        """Answer by the command's first argument."""
        return outputs[command[1] if len(command) > 1 else ""]

    assert query_hardware(run) == NvidiaHardware(("89",), (13, 1))


def test_fingerprint_changes_with_the_driver_ceiling():
    """Check that a driver update alone changes the fingerprint."""
    assert (NvidiaHardware(("89",), (13, 1)).fingerprint()
            != NvidiaHardware(("89",), (13, 2)).fingerprint())
