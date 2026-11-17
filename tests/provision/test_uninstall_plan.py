# test_uninstall_plan.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Which uninstall plan each target removes its packages through."""

from __future__ import annotations

import pytest

from sushicore.provision.target import LinuxTarget, WindowsTarget
from sushicore.provision.uninstall_plan import UNINSTALL_PLANS
from sushicore.provision.uninstall_plans.linux import LinuxUninstallPlan
from sushicore.provision.uninstall_plans.windows import WindowsUninstallPlan


@pytest.mark.small
@pytest.mark.parametrize(("target", "plan"), [
    (WindowsTarget(), WindowsUninstallPlan), (LinuxTarget(), LinuxUninstallPlan),
], ids=["windows", "linux"])
def test_each_target_removes_its_packages_through_its_own_plan(target, plan):
    """Check that the registry hands each target the uninstall plan of its own module."""
    assert type(UNINSTALL_PLANS.plan_for(target)) is plan
