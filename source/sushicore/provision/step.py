# step.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The contract one unit of installer work implements."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .install_context import InstallContext
from .step_result import StepResult


class Step(ABC):
    """One unit of installer work."""

    #: Human-readable name, shown in the pipeline log.
    name: str = "step"

    @abstractmethod
    def run(self, ctx: InstallContext) -> StepResult:  # pragma: no cover - abstract
        """Execute this step against *ctx* and report its outcome."""
        raise NotImplementedError
