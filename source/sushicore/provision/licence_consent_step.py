# licence_consent_step.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Asks for consent to the run's third-party licences before anything is installed."""

from __future__ import annotations

import typing

from .licence_consent import Licence, LicenceConsent
from .install_context import InstallContext
from .step import Step
from .step_result import StepResult


@typing.final
class LicenceConsentStep(Step):
    """Collects the licences the install steps declare and asks for consent once.

    Args:
        consent: The run's consent; it remembers the decision the installers read.
        needs: Each returns the licences one install step needs for a context.
    """

    name = "licences"

    def __init__(self, consent: LicenceConsent,
                 needs: typing.Sequence[typing.Callable[[InstallContext], list[Licence]]],
                 ) -> None:
        """Store the consent and the declarations."""
        self._consent = consent
        self._needs = needs

    def run(self, ctx: InstallContext) -> StepResult:
        """Fails the run when the licences are refused; a dry run installs nothing and asks nothing."""
        if ctx.dry_run:
            return StepResult.SKIPPED
        licences: list[Licence] = []
        for need in self._needs:
            licences.extend(held for held in need(ctx) if held not in licences)
        if not licences:
            return StepResult.SKIPPED
        return StepResult.OK if self._consent.request(licences).granted else StepResult.FAILED
