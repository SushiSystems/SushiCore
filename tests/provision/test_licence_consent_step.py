# test_licence_consent_step.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The licence step stops an install run the user did not consent to before anything installs."""

from __future__ import annotations

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.licence_consent import Licence, LicenceConsent
from sushicore.provision.licence_consent_step import LicenceConsentStep
from sushicore.provision.pipeline import InstallContext, InstallPipeline, Step, StepResult

pytestmark = pytest.mark.small

K_EULA = Licence("Vendor EULA", "https://vendor.example/eula")


class _InstallStep(Step):
    """Records each run in place of an install step."""

    name = "install"

    def __init__(self) -> None:
        """Start with no recorded run."""
        self.runs = 0

    def run(self, ctx: InstallContext) -> StepResult:
        """Record the run."""
        self.runs += 1
        return StepResult.OK


def _run(answer: str, *, dry_run: bool = False) -> tuple[bool, _InstallStep, RecordingConsole]:
    """Run the licence step, then a recording install step, with the user giving *answer*."""
    console = RecordingConsole(answer=answer)
    install = _InstallStep()
    consent = LicenceConsent(console, accept_flag=False)
    pipeline = InstallPipeline([LicenceConsentStep(consent, [lambda ctx: [K_EULA]]), install])
    ok = pipeline.run(InstallContext(cfg=ProvisionSettings(platform="linux"), dry_run=dry_run))
    return ok, install, console


def test_a_refused_licence_installs_nothing(recording_console):
    """Check that a no to the question stops the run before the install step."""
    ok, install, _console = _run("n")

    assert (ok, install.runs) == (False, 0)


def test_an_accepted_licence_lets_the_install_run(recording_console):
    """Check that a yes to the question lets the install step run."""
    ok, install, _console = _run("y")

    assert (ok, install.runs) == (True, 1)


def test_a_dry_run_asks_nothing(recording_console):
    """Check that a dry run, which installs nothing, never asks."""
    _ok, _install, console = _run("n", dry_run=True)

    assert not console.has_call("prompt")
