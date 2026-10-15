# test_backend.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests what every GPU backend spec shares."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from sushicore.provision.gpu.backend import NotProvided

from sushicore.provision.gpu.cuda import CUDA

from sushicore.provision.gpu.level_zero import LEVEL_ZERO

from sushicore.provision.gpu.rocm import ROCM



pytestmark = pytest.mark.medium



@pytest.mark.parametrize("spec", [CUDA, ROCM, LEVEL_ZERO])
def test_every_backend_reports_not_provided_on_darwin(spec, recording_console):
    """Check that every backend reports not provided on darwin."""
    cfg = SimpleNamespace(platform="darwin")

    assert spec.locator.locate(cfg) is None
    assert isinstance(spec.locator._for(cfg), NotProvided)
    assert spec.locator.provision(cfg, dry_run=True) is True
