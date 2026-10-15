# test_chosen_toolkit_locator.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Any vendor's toolkit is chosen, installed, remembered and named in its root variable."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from sushicore.provision.gpu.chosen_toolkit_locator import ChosenToolkitLocator
from sushicore.provision.gpu.toolkit_choice import ToolkitChoice
from sushicore.provision.gpu.toolkit_choice_file import ToolkitChoiceFile
from sushicore.provision.gpu.toolkit_vendor import ToolkitSourceError, ToolkitVendor


pytestmark = pytest.mark.medium

K_CFG = SimpleNamespace(platform="linux")
K_ROOT_VARIABLE = "FAKE_TOOLKIT_PATH"
K_OVERRIDE = "FAKE_TOOLKIT_RELEASE"


class _Hardware:
    """Cards named by one text."""

    def __init__(self, cards: str) -> None:
        """Store the cards."""
        self.cards = cards

    def fingerprint(self) -> str:
        """Return the cards."""
        return self.cards

    def describe(self) -> str:
        """Return the cards."""
        return self.cards


class _Vendor:
    """Publishes ``1.0`` and ``2.0``; a card named ``old`` fits only ``1.0``."""

    def __init__(self, base: Path) -> None:
        """Install under *base*."""
        self.base = base
        self.hardware: _Hardware | None = _Hardware("new")
        self.offline = False
        self.installed: list[str] = []
        self.chosen: list[str] = []

    name = "Fake"
    root_variable = K_ROOT_VARIABLE
    override_variable = K_OVERRIDE
    platform_key = "linux-x86_64"

    @property
    def toolkits_dir(self) -> Path:
        """Return the base folder."""
        return self.base

    def query_hardware(self):
        """Return the cards."""
        return self.hardware

    def choose(self, hardware):
        """Pick by the card's name, or fail when offline."""
        self._online()
        self.chosen.append(hardware.cards)
        return {"new": "2.0", "old": "1.0"}.get(hardware.cards)

    def resolve_override(self, text):
        """Accept the two published releases."""
        self._online()
        if text not in ("1.0", "2.0"):
            raise ToolkitSourceError(f"no release {text}")
        return text

    def is_installed(self, label):
        """Report whether the marker file exists."""
        return (self.root_of(label) / "marker").is_file()

    def root_of(self, label):
        """Return the release folder."""
        return self.base / label

    def install(self, label):
        """Create the marker file."""
        self._online()
        self.root_of(label).mkdir(parents=True)
        (self.root_of(label) / "marker").write_text("")
        self.installed.append(label)
        return self.root_of(label)

    def discard_downloads(self):
        """Do nothing; there are no downloads."""

    def is_toolkit_root(self, root):
        """Report whether *root* holds the marker."""
        return (root / "marker").is_file()

    def find_system_toolkit(self):
        """Report no system install."""
        return None

    def _online(self):
        """Fail as an unreachable index does."""
        if self.offline:
            raise ToolkitSourceError("offline")


class _Environment:
    """The user's variables, in memory; not a dict, which an empty one would make falsy and
    send the writes to the real store."""

    def __init__(self) -> None:
        """Start with no variables."""
        self.values: dict[str, str] = {}

    def read(self, name):
        """Return the value of *name*."""
        return self.values.get(name)

    def write(self, name, value):
        """Set *name*."""
        self.values[name] = value

    def remove(self, name):
        """Unset *name*."""
        self.values.pop(name, None)


@pytest.fixture
def parts(tmp_path, monkeypatch, recording_console):
    """Return a locator over a fake vendor, and the fakes."""
    monkeypatch.delenv(K_ROOT_VARIABLE, raising=False)
    monkeypatch.delenv(K_OVERRIDE, raising=False)
    found = SimpleNamespace(vendor=_Vendor(tmp_path / "toolkits"),
                            choices=ToolkitChoiceFile(tmp_path / "choice.json"),
                            environment=_Environment(), console=recording_console)
    found.locator = ChosenToolkitLocator(found.vendor, found.choices, found.environment)
    return found


def _warnings(parts) -> list[str]:
    """Return the messages recorded on the console's ``warn`` calls."""
    return [args[0] for name, args in parts.console.calls if name == "warn"]


def test_the_fake_answers_the_vendor_contract(tmp_path):
    """Check that the fake stays in step with the protocol it stands in for."""
    assert isinstance(_Vendor(tmp_path), ToolkitVendor)


def test_provision_installs_the_chosen_release_and_names_its_root(parts):
    """Check the install, the root variable in both stores and the recorded choice."""
    assert parts.locator.provision(K_CFG, dry_run=False) is True

    root = parts.vendor.root_of("2.0")
    assert parts.vendor.installed == ["2.0"]
    assert parts.environment.values[K_ROOT_VARIABLE] == str(root)
    assert parts.locator.locate(K_CFG).root == root
    assert parts.choices.read() == ToolkitChoice("new", "linux-x86_64", "2.0")


def test_a_recorded_choice_is_reused_without_the_network(parts):
    """Check that the same hardware reuses its release with the index unreachable."""
    parts.locator.provision(K_CFG, dry_run=False)
    parts.vendor.offline = True

    parts.locator.provision(K_CFG, dry_run=False)

    assert parts.vendor.chosen == ["new"]
    assert _warnings(parts) == []


def test_new_hardware_chooses_again(parts):
    """Check that a changed fingerprint is not served the recorded release."""
    parts.locator.provision(K_CFG, dry_run=False)
    parts.vendor.hardware = _Hardware("old")

    parts.locator.provision(K_CFG, dry_run=False)

    assert parts.vendor.installed == ["2.0", "1.0"]


def test_the_override_wins_and_is_not_recorded(parts, monkeypatch):
    """Check that the override installs its release and leaves the record alone."""
    monkeypatch.setenv(K_OVERRIDE, "1.0")

    parts.locator.provision(K_CFG, dry_run=False)

    assert parts.vendor.installed == ["1.0"]
    assert parts.choices.read() is None


def test_an_unknown_override_installs_nothing(parts, monkeypatch):
    """Check that an override no release matches is reported, not raised."""
    monkeypatch.setenv(K_OVERRIDE, "9.9")

    assert parts.locator.provision(K_CFG, dry_run=False) is True

    assert parts.vendor.installed == []
    assert _warnings(parts)


def test_an_unreachable_index_keeps_the_toolkit_in_use(parts, tmp_path):
    """Check that an offline run reports and keeps an existing toolkit."""
    existing = tmp_path / "system"
    existing.mkdir()
    (existing / "marker").write_text("")
    parts.environment.values[K_ROOT_VARIABLE] = str(existing)
    parts.vendor.offline = True

    assert parts.locator.provision(K_CFG, dry_run=False) is True

    assert parts.vendor.installed == []
    assert any(str(existing) in message for message in _warnings(parts))


def test_no_driver_installs_nothing(parts):
    """Check that a machine without the vendor's driver is reported and left alone."""
    parts.vendor.hardware = None

    assert parts.locator.provision(K_CFG, dry_run=False) is True

    assert parts.vendor.installed == []
    assert _warnings(parts)


def test_dry_run_installs_nothing(parts):
    """Check that a dry run neither installs nor writes the root variable."""
    parts.locator.provision(K_CFG, dry_run=True)

    assert parts.vendor.installed == []
    assert K_ROOT_VARIABLE not in parts.environment.values


def test_hardware_no_release_fits_falls_back_to_the_cpu(parts):
    """Check that a card no release fits gets no install and a warning."""
    parts.vendor.hardware = _Hardware("ancient")

    parts.locator.provision(K_CFG, dry_run=False)

    assert parts.vendor.installed == []
    assert any("CPU path" in message for message in _warnings(parts))
