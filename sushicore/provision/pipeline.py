# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Pipeline core: the ``Step`` contract, shared context, and the runner."""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields

from sushicore.provision._output import console

from .config import ProvisionConfig


class StepResult(enum.Enum):
    """Outcome of a single pipeline step."""

    OK = "ok"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True)
class ToolchainSelection:
    """Which of the four customizable toolchain components a run provisions."""

    install_intel_llvm: bool = False
    install_acpp: bool = False
    oneapi: bool = False
    gpu: bool = False

    def as_dict(self) -> dict[str, bool]:
        """Return the selection as field name -> value."""
        return {f.name: bool(getattr(self, f.name)) for f in fields(self)}

    def merged(self, overrides: dict[str, bool]) -> "ToolchainSelection":
        """Return a copy with the known field names in *overrides* applied."""
        values = self.as_dict()
        values.update({k: bool(v) for k, v in overrides.items() if k in values})
        return ToolchainSelection(**values)


@dataclass
class InstallContext:
    """State shared across steps for one installer run."""

    cfg: ProvisionConfig
    selection: ToolchainSelection = field(default_factory=ToolchainSelection)
    #: The module name recorded in the registry.
    consumer: str = ""
    #: The command a user types to re-run provisioning.
    program: str = "hub"
    dry_run: bool = False
    everything: bool = False
    #: The toolchain ConfigureStep pins as the default, or None to leave it.
    active_toolchain: str | None = None
    #: Whether to re-download a toolchain that is already present.
    refresh_toolchains: bool = False
    #: Whether the user has consented to the heavy Windows LLVM download.
    assume_acpp_llvm: bool = False
    #: The discrete-GPU vendor: nvidia, amd, intel, or none.
    gpu_vendor: str = ""
    #: Non-fatal problems surfaced by any step.
    warnings: list[str] = field(default_factory=list)
    #: Populated by DetectStep: tool/dependency name -> present?
    detected: dict[str, bool] = field(default_factory=dict)
    #: Populated by InstallDepsStep: package names actually installed this run.
    installed: list[str] = field(default_factory=list)
    #: Populated by ConfigureStep: config field name -> resolved absolute path.
    resolved_paths: dict[str, str] = field(default_factory=dict)

    @property
    def gpu(self) -> bool:
        """Report whether this run provisions the GPU toolkit."""
        return self.selection.gpu


class Step(ABC):
    """One unit of installer work."""

    #: Human-readable name, shown in the pipeline log.
    name: str = "step"

    @abstractmethod
    def run(self, ctx: InstallContext) -> StepResult:  # pragma: no cover - abstract
        """Execute this step against *ctx* and report its outcome."""
        raise NotImplementedError


class InstallPipeline:
    """Runs an ordered list of steps, stopping on the first failure."""

    def __init__(self, steps: list[Step]) -> None:
        """Hold the ordered *steps* this pipeline runs."""
        self._steps = steps

    @property
    def steps(self) -> list[Step]:
        """Return a copy of the ordered steps this pipeline runs."""
        return list(self._steps)

    def run(self, ctx: InstallContext, show_progress: bool = True) -> bool:
        """Execute every step in order. Return True if none failed.

        Args:
            ctx: The shared context steps read and populate.
            show_progress: Whether to draw the setup progress bar.
        """
        total = len(self._steps)
        if not show_progress:
            for index, step in enumerate(self._steps, start=1):
                console.progress(step.name, index, total, index / total)
                result = step.run(ctx)
                if result is StepResult.FAILED:
                    console.error(f"Step '{step.name}' failed; stopping.")
                    return False
            self._report_warnings(ctx)
            return True

        from rich.progress import (
            BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console.console,
            transient=False,
        ) as progress:
            task = progress.add_task("[header]Starting Setup...", total=total)

            for index, step in enumerate(self._steps, start=1):
                progress.update(
                    task,
                    description=f"[header]Running Setup...[/header] [warn]({step.name})[/warn]")
                console.header(f"setup: {step.name}")
                console.progress(step.name, index, total, index / total)
                result = step.run(ctx)
                if result is StepResult.FAILED:
                    progress.update(task, description=f"[error]Setup failed at '{step.name}'[/error]")
                    console.error(f"Step '{step.name}' failed; stopping pipeline.")
                    return False
                if result is StepResult.SKIPPED:
                    console.info(f"Step '{step.name}' skipped (nothing to do).")
                else:
                    console.success(f"Step '{step.name}' done.")
                progress.advance(task)

            progress.update(task, description="[success]Setup Complete![/success]")
        self._report_warnings(ctx)
        return True

    @staticmethod
    def _report_warnings(ctx: InstallContext) -> None:
        """Re-print any non-fatal problems after the progress bar clears."""
        if not ctx.warnings:
            return
        console.warn(f"Completed with {len(ctx.warnings)} warning(s):")
        for message in ctx.warnings:
            console.warn(f"  - {message}")
