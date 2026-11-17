# test_llvm_plan.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Which LLVM plan each target supplies the acpp build's LLVM through."""

from __future__ import annotations

import pytest

from sushicore.provision.llvm_plan import LLVM_PLANS
from sushicore.provision.llvm_plans.linux import LinuxLlvmPlan
from sushicore.provision.llvm_plans.windows import WindowsLlvmPlan
from sushicore.provision.target import LinuxTarget, WindowsTarget


@pytest.mark.small
@pytest.mark.parametrize(("target", "plan"), [
    (WindowsTarget(), WindowsLlvmPlan), (LinuxTarget(), LinuxLlvmPlan),
], ids=["windows", "linux"])
def test_each_target_supplies_llvm_through_its_own_plan(target, plan):
    """Check that the registry hands each target the LLVM plan of its own module."""
    assert type(LLVM_PLANS.plan_for(target)) is plan
