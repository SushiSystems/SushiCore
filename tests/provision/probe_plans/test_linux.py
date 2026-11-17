# test_linux.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the Linux probe plan records in the local config."""

from __future__ import annotations

import pytest

from sushicore.provision.config import ProvisionSettings
from sushicore.provision.probe_plans.linux import LinuxProbePlan


@pytest.mark.medium
def test_a_configured_oneapi_root_with_setvars_is_recorded(tmp_path):
    """Check that a oneAPI root holding setvars.sh reaches the local config."""
    (tmp_path / "setvars.sh").write_text("", encoding="utf-8")
    cfg = ProvisionSettings(platform="linux", oneapi_root=str(tmp_path))

    values = LinuxProbePlan().resolve_local_config(cfg)

    assert values["oneapi_root"] == str(tmp_path)


@pytest.mark.medium
def test_a_configured_oneapi_root_without_setvars_is_left_out(tmp_path):
    """Check that a oneAPI root with no setvars.sh does not reach the local config."""
    cfg = ProvisionSettings(platform="linux", oneapi_root=str(tmp_path))

    assert "oneapi_root" not in LinuxProbePlan().resolve_local_config(cfg)
