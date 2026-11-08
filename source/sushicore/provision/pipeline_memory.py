# pipeline_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A pipeline step that answers a scripted result and records that it ran."""

from __future__ import annotations

from .pipeline import InstallContext, Step, StepResult


class ScriptedStep(Step):
    """Answers the result it was given and appends its name to a shared log when it runs.

    Args:
        name: The step's name, as the pipeline reports it.
        result: What the step answers.
        log: The list every step of one test appends its name to, in run order.
        warnings: Messages the step adds to the context's warnings when it runs.
    """

    def __init__(self, name: str, result: StepResult, log: list[str],
                 warnings: tuple[str, ...] = ()) -> None:
        """Store the name, the scripted result, the shared log and the warnings."""
        self.name = name
        self._result = result
        self._log = log
        self._warnings = warnings

    def run(self, ctx: InstallContext) -> StepResult:
        """Log the step's name, add its warnings to *ctx* and return the scripted result."""
        self._log.append(self.name)
        ctx.warnings.extend(self._warnings)
        return self._result
