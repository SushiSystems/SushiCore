# test_install_deps_plan.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Which install plan each target runs."""

from __future__ import annotations

import pytest

from sushicore.provision.install_deps_plan import INSTALL_PLANS
from sushicore.provision.install_deps_plans.linux import LinuxInstallPlan
from sushicore.provision.install_deps_plans.windows import WindowsInstallPlan
from sushicore.provision.target import LinuxTarget, WindowsTarget


@pytest.mark.small
@pytest.mark.parametrize(("target", "plan"), [
    (WindowsTarget(), WindowsInstallPlan), (LinuxTarget(), LinuxInstallPlan),
], ids=["windows", "linux"])
def test_each_target_runs_its_own_install_plan(target, plan):
    """Check that the registry hands each target the install plan of its own module."""
    assert type(INSTALL_PLANS.plan_for(target)) is plan
