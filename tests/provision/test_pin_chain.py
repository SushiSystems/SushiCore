# test_pin_chain.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the walk that finds a library pinned at two versions."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.deps_fragment import SushiPin
from sushicore.provision.pin_chain import PinConflict, conflicts

K_COMMIT = "0123456789abcdef0123456789abcdef01234567"
K_ROOT = Path("/ws/sushiai")


def _pin(name, version):
    """Return the pin of *name* at *version*."""
    return SushiPin(name, version, K_COMMIT)


def _chain(log_version_of_runtime):
    """Lay out sushiai -> sushiblas -> sushiruntime -> sushilog, sushiai also pinning sushilog.

    sushiai pins sushilog at v1.0.0; sushiruntime pins it at *log_version_of_runtime*. Return the
    pins of sushiai and the lookup that gives each library's checkout and pins.
    """
    libraries = {
        ("sushiblas", "v2.0.0"): (Path("/ws/sushiblas"), [_pin("sushiruntime", "v3.0.0")]),
        ("sushiruntime", "v3.0.0"): (Path("/ws/sushiruntime"),
                                     [_pin("sushilog", log_version_of_runtime)]),
        ("sushilog", "v1.0.0"): (Path("/ws/sushilog"), []),
    }
    pins = [_pin("sushiblas", "v2.0.0"), _pin("sushilog", "v1.0.0")]
    return pins, lambda checkout, name, version: libraries.get((name, version))


@pytest.mark.small
def test_a_chain_pinning_one_version_has_no_conflict():
    """Check that three levels pinning sushilog at one version agree."""
    pins, pins_of = _chain("v1.0.0")
    assert conflicts("sushiai", K_ROOT, pins, pins_of) == []


@pytest.mark.small
def test_a_chain_pinning_two_versions_names_both_repositories():
    """Check that a third-level pin at another version is a conflict naming both pinners."""
    pins, pins_of = _chain("v1.1.0")
    assert conflicts("sushiai", K_ROOT, pins, pins_of) == [
        PinConflict("sushilog", "sushiai", "v1.0.0", "sushiruntime", "v1.1.0")]


@pytest.mark.small
def test_the_conflict_message_names_the_library_both_pinners_and_both_versions():
    """Check that the message carries the library, both pinning repositories and both versions."""
    message = PinConflict("sushilog", "sushiai", "v1.0.0", "sushiruntime", "v1.1.0").message()
    assert all(part in message for part in
               ("sushilog", "sushiai", "v1.0.0", "sushiruntime", "v1.1.0"))


@pytest.mark.small
def test_a_library_with_no_checkout_ends_its_branch():
    """Check that an unresolved library is not walked and raises nothing."""
    assert conflicts("sushiai", K_ROOT, [_pin("sushiblas", "v2.0.0")],
                     lambda checkout, name, version: None) == []
