# test_licence_consent.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Setup installs a third-party licence's software only after the user said yes to it."""

from __future__ import annotations

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.provision.licence_consent import (
    ConsentDecision,
    Licence,
    LicenceConsent,
    decide,
    is_accepted,
)
from sushicore.provision.licence_consent_memory import granted_consent

pytestmark = pytest.mark.small

K_ONE = Licence("One EULA", "https://one.example/eula")
K_TWO = Licence("Two EULA", "https://two.example/eula")


@pytest.mark.parametrize(("licences", "machine", "flag", "answer", "expected"), [
    ((), True, False, None, ConsentDecision(True, ())),
    ((K_ONE,), True, True, None, ConsentDecision(True, (K_ONE,))),
    ((K_ONE,), False, True, None, ConsentDecision(True, (K_ONE,))),
    ((K_ONE, K_TWO), True, False, None, ConsentDecision(False, (K_ONE, K_TWO), 2)),
    ((K_ONE,), False, False, True, ConsentDecision(True, (K_ONE,))),
    ((K_ONE,), False, False, False, ConsentDecision(False, (K_ONE,), 1)),
])
def test_decide_grants_only_on_the_flag_or_a_yes(licences, machine, flag, answer, expected):
    """Check each mode, flag and answer against the decision the ruling gives."""
    assert decide(licences, machine=machine, accept_flag=flag, answer=answer) == expected


def test_consent_in_machine_mode_without_the_flag_lists_every_licence_and_asks_nothing():
    """Check that a machine run names both licences with their links and never prompts."""
    console = RecordingConsole(machine=True)

    decision = LicenceConsent(console, accept_flag=False).request([K_ONE, K_TWO])

    assert (decision.granted, decision.code) == (False, 2)
    assert not console.has_call("prompt")
    assert f"  {K_ONE.name}: {K_ONE.link}" in console.texts("error")
    assert f"  {K_TWO.name}: {K_TWO.link}" in console.texts("error")


def test_consent_asks_an_interactive_user_once_per_run():
    """Check that a second request returns the first decision without a second prompt."""
    console = RecordingConsole(answer="y")
    consent = LicenceConsent(console, accept_flag=False)

    consent.request([K_ONE])
    consent.request([K_ONE, K_TWO])

    assert console.texts("prompt") == ["Accept these licences? [y/N]"]


def test_consent_names_each_licence_before_asking():
    """Check that the interactive question follows a line per licence with its link."""
    console = RecordingConsole(answer="n")

    LicenceConsent(console, accept_flag=False).request([K_ONE])

    kinds = [call.kind for call in console.calls]
    assert kinds.index("info") < kinds.index("prompt")
    assert console.texts("info") == [f"  {K_ONE.name}: {K_ONE.link}"]


def test_consent_accepts_only_the_licences_it_was_asked_about():
    """Check that a granted consent covers its own licences and no other."""
    consent = granted_consent(K_ONE)

    assert (is_accepted(consent, K_ONE), is_accepted(consent, K_TWO)) == (True, False)


def test_is_accepted_is_false_when_the_run_holds_no_consent():
    """Check that an installer outside a setup run holds no consent."""
    assert not is_accepted(None, K_ONE)
