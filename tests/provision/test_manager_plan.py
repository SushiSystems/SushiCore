# test_manager_plan.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Which manager plan each target builds its package managers from."""

from __future__ import annotations

import pytest

from sushicore.provision.manager_plan import MANAGER_PLANS
from sushicore.provision.manager_plans.linux import LinuxManagerPlan
from sushicore.provision.manager_plans.windows import WindowsManagerPlan
from sushicore.provision.target import LinuxTarget, WindowsTarget


@pytest.mark.small
@pytest.mark.parametrize(("target", "plan"), [
    (WindowsTarget(), WindowsManagerPlan), (LinuxTarget(), LinuxManagerPlan),
], ids=["windows", "linux"])
def test_each_target_builds_its_managers_from_its_own_plan(target, plan):
    """Check that the registry hands each target the manager plan of its own module."""
    assert type(MANAGER_PLANS.plan_for(target)) is plan
