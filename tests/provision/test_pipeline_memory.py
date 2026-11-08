# test_pipeline_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the scripted step promises: it logs that it ran, adds its warnings and answers its result."""

from __future__ import annotations

import pytest

from sushicore.provision.config import ProvisionSettings
from sushicore.provision.pipeline import InstallContext, StepResult
from sushicore.provision.pipeline_memory import ScriptedStep


@pytest.mark.small
def test_a_run_logs_the_name_and_answers_the_scripted_result():
    log = []
    step = ScriptedStep("detect", StepResult.SKIPPED, log)
    assert step.run(InstallContext(cfg=ProvisionSettings())) is StepResult.SKIPPED
    assert log == ["detect"]


@pytest.mark.small
def test_a_run_adds_its_warnings_to_the_context():
    ctx = InstallContext(cfg=ProvisionSettings())
    ScriptedStep("detect", StepResult.OK, [], warnings=("careful",)).run(ctx)
    assert ctx.warnings == ["careful"]
