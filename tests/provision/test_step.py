# test_step.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the contract one installer step implements."""

from __future__ import annotations

import pytest

from sushicore.provision.config import ProvisionSettings
from sushicore.provision.install_context import InstallContext
from sushicore.provision.step import Step
from sushicore.provision.step_result import StepResult


@pytest.mark.small
def test_a_step_cannot_be_built_without_run():
    """Check that the contract leaves run abstract."""
    with pytest.raises(TypeError):
        Step()


@pytest.mark.small
def test_a_step_that_implements_run_reports_its_outcome():
    """Check that a subclass of the contract is built and answers its outcome."""
    class _Done(Step):
        name = "done"

        def run(self, ctx: InstallContext) -> StepResult:
            """Report success."""
            return StepResult.OK

    assert _Done().run(InstallContext(cfg=ProvisionSettings())) is StepResult.OK
