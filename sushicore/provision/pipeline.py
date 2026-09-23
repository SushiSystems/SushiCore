# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Pipeline core: the ``Step`` contract, shared context, and the runner.

These are the abstractions the rest of the installer depends on. Concrete steps
live with each consumer; concrete package managers and dependency sources live
in their own modules. Nothing here imports a concrete implementation, which
keeps the dependency direction pointing at the abstractions (Dependency
Inversion).
"""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields

from ._output import console
from .config import ProvisionConfig


class StepResult(enum.Enum):
    """Outcome of a single pipeline step.

    ``SKIPPED`` is distinct from ``OK`` so the summary can say "nothing to do"
    versus "did work"; both let the pipeline continue. ``FAILED`` stops it.
    """

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
    """State shared across steps for one installer run.

    Earlier steps populate fields that later steps read (e.g. ``DetectStep``
    fills ``detected``; ``ConfigureStep`` fills ``resolved_paths``). Keeping the
    shared state in one object means steps stay decoupled from one another —
    they talk through the context, never directly.
    """

    cfg: ProvisionConfig
    selection: ToolchainSelection = field(default_factory=ToolchainSelection)
    #: The module name recorded in the registry.
    consumer: str = ""
    dry_run: bool = False
    everything: bool = False
    # Which SYCL toolchain ConfigureStep pins as the default for subsequent
    # builds (None => leave the existing choice alone).
    active_toolchain: str | None = None
    # Re-download a toolchain that is already present. Off by default — a
    # present toolchain is the whole point of an idempotent install.
    refresh_toolchains: bool = False
    # Consent for the heavy Windows LLVM download acpp needs. Gathered up front
    # (before the progress spinner) so the prompt is actually answerable; the
    # toolchain installer never prompts mid-pipeline.
    assume_acpp_llvm: bool = False
    # Populated by DetectStep: the discrete-GPU vendor (nvidia|amd|intel|none),
    # which selects the compute SDK InstallDepsStep provisions and the build
    # backend the module CLIs default to.
    gpu_vendor: str = ""
    # Non-fatal problems surfaced by any step. Collected here rather than only
    # logged inline so the pipeline can re-print them after the progress bar —
    # an inline warn scrolls off above the "Setup Complete!" line and gets
    # missed. Empty means a fully clean run.
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
    """One unit of installer work.

    Every step honors the same contract — ``run(ctx) -> StepResult`` — so the
    pipeline can drive any sequence of steps without knowing what each does
    (Liskov / Open-Closed).
    """

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
            show_progress: Draw the setup progress bar. Read-only flows (a bare
                ``detect``, i.e. ``hub doctor``) pass False: a "Setup Complete!"
                bar there is misleading — nothing is being installed.
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
        """Re-print any non-fatal problems after the progress bar clears.

        Warnings logged mid-pipeline scroll off above the final summary;
        echoing them here makes sure a partial install (e.g. a GPU SDK that
        failed to download) is impossible to miss.
        """
        if not ctx.warnings:
            return
        console.warn(f"Completed with {len(ctx.warnings)} warning(s):")
        for message in ctx.warnings:
            console.warn(f"  - {message}")
