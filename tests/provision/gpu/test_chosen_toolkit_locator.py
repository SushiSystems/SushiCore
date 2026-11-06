# test_chosen_toolkit_locator.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Any vendor's toolkit is chosen, installed, remembered and named in its root variable."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from sushicore.provision.gpu.chosen_toolkit_locator import ChosenToolkitLocator
from sushicore.provision.gpu.toolkit_choice import ToolkitChoice
from sushicore.provision.gpu.toolkit_choice_file import ToolkitChoiceFile
from sushicore.provision.gpu.toolkit_vendor_memory import FixedHardware, InMemoryToolkitVendor
from sushicore.provision.user_environment import ProfileEnvironment

pytestmark = pytest.mark.medium

K_CFG = SimpleNamespace(platform="linux")
K_ROOT_VARIABLE = "FAKE_TOOLKIT_PATH"
K_OVERRIDE = "FAKE_TOOLKIT_RELEASE"
K_LABELS = {"new": "2.0", "old": "1.0"}


def _scene(tmp_path: Path, recording_console, *, hardware="new", **vendor_options):
    """Return a locator over an in-memory vendor, a profile file and a choice file under *tmp_path*."""
    vendor = InMemoryToolkitVendor(
        tmp_path / "toolkits", labels=K_LABELS, published=("1.0", "2.0"),
        hardware=None if hardware is None else FixedHardware(hardware), **vendor_options)
    choices = ToolkitChoiceFile(tmp_path / "choice.json")
    user = ProfileEnvironment(tmp_path / "profile")
    process: dict[str, str] = {}
    return SimpleNamespace(
        vendor=vendor, choices=choices, user=user, process=process, console=recording_console,
        locator=ChosenToolkitLocator(vendor, choices, user, process))


@pytest.fixture
def parts(tmp_path, recording_console):
    """Return a scene whose cards are named ``new`` and fit release 2.0."""
    return _scene(tmp_path, recording_console)


def test_provision_installs_the_release_the_hardware_needs(parts):
    """Check that the release chosen for the cards is the one installed."""
    assert parts.locator.provision(K_CFG, dry_run=False) is True

    assert parts.vendor.installed == ["2.0"]


def test_provision_names_the_root_in_the_process_variable(parts):
    """Check that the process variable holds the root of the installed release."""
    parts.locator.provision(K_CFG, dry_run=False)

    assert parts.process[K_ROOT_VARIABLE] == str(parts.vendor.root_of("2.0"))


def test_provision_names_the_root_in_the_user_variable(parts):
    """Check that the user's persistent variable holds the root of the installed release."""
    parts.locator.provision(K_CFG, dry_run=False)

    assert parts.user.read(K_ROOT_VARIABLE) == str(parts.vendor.root_of("2.0"))


def test_locate_finds_the_toolkit_that_provision_named(parts):
    """Check that locate returns the root provision wrote to the process variable."""
    parts.locator.provision(K_CFG, dry_run=False)

    assert parts.locator.locate(K_CFG).root == parts.vendor.root_of("2.0")


def test_provision_records_the_choice(parts):
    """Check that the choice file holds the fingerprint, the platform and the release."""
    parts.locator.provision(K_CFG, dry_run=False)

    assert parts.choices.read() == ToolkitChoice("new", "linux-x86_64", "2.0")


def test_a_recorded_choice_is_reused_without_the_network(parts):
    """Check that the same hardware reuses its release with the index unreachable."""
    parts.locator.provision(K_CFG, dry_run=False)
    parts.vendor.offline = True

    parts.locator.provision(K_CFG, dry_run=False)

    assert parts.vendor.chosen == ["new"]
    assert parts.console.texts("warn") == []


def test_new_hardware_chooses_again(parts):
    """Check that a changed fingerprint is not served the recorded release."""
    parts.locator.provision(K_CFG, dry_run=False)
    parts.vendor.hardware = FixedHardware("old")

    parts.locator.provision(K_CFG, dry_run=False)

    assert parts.vendor.installed == ["2.0", "1.0"]


def test_the_override_installs_its_release(parts):
    """Check that the release the override variable names is the one installed."""
    parts.process[K_OVERRIDE] = "1.0"

    parts.locator.provision(K_CFG, dry_run=False)

    assert parts.vendor.installed == ["1.0"]


def test_the_override_is_not_recorded(parts):
    """Check that an override leaves the choice file without a record."""
    parts.process[K_OVERRIDE] = "1.0"

    parts.locator.provision(K_CFG, dry_run=False)

    assert parts.choices.read() is None


def test_an_unknown_override_installs_nothing_and_says_why(parts):
    """Check that an override no release matches is reported with its reason, not raised."""
    parts.process[K_OVERRIDE] = "9.9"

    assert parts.locator.provision(K_CFG, dry_run=False) is True

    assert parts.vendor.installed == []
    assert parts.console.texts("warn") == [
        "Fake toolkit not installed: no release 9.9; the build uses the CPU path."]


def test_an_unreachable_index_keeps_the_toolkit_in_use(tmp_path, recording_console):
    """Check that an offline run installs nothing and names the toolkit that stays in use."""
    existing = Path("system-toolkit")
    parts = _scene(tmp_path, recording_console, toolkit_roots=[existing])
    parts.process[K_ROOT_VARIABLE] = str(existing)
    parts.vendor.offline = True

    assert parts.locator.provision(K_CFG, dry_run=False) is True

    assert parts.vendor.installed == []
    assert parts.console.texts("warn") == [
        f"Fake toolkit not installed: offline; the toolkit at {existing} stays in use."]


def test_no_driver_installs_nothing_and_says_so(tmp_path, recording_console):
    """Check that a machine without the vendor's driver is reported and left alone."""
    parts = _scene(tmp_path, recording_console, hardware=None)

    assert parts.locator.provision(K_CFG, dry_run=False) is True

    assert parts.vendor.installed == []
    assert parts.console.texts("warn") == [
        "The driver reported no card; the Fake toolkit is not installed and the build "
        "uses the CPU path."]


def test_dry_run_installs_nothing(parts):
    """Check that a dry run installs no release."""
    parts.locator.provision(K_CFG, dry_run=True)

    assert parts.vendor.installed == []


def test_dry_run_does_not_write_the_root_variable(parts):
    """Check that a dry run leaves the process variable unset."""
    parts.locator.provision(K_CFG, dry_run=True)

    assert K_ROOT_VARIABLE not in parts.process


def test_hardware_no_release_fits_falls_back_to_the_cpu(tmp_path, recording_console):
    """Check that a card no release fits gets no install and the CPU-path warning."""
    parts = _scene(tmp_path, recording_console, hardware="ancient")

    parts.locator.provision(K_CFG, dry_run=False)

    assert parts.vendor.installed == []
    assert parts.console.texts("warn") == [
        "No published Fake release fits ancient; update the driver, or set "
        f"{K_OVERRIDE}. The build uses the CPU path."]
