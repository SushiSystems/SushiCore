# test_cuda_hardware.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
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


def test_parse_hardware_without_a_ceiling_is_none():
    """Check that a banner with no CUDA version yields no record."""
    assert parse_hardware("8.9\n", "NVIDIA-SMI has failed") is None


def test_parse_hardware_without_a_card_is_none():
    """Check that no compute capability yields no record."""
    assert parse_hardware("", K_BANNER) is None


def test_query_hardware_without_a_driver_is_none():
    """Check that a missing nvidia-smi is reported as no hardware."""
    def missing(command):
        """Fail as a missing binary does."""
        raise FileNotFoundError(command[0])

    assert query_hardware(missing) is None


def test_query_hardware_with_a_failing_driver_is_none():
    """Check that nvidia-smi exiting non-zero is reported as no hardware."""
    def failing(command):
        """Fail as a broken driver does."""
        raise subprocess.CalledProcessError(9, command)

    assert query_hardware(failing) is None


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
