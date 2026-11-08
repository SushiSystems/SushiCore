# test_pipeline.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the install pipeline."""

from __future__ import annotations

import pytest

from sushicore.provision.config import ProvisionSettings
from sushicore.provision.pipeline import InstallContext, InstallPipeline, StepResult
from sushicore.provision.pipeline_memory import ScriptedStep


def _ran(steps, **options):
    """Run *steps* through a pipeline over a fresh context; return the pipeline's answer."""
    return InstallPipeline(steps).run(InstallContext(cfg=ProvisionSettings()), **options)


@pytest.mark.small
def test_pipeline_stops_on_the_first_failure(recording_console):
    """Check that the pipeline answers False when a step fails."""
    log = []
    steps = [ScriptedStep("a", StepResult.OK, log), ScriptedStep("b", StepResult.FAILED, log),
             ScriptedStep("c", StepResult.OK, log)]
    assert _ran(steps) is False


@pytest.mark.small
def test_pipeline_runs_no_step_after_the_first_failure(recording_console):
    """Check that the steps after a failed one do not run."""
    log = []
    steps = [ScriptedStep("a", StepResult.OK, log), ScriptedStep("b", StepResult.FAILED, log),
             ScriptedStep("c", StepResult.OK, log)]
    _ran(steps)
    assert log == ["a", "b"]


@pytest.mark.small
def test_each_step_gets_a_header(recording_console):
    """Check that each step is announced by one header."""
    log = []
    _ran([ScriptedStep("a", StepResult.OK, log), ScriptedStep("b", StepResult.SKIPPED, log)])
    assert [args[0] for name, args in recording_console.calls if name == "header"] == [
        "setup: a", "setup: b"]


@pytest.mark.small
def test_each_step_gets_a_progress_event(recording_console):
    """Check that each step is reported to a program by one progress event."""
    log = []
    _ran([ScriptedStep("a", StepResult.OK, log), ScriptedStep("b", StepResult.SKIPPED, log)])
    assert [args[:3] for name, args in recording_console.calls if name == "progress"] == [
        ("a", 1, 2), ("b", 2, 2)]


@pytest.mark.small
def test_a_done_step_is_reported_as_a_success_and_a_skipped_one_as_information(recording_console):
    """Check that one step of each kind gives one success line and one information line."""
    log = []
    _ran([ScriptedStep("a", StepResult.OK, log), ScriptedStep("b", StepResult.SKIPPED, log)])
    names = [name for name, _ in recording_console.calls]
    assert (names.count("success"), names.count("info")) == (1, 1)


@pytest.mark.small
def test_a_caller_that_still_passes_show_progress_is_served(recording_console):
    """Check that the ignored show_progress argument is still accepted."""
    assert _ran([ScriptedStep("a", StepResult.OK, [])], show_progress=True) is True


@pytest.mark.small
def test_the_warnings_of_a_run_are_printed_again_after_the_steps(recording_console):
    """Check that a non-fatal warning of the context is re-printed once the steps ran."""
    step = ScriptedStep("a", StepResult.OK, [], warnings=("ninja missing",))
    _ran([step])
    warnings = [args[0] for name, args in recording_console.calls if name == "warn"]
    assert warnings == ["Completed with 1 warning(s):", "  - ninja missing"]


@pytest.mark.small
def test_a_step_given_the_empty_selection_installs_nothing(recording_console):
    """Check that the default selection the context carries turns every component off."""
    seen = []

    class _Probe(ScriptedStep):
        def run(self, ctx):
            seen.append(ctx.selection.as_dict())
            return super().run(ctx)

    _ran([_Probe("a", StepResult.OK, [])])
    assert seen == [{"install_intel_llvm": False, "install_acpp": False, "oneapi": False,
                     "gpu": False}]
