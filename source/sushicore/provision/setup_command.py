# setup_command.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Provisions what a module needs to build, then reports its readiness."""

from __future__ import annotations

from typing import Sequence

from ..deps_fragment import pins_at
from . import home, module_plan, probe, selection, sushi_setup
from .doctor_command import run_doctor
from .lock import LockTimeout, ProvisionLock
from .module_provision import ModuleProvision
from .outcome import K_EXIT_USAGE, Outcome, failed
from .pipeline import InstallContext, InstallPipeline
from .sinks import ModuleSink
from .steps import ConfigureStep, DetectStep, InstallDepsStep

#: Header written atop a module's ``config.local.toml``.
K_SINK_HEADER = [
    "# Auto-generated. Machine-specific tool paths for this module.",
    "# Safe to edit; re-running `setup` backs this up first.",
]

#: Seconds ``setup`` waits for another process's ``ProvisionLock`` before giving up.
K_LOCK_TIMEOUT = 600.0


def run_setup(module: ModuleProvision, *, dry_run: bool, yes: bool,
              toolchains: Sequence[str], gpu: bool) -> Outcome:
    """Provisions *module*'s closure, then reports readiness, and returns how the run ended."""
    console = module.console()
    root = module.project_root()
    cfg = module.load_config()
    try:
        pins = pins_at(root / module.fragment)
    except ValueError as exc:
        console.error(str(exc))
        return failed()
    fetch = InstallContext(cfg=cfg, consumer=module.profile.key,
                           program=module.profile.program, dry_run=dry_run)
    if not sushi_setup.prepare(fetch, root, pins, module.git(), K_LOCK_TIMEOUT):
        return failed()
    try:
        found = module_plan.closure_for(module, root)
    except ValueError as exc:
        console.error(str(exc))
        return failed()
    if found.missing:
        for name, wanted_by in found.missing:
            console.error(module_plan.missing_module_message(name, wanted_by))
        return failed(K_EXIT_USAGE)
    source = module_plan.source_for(module, root, found)
    try:
        chosen = selection.derive(source, probe.toolchain_presence(cfg),
                                  requested=toolchains, gpu=gpu)
    except ValueError as exc:
        console.error(str(exc))
        return failed(K_EXIT_USAGE)
    managers = module_plan.managers_for(cfg)
    pipeline = InstallPipeline([
        DetectStep(source, managers),
        InstallDepsStep(source, managers),
        ConfigureStep(ModuleSink(root / module.config_dir, K_SINK_HEADER)),
    ])
    ctx = InstallContext(
        cfg=cfg,
        selection=chosen,
        consumer=module.profile.key,
        program=module.profile.program,
        dry_run=dry_run,
        assume_acpp_llvm=yes,
    )
    try:
        with ProvisionLock(home.root() / ".lock", timeout=K_LOCK_TIMEOUT):
            ok = pipeline.run(ctx)
    except LockTimeout as exc:
        console.error(str(exc))
        return failed()
    if not ok:
        return failed()
    return run_doctor(module, None, managers)
