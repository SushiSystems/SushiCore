# configure_step.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Writes the probed tool paths and the active toolchain to a config sink."""

from __future__ import annotations

from typing import Any

from .default_console import console_or_default
from .pipeline import InstallContext, Step, StepResult
from .sinks import ConfigSink, render_local_config
from .machine_actions import MachineActions


class ConfigureStep(Step):
    """Probe installed tools and write them through a :class:`ConfigSink`."""

    name = "configure"

    def __init__(self, sink: ConfigSink, *, console: Any = None,
                 actions: MachineActions | None = None) -> None:
        """Bind this step to the sink its probed values and active toolchain are written to.

        Args:
            console: The console the step prints through.
            actions: The machine calls; the real ones when omitted.
        """
        console = console_or_default(console, "ConfigureStep")
        self._sink = sink
        self._console = console
        self._actions = actions or MachineActions()

    def run(self, ctx: InstallContext) -> StepResult:
        """Probe machine-specific tool paths and write them and the active toolchain to the sink."""
        self._actions.refresh_path()
        values = self._actions.resolve_config(ctx.cfg, gpu=ctx.gpu)
        ctx.resolved_paths = values

        if ctx.dry_run:
            if ctx.active_toolchain:
                self._console.info(f"(dry-run) would set active toolchain to "
                             f"'{ctx.active_toolchain}'.")
            if values:
                self._console.info(f"(dry-run) would write {self._sink.target}:")
                self._console.console.print(
                    render_local_config(ctx.cfg.platform, values), markup=False)
            return StepResult.OK

        if not values and not ctx.active_toolchain:
            self._console.info("No machine-specific paths to write; defaults suffice.")
            return StepResult.SKIPPED

        if values:
            backup = self._sink.backup()
            if backup is not None:
                self._console.info(f"Backed up existing config to {backup.name}")
            written = self._sink.write_paths(ctx.cfg.platform, values)
            self._console.success(f"Wrote {written}")

        if ctx.active_toolchain:
            self._sink.write_tool({"toolchain": ctx.active_toolchain})
            self._console.success(f"Active SYCL toolchain set to '{ctx.active_toolchain}'.")
        return StepResult.OK
