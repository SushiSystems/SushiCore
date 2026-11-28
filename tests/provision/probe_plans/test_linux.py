# test_linux.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the Linux probe plan records in the local config."""

from __future__ import annotations

import pytest

from sushicore.provision.config import ProvisionSettings
from sushicore.provision.dependency_home import DependencyHome
from sushicore.provision.probe_plans import linux as linux_plan
from sushicore.provision.probe_plans.linux import LinuxProbePlan


@pytest.fixture
def offline_plan(tmp_path, monkeypatch):
    """Return a Linux plan that finds no compiler on PATH and searches an empty home."""
    monkeypatch.setattr(linux_plan.shutil, "which", lambda _name: None)
    return LinuxProbePlan(home=DependencyHome(lambda: tmp_path / "home"))


@pytest.mark.medium
def test_a_configured_oneapi_root_with_setvars_is_recorded(tmp_path, offline_plan):
    """Check that a oneAPI root holding setvars.sh reaches the local config."""
    (tmp_path / "setvars.sh").write_text("", encoding="utf-8")
    cfg = ProvisionSettings(platform="linux", oneapi_root=str(tmp_path))

    values = offline_plan.resolve_local_config(cfg)

    assert values["oneapi_root"] == str(tmp_path)


@pytest.mark.medium
def test_a_configured_oneapi_root_without_setvars_is_left_out(tmp_path, offline_plan):
    """Check that a oneAPI root with no setvars.sh does not reach the local config."""
    cfg = ProvisionSettings(platform="linux", oneapi_root=str(tmp_path))

    assert "oneapi_root" not in offline_plan.resolve_local_config(cfg)


@pytest.mark.small
def test_the_probe_lookup_builds_the_plan_with_the_home_it_is_given(tmp_path, monkeypatch):
    """Check that find_sycl_compiler's plan searches the given home, not the default one."""
    from sushicore.provision import probe
    from sushicore.provision.config import ProvisionSettings
    from sushicore.provision.probe_plan import PROBE_PLANS
    from sushicore.provision.target import target_of

    held = DependencyHome(lambda: tmp_path / "held-root")
    cfg = ProvisionSettings(platform="linux")

    seen = []
    monkeypatch.setattr(linux_plan, "discover_installed_toolchains",
                        lambda _cfg, _values, *, home: seen.append(home))
    PROBE_PLANS.plan_for(target_of(cfg), home=held).resolve_local_config(cfg)
    assert seen == [held]
    assert probe.find_sycl_compiler(cfg, home=held) is not None
