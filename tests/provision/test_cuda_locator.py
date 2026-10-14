# test_cuda_locator.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The CUDA locator installs the release the hardware needs and points CUDA_PATH at it."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from sushicore.provision.gpu.cuda import K_CUDA_PATH, K_RELEASE_OVERRIDE, CudaLocator
from sushicore.provision.gpu.cuda_choice import CudaChoice
from sushicore.provision.gpu.cuda_choice_file import CudaChoiceFile
from sushicore.provision.gpu.cuda_hardware import NvidiaHardware
from sushicore.provision.gpu.cuda_redist import RedistError
from sushicore.provision.gpu.cuda_release import RedistRelease
from sushicore.provision.gpu.cuda_toolkit_installer import nvcc_in

K_CFG = SimpleNamespace(platform="windows")
K_ADA = NvidiaHardware(("89",), (13, 1))
K_VERSIONS = [(13, 4, 3), (13, 1, 2), (12, 6, 3)]


class _Index:
    """Publishes fixed versions; fails on every call once *offline* is set."""

    def __init__(self, offline: bool = False) -> None:
        """Store whether the index is reachable."""
        self.offline = offline

    def versions(self):
        """Return the published versions."""
        if self.offline:
            raise RedistError("offline")
        return list(K_VERSIONS)

    def release(self, version, key):
        """Return an empty release of *version*."""
        if self.offline:
            raise RedistError("offline")
        return RedistRelease(version, {})


class _Installer:
    """Installs by creating nvcc under a folder; 13.x builds sm_75 and newer."""

    def __init__(self, base: Path) -> None:
        """Install under *base*."""
        self.base = base
        self.installed: list[str] = []

    def root_of(self, label):
        """Return the release's root."""
        return self.base / label

    def is_installed(self, label):
        """Report whether nvcc is in place."""
        return nvcc_in(self.root_of(label)).is_file()

    def probe_architectures(self, release):
        """Return what the release's major builds for."""
        return frozenset({"75", "89"}) if release.version[0] == 13 else frozenset({"61", "89"})

    def install(self, release):
        """Create the release's nvcc and return its root."""
        root = self.root_of(release.label)
        nvcc_in(root).parent.mkdir(parents=True)
        nvcc_in(root).write_text("")
        self.installed.append(release.label)
        return root

    def discard_downloads(self):
        """Do nothing; there are no downloads."""


class _Environment:
    """The user's variables, in memory; deliberately not a dict, which an empty one would
    make falsy and send the writes to the real store."""

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
def parts(tmp_path, monkeypatch):
    """Return a locator over fakes and the fakes themselves."""
    monkeypatch.delenv(K_CUDA_PATH, raising=False)
    monkeypatch.delenv(K_RELEASE_OVERRIDE, raising=False)
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))
    found = SimpleNamespace(hardware=K_ADA, index=_Index(), installer=_Installer(tmp_path),
                            choices=CudaChoiceFile(tmp_path / "choice.json"),
                            environment=_Environment())
    found.locator = CudaLocator(lambda: found.hardware, found.index, found.installer,
                                found.choices, found.environment)
    return found


def _warnings(recording_console) -> list[str]:
    """Return the messages recorded on the console's ``warn`` calls."""
    return [args[0] for name, args in recording_console.calls if name == "warn"]


def test_provision_installs_the_chosen_release_and_points_cuda_path(
        parts, recording_console):
    """Check that a 13.1 driver with an Ada card gets 13.1.2 and CUDA_PATH names it."""
    assert parts.locator.provision(K_CFG, dry_run=False) is True

    root = parts.installer.root_of("13.1.2")
    assert parts.installer.installed == ["13.1.2"]
    assert parts.environment.values[K_CUDA_PATH] == str(root)
    assert parts.locator.locate(K_CFG).root == root
    assert parts.choices.read() == CudaChoice(K_ADA.fingerprint(), "windows-x86_64", "13.1.2")


def test_provision_gives_pascal_a_12x_release(parts, recording_console):
    """Check that an sm_61 card is given the newest release that still builds for it."""
    parts.hardware = NvidiaHardware(("61",), (13, 4))

    parts.locator.provision(K_CFG, dry_run=False)

    assert parts.installer.installed == ["12.6.3"]


def test_a_recorded_choice_is_reused_without_the_network(parts, recording_console):
    """Check that the same hardware reuses its release with the index unreachable."""
    parts.locator.provision(K_CFG, dry_run=False)
    parts.index.offline = True

    parts.locator.provision(K_CFG, dry_run=False)

    assert parts.installer.installed == ["13.1.2"]
    assert _warnings(recording_console) == []


def test_new_hardware_chooses_again(parts, recording_console):
    """Check that a changed fingerprint is not served the recorded release."""
    parts.locator.provision(K_CFG, dry_run=False)
    parts.hardware = NvidiaHardware(("89",), (13, 4))

    parts.locator.provision(K_CFG, dry_run=False)

    assert parts.installer.installed == ["13.1.2", "13.4.3"]


def test_the_override_names_the_release(parts, recording_console, monkeypatch):
    """Check that a release prefix installs the newest release it matches."""
    monkeypatch.setenv(K_RELEASE_OVERRIDE, "12.6")

    parts.locator.provision(K_CFG, dry_run=False)

    assert parts.installer.installed == ["12.6.3"]
    assert parts.choices.read() is None


def test_an_unreachable_index_keeps_the_toolkit_in_use(parts, recording_console, tmp_path):
    """Check that an offline run reports and keeps an existing toolkit."""
    existing = tmp_path / "system-cuda"
    nvcc_in(existing).parent.mkdir(parents=True)
    nvcc_in(existing).write_text("")
    parts.environment.values[K_CUDA_PATH] = str(existing)
    parts.index.offline = True

    assert parts.locator.provision(K_CFG, dry_run=False) is True

    assert parts.installer.installed == []
    assert any(str(existing) in message for message in _warnings(recording_console))


def test_no_driver_installs_nothing(parts, recording_console):
    """Check that a machine without nvidia-smi is reported and left alone."""
    parts.hardware = None

    assert parts.locator.provision(K_CFG, dry_run=False) is True

    assert parts.installer.installed == []
    assert _warnings(recording_console)


def test_dry_run_installs_nothing(parts, recording_console):
    """Check that a dry run neither installs nor writes CUDA_PATH."""
    parts.locator.provision(K_CFG, dry_run=True)

    assert parts.installer.installed == []
    assert K_CUDA_PATH not in parts.environment.values


def test_a_card_no_release_builds_for_falls_back_to_the_cpu(parts, recording_console):
    """Check that an sm_35 card gets no release and a warning."""
    parts.hardware = NvidiaHardware(("35",), (13, 4))

    parts.locator.provision(K_CFG, dry_run=False)

    assert parts.installer.installed == []
    assert any("CPU path" in message for message in _warnings(recording_console))

