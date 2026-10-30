# doctor_command.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Runs a module's readiness checks and reports them."""

from __future__ import annotations

from typing import Optional, Sequence

from ..deps_fragment import read_present
from . import module_plan
from .checks import python_check
from .doctor import Check, Doctor
from .module_checks import ModuleState, doctor_checks
from .module_provision import ModuleProvision
from .outcome import Outcome, failed
from .packages import IPackageManager


def _report(checks: Sequence[Check], groups: Optional[set[str]], console: object) -> Outcome:
    """Runs *checks*, draws the report table on *console*, and returns how the run ended."""
    doctor = Doctor(checks)
    report = doctor.run(groups)
    doctor.render_table(report, console)
    return Outcome(report.exit_code() == 0, report.exit_code(), report.payload())


def run_doctor(module: ModuleProvision, groups: Optional[set[str]],
               managers: list[IPackageManager] | None = None) -> Outcome:
    """Runs this module's checks, draws the report, and returns how the run ended.

    Args:
        managers: The package managers a ``setup`` run already built; built here when None.
    """
    console = module.console()
    if module.is_binary():
        return _report([python_check()] + module.extra_checks(), groups, console)
    cfg = module.load_config()
    root = module.project_root()
    try:
        found = module_plan.closure_for(module, root)
        own = read_present(root / module_plan.fragment_of(module, root))
    except ValueError as exc:
        console.error(str(exc))
        return failed()
    if managers is None:
        managers = module_plan.managers_for(cfg)
    state = ModuleState(cfg=cfg, root=root, owner=module.profile.key,
                        program=module.profile.program, own=own,
                        source=module_plan.source_for(module, root, found), missing=found.missing)
    checks = doctor_checks(state, managers, module.git()) + module.extra_checks()
    return _report(checks, groups, console)
