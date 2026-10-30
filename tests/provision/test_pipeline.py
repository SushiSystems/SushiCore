# test_pipeline.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the pipeline core."""

from __future__ import annotations

import pytest

from sushicore.provision.config import ProvisionSettings
from sushicore.provision.pipeline import (
    InstallContext, InstallPipeline, Step, StepResult, ToolchainSelection)


pytestmark = pytest.mark.small


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


def test_each_step_is_reported_once_with_a_header_a_progress_event_and_an_outcome(recording_console):
    log = []
    steps = [_Step("a", StepResult.OK, log), _Step("b", StepResult.SKIPPED, log)]
    assert InstallPipeline(steps).run(InstallContext(cfg=ProvisionSettings())) is True
    names = [name for name, _ in recording_console.calls]
    assert names.count("header") == 2
    assert names.count("progress") == 2
    assert names.count("success") == 1
    assert names.count("info") == 1


def test_the_pipeline_reaches_for_no_rich_progress_bar():
    """The pipeline reports through the console seam alone, so Rich stays behind the renderer."""
    import inspect

    from sushicore.provision import pipeline

    assert "rich" not in inspect.getsource(pipeline)


def test_a_caller_that_still_passes_show_progress_is_served(recording_console):
    ok = InstallPipeline([_Step("a", StepResult.OK, [])]).run(
        InstallContext(cfg=ProvisionSettings()), show_progress=True)
    assert ok is True
