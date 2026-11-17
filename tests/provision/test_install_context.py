# test_install_context.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the state one installer run shares across its steps."""

from __future__ import annotations

import pytest

from sushicore.provision.config import ProvisionSettings
from sushicore.provision.install_context import InstallContext
from sushicore.provision.toolchain_selection import ToolchainSelection


@pytest.mark.small
def test_gpu_follows_the_selection():
    """Check that the context says whether the run provisions the GPU from its selection."""
    cfg = ProvisionSettings()
    assert InstallContext(cfg=cfg).gpu is False
    assert InstallContext(cfg=cfg, selection=ToolchainSelection(gpu=True)).gpu is True


@pytest.mark.small
def test_two_contexts_share_no_collection():
    """Check that each context starts with its own warnings, detected, installed and paths."""
    cfg = ProvisionSettings()
    first, second = InstallContext(cfg=cfg), InstallContext(cfg=cfg)
    first.warnings.append("w")
    first.detected["cmake"] = True
    assert second.warnings == []
    assert second.detected == {}
