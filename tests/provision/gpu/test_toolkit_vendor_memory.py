# test_toolkit_vendor_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the in-memory toolkit vendor promises as a stand-in for a real vendor."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.gpu.toolkit_vendor import ToolkitSourceError
from sushicore.provision.gpu.toolkit_vendor_memory import FixedHardware, InMemoryToolkitVendor

pytestmark = pytest.mark.small

K_BASE = Path("toolkits")


def _vendor(**options) -> InMemoryToolkitVendor:
    """Return a vendor that publishes 1.0 and 2.0 and maps the card ``new`` to 2.0."""
    return InMemoryToolkitVendor(K_BASE, labels={"new": "2.0"}, published=("1.0", "2.0"),
                                 **options)


def test_fixed_hardware_names_its_cards_as_fingerprint_and_description():
    """Check that the cards text is both the fingerprint and the description."""
    cards = FixedHardware("sm_89")

    assert (cards.fingerprint(), cards.describe()) == ("sm_89", "sm_89")


def test_choose_returns_the_release_of_the_fingerprint_and_records_it():
    """Check that choose maps the fingerprint to its release and records the question."""
    vendor = _vendor()

    assert vendor.choose(FixedHardware("new")) == "2.0"
    assert vendor.chosen == ["new"]


def test_choose_returns_none_for_a_fingerprint_no_release_fits():
    """Check that an unmapped fingerprint gets no release."""
    assert _vendor().choose(FixedHardware("ancient")) is None


def test_resolve_override_returns_a_published_release():
    """Check that a published release resolves to itself."""
    assert _vendor().resolve_override("1.0") == "1.0"


def test_resolve_override_refuses_a_release_that_is_not_published():
    """Check that an unpublished release raises ToolkitSourceError."""
    with pytest.raises(ToolkitSourceError):
        _vendor().resolve_override("9.9")


def test_install_marks_the_release_installed_and_returns_its_root():
    """Check that an install returns the folder under the base and makes it a toolkit root."""
    vendor = _vendor()

    root = vendor.install("2.0")

    assert root == K_BASE / "2.0"
    assert vendor.is_installed("2.0")
    assert vendor.is_toolkit_root(root)
    assert vendor.installed == ["2.0"]


def test_a_release_not_installed_is_not_installed():
    """Check that nothing is installed before install is called."""
    assert not _vendor().is_installed("2.0")


def test_a_preset_toolkit_root_is_a_toolkit_root():
    """Check that a folder given as already holding a toolkit is recognised."""
    assert _vendor(toolkit_roots=[Path("elsewhere")]).is_toolkit_root(Path("elsewhere"))


@pytest.mark.parametrize("call", [
    lambda vendor: vendor.choose(FixedHardware("new")),
    lambda vendor: vendor.resolve_override("1.0"),
    lambda vendor: vendor.install("1.0"),
], ids=["choose", "resolve-override", "install"])
def test_an_offline_vendor_raises_on_every_call_that_reads_the_index(call):
    """Check that choose, resolve_override and install raise when the index is unreachable."""
    vendor = _vendor()
    vendor.offline = True

    with pytest.raises(ToolkitSourceError):
        call(vendor)


def test_discard_downloads_counts_the_calls():
    """Check that each discard adds one to the count."""
    vendor = _vendor()

    vendor.discard_downloads()

    assert vendor.discards == 1


def test_the_vendor_answers_the_hardware_it_was_given():
    """Check that query_hardware returns the fixed hardware."""
    assert _vendor(hardware=FixedHardware("new")).query_hardware().describe() == "new"


def test_the_vendor_answers_the_system_toolkit_it_was_given():
    """Check that find_system_toolkit returns the fixed path."""
    assert _vendor(system_toolkit=Path("system")).find_system_toolkit() == Path("system")
