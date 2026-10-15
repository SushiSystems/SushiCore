# test_gpu_hardware.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the protocol every vendor's hardware report follows."""

import pytest

from sushicore.provision.gpu.gpu_hardware import GpuHardware

pytestmark = pytest.mark.small


class _Cards:
    def fingerprint(self) -> str:
        return "sm_89/580.1"

    def describe(self) -> str:
        return "sm_89"


class _Half:
    def fingerprint(self) -> str:
        return ""


def test_an_object_with_both_methods_is_gpu_hardware():
    assert isinstance(_Cards(), GpuHardware)


def test_an_object_without_describe_is_not():
    assert not isinstance(_Half(), GpuHardware)
