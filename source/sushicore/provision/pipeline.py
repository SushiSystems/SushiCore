# pipeline.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Runs an ordered list of installer steps against one shared context.

``InstallContext``, ``Step``, ``StepResult`` and ``ToolchainSelection`` are re-exported for the
module CLIs that import them from here.
"""

from __future__ import annotations

from typing import Any

from .default_console import console_or_default
from .install_context import InstallContext
from .step import Step
from .step_result import StepResult
from .toolchain_selection import ToolchainSelection  # noqa: F401


class InstallPipeline:
    """Runs an ordered list of steps, stopping on the first failure."""

    def __init__(self, steps: list[Step], console: Any = None) -> None:
        """Hold the ordered *steps* this pipeline runs and the *console* it reports through."""
        console = console_or_default(console, "InstallPipeline")
        self._steps = steps
        self._console = console

    @property
    def steps(self) -> list[Step]:
        """Return a copy of the ordered steps this pipeline runs."""
        return list(self._steps)

    def run(self, ctx: InstallContext, show_progress: bool = True) -> bool:
        """Execute every step in order. Return True if none failed.

        Each step is reported once to a human, as a header and a progress line, and once to a
        program as a ``progress`` event.

        Args:
            ctx: The shared context steps read and populate.
            show_progress: Ignored. It once drew a bar that repeated the progress line; callers that
                still pass it keep working.
        """
        del show_progress
        total = len(self._steps)
        for index, step in enumerate(self._steps, start=1):
            self._console.header(f"setup: {step.name}")
            self._console.progress(step.name, index, total, index / total)
            result = step.run(ctx)
            if result is StepResult.FAILED:
                self._console.error(f"Step '{step.name}' failed; stopping pipeline.")
                return False
            if result is StepResult.SKIPPED:
                self._console.info(f"Step '{step.name}' skipped (nothing to do).")
            else:
                self._console.success(f"Step '{step.name}' done.")
        self._report_warnings(ctx)
        return True

    def _report_warnings(self, ctx: InstallContext) -> None:
        """Re-print any non-fatal problems after the progress bar clears."""
        if not ctx.warnings:
            return
        self._console.warn(f"Completed with {len(ctx.warnings)} warning(s):")
        for message in ctx.warnings:
            self._console.warn(f"  - {message}")
