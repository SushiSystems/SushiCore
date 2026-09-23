# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the pipeline core."""

from __future__ import annotations

from sushicore.provision.config import ProvisionSettings
from sushicore.provision.pipeline import (
    InstallContext, InstallPipeline, Step, StepResult, ToolchainSelection)


class _Step(Step):
    """Fake step for testing the pipeline."""

    def __init__(self, name, result, log):
        """Initialize the step with a name, result, and log."""
        self.name, self._result, self._log = name, result, log

    def run(self, ctx):
        """Execute the step and log its name."""
        self._log.append(self.name)
        return self._result


def test_pipeline_stops_on_the_first_failure(recording_console):
    """Check that the pipeline stops on the first failure."""
    log = []
    steps = [_Step("a", StepResult.OK, log), _Step("b", StepResult.FAILED, log),
             _Step("c", StepResult.OK, log)]
    ok = InstallPipeline(steps).run(InstallContext(cfg=ProvisionSettings()), show_progress=False)
    assert ok is False
    assert log == ["a", "b"]


def test_empty_selection_installs_nothing():
    """Check that an empty selection installs nothing."""
    assert ToolchainSelection().as_dict() == {
        "install_intel_llvm": False, "install_acpp": False, "oneapi": False, "gpu": False}


def test_gpu_reads_through_the_selection():
    """Check that the GPU setting reads through the selection."""
    ctx = InstallContext(cfg=ProvisionSettings(), selection=ToolchainSelection(gpu=True))
    assert ctx.gpu is True
