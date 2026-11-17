# test_probe_plan.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Which probe plan each target finds its tools through."""

from __future__ import annotations

import pytest

from sushicore.provision.probe_plan import PROBE_PLANS
from sushicore.provision.probe_plans.linux import LinuxProbePlan
from sushicore.provision.probe_plans.windows import WindowsProbePlan
from sushicore.provision.target import LinuxTarget, WindowsTarget


@pytest.mark.small
@pytest.mark.parametrize(("target", "plan"), [
    (WindowsTarget(), WindowsProbePlan), (LinuxTarget(), LinuxProbePlan),
], ids=["windows", "linux"])
def test_each_target_probes_through_its_own_plan(target, plan):
    """Check that the registry hands each target the probe plan of its own module."""
    assert type(PROBE_PLANS.plan_for(target)) is plan
