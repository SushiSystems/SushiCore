# test_verifier_slot.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the slot that holds the verifier of the current run."""

from __future__ import annotations

import pytest

from sushicore.provision.download_verifier import DownloadVerifier
from sushicore.provision.verifier_slot import VerifierSlot

pytestmark = pytest.mark.small


def test_a_new_slot_holds_its_fallback():
    fallback = DownloadVerifier({})
    assert VerifierSlot(lambda: fallback).current() is fallback


def test_binding_none_returns_to_the_fallback():
    fallback = DownloadVerifier({})
    slot = VerifierSlot(lambda: fallback)
    slot.bind(DownloadVerifier({}))
    slot.bind(None)
    assert slot.current() is fallback


def test_holding_returns_the_verifier_inside_the_block_and_the_fallback_after_it():
    fallback = DownloadVerifier({})
    held = DownloadVerifier({})
    slot = VerifierSlot(lambda: fallback)
    with slot.holding(held):
        inside = slot.current()
    assert (inside, slot.current()) == (held, fallback)


def test_holding_returns_to_the_fallback_when_the_block_raises():
    fallback = DownloadVerifier({})
    slot = VerifierSlot(lambda: fallback)
    with pytest.raises(RuntimeError):
        with slot.holding(DownloadVerifier({})):
            raise RuntimeError("stop")
    assert slot.current() is fallback


def test_unbinding_builds_a_new_fallback_each_time():
    slot = VerifierSlot(lambda: DownloadVerifier({}))
    first = slot.current()
    slot.bind(None)
    assert slot.current() is not first
