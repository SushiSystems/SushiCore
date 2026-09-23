# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for tool probing."""

from __future__ import annotations

from sushicore.provision import probe


def test_classify_prefers_a_discrete_adapter():
    adapters = "Intel(R) UHD Graphics 770\nNVIDIA GeForce RTX 4070\n"
    assert probe.classify_display_adapters(adapters) == "nvidia"


def test_integrated_only_falls_back_to_its_vendor():
    assert probe.classify_display_adapters("Intel(R) UHD Graphics 770\n") == "intel"


def test_binary_works_rejects_a_missing_command():
    assert probe.binary_works("sushi-no-such-binary-xyz") is False


def test_tools_dir_follows_the_root(provision_home):
    assert probe._tools_dir() == provision_home.resolve() / "tools"
