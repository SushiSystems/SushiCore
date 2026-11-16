# licence_consent_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Builds a consent already given, for tests of installers that need one."""

from __future__ import annotations

from ..console_memory import RecordingConsole
from .licence_consent import Licence, LicenceConsent


def granted_consent(*licences: Licence) -> LicenceConsent:
    """Returns a consent that covers *licences*."""
    consent = LicenceConsent(RecordingConsole(machine=True), accept_flag=True)
    consent.request(licences)
    return consent
