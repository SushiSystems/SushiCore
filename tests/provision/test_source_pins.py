# test_source_pins.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The installers read their commits and key fingerprint from the base fragment."""

from __future__ import annotations

import pytest

from sushicore.errors import ConfigError
from sushicore.provision.source_pins import base_git_pin, base_key_pin

pytestmark = pytest.mark.small


@pytest.mark.parametrize("name", ["vcpkg", "adaptivecpp", "unified-runtime"])
def test_each_clone_the_installers_make_has_a_pinned_commit(name):
    """Check that the base fragment pins a full commit and the ref it came from for each clone."""
    pin = base_git_pin(name)

    assert (pin.name, bool(pin.ref), len(pin.commit)) == (name, True, 40)


def test_the_oneapi_key_has_a_pinned_fingerprint():
    """Check that the base fragment pins the full fingerprint of the oneAPI apt key."""
    assert len(base_key_pin("oneapi-apt-key").fingerprint) == 40


def test_an_entry_with_no_commit_is_refused():
    """Check that asking for a commit the fragment does not pin is a configuration error."""
    with pytest.raises(ConfigError, match="pins no commit under 'cmake'"):
        base_git_pin("cmake")


def test_an_entry_with_no_fingerprint_is_refused():
    """Check that asking for a fingerprint the fragment does not pin is a configuration error."""
    with pytest.raises(ConfigError, match="pins no fingerprint under 'cmake'"):
        base_key_pin("cmake")
