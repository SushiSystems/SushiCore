# test_target_plans.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""How a dispatch finds the plan its target registered."""

from __future__ import annotations

import sys

import pytest

from sushicore.provision.target import K_LINUX, K_WINDOWS, LinuxTarget, WindowsTarget
from sushicore.provision.target_plans import TargetPlanError, TargetPlans


@pytest.mark.small
def test_a_registered_plan_is_returned_for_its_target():
    """Check that the plan registered for a target's name is the one the lookup returns."""
    plans: TargetPlans[str] = TargetPlans("sushicore.provision.probe_plans")
    plans.register(K_LINUX, "linux plan")

    assert plans.plan_for(LinuxTarget()) == "linux plan"


@pytest.mark.small
def test_a_second_plan_for_one_target_is_refused():
    """Check that registering two plans for one target raises."""
    plans: TargetPlans[str] = TargetPlans("sushicore.provision.probe_plans")
    plans.register(K_WINDOWS, "first")

    with pytest.raises(TargetPlanError):
        plans.register(K_WINDOWS, "second")


@pytest.mark.small
def test_a_target_without_a_plan_is_refused(tmp_path, monkeypatch):
    """Check that a lookup for a target no module registered raises."""
    (tmp_path / "empty_plans").mkdir()
    (tmp_path / "empty_plans" / "__init__.py").write_text("", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    plans: TargetPlans[str] = TargetPlans("empty_plans")

    with pytest.raises(TargetPlanError):
        plans.plan_for(WindowsTarget())
    sys.modules.pop("empty_plans", None)


@pytest.mark.small
def test_a_new_plan_module_registers_itself_with_no_edit_to_the_registry(tmp_path, monkeypatch):
    """Check that a module dropped into the plan package is found by the first lookup."""
    package = tmp_path / "added_plans"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "windows.py").write_text(
        "from sushicore.provision.target import K_WINDOWS\n"
        "from added_plans_registry import PLANS\n"
        "PLANS.register(K_WINDOWS, 'dropped in')\n", encoding="utf-8")
    (tmp_path / "added_plans_registry.py").write_text(
        "from sushicore.provision.target_plans import TargetPlans\n"
        "PLANS = TargetPlans('added_plans')\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    from added_plans_registry import PLANS

    assert PLANS.plan_for(WindowsTarget()) == "dropped in"
    for name in ("added_plans", "added_plans.windows", "added_plans_registry"):
        sys.modules.pop(name, None)
