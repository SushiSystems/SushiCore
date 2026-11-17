# test_gpu_vendor.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for how the GPU vendor is named from display adapters."""

from __future__ import annotations

import pytest

from sushicore.provision import gpu_vendor


@pytest.mark.small
def test_classify_prefers_a_discrete_adapter():
    """Check that classification prefers a discrete adapter."""
    adapters = "Intel(R) UHD Graphics 770\nNVIDIA GeForce RTX 4070\n"
    assert gpu_vendor.classify_display_adapters(adapters) == "nvidia"


@pytest.mark.small
def test_integrated_only_falls_back_to_its_vendor():
    """Check that integrated-only falls back to its vendor."""
    assert gpu_vendor.classify_display_adapters("Intel(R) UHD Graphics 770\n") == "intel"


@pytest.mark.small
def test_an_intel_arc_a_series_line_is_discrete_not_integrated():
    """Check that an Intel Arc A-series adapter is not reported as integrated."""
    assert gpu_vendor.is_integrated_adapter("Intel(R) Arc(TM) A770 Graphics") is False


@pytest.mark.small
def test_no_known_adapter_names_no_vendor():
    """Check that adapter text naming no known vendor classifies as none."""
    assert gpu_vendor.classify_display_adapters("Some Unknown Display 1\n") == "none"


@pytest.mark.small
def test_detect_prefers_the_vendor_tool_on_path(monkeypatch):
    """Check that an nvidia-smi on PATH names nvidia without reading any adapter."""
    monkeypatch.setattr(gpu_vendor.shutil, "which",
                        lambda name: "/bin/nvidia-smi" if name == "nvidia-smi" else None)
    assert gpu_vendor.detect_gpu_vendor() == "nvidia"
