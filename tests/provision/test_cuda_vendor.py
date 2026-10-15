# test_cuda_vendor.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""NVIDIA's answers: the driver ceiling, the compiler's architectures and the override."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.gpu.cuda_hardware import NvidiaHardware
from sushicore.provision.gpu.cuda_redist import RedistError
from sushicore.provision.gpu.cuda_release import RedistRelease
from sushicore.provision.gpu.cuda_toolkit_installer import ToolkitInstallError
from sushicore.provision.gpu.cuda_vendor import CudaVendor
from sushicore.provision.gpu.toolkit_vendor import ToolkitVendor


pytestmark = pytest.mark.medium

K_VERSIONS = [(13, 4, 3), (13, 1, 2), (12, 9, 2), (12, 6, 3)]


class _Index:
    """Publishes fixed versions."""

    def versions(self):
        """Return the published versions, newest first."""
        return list(K_VERSIONS)

    def release(self, version, key):
        """Return an empty release of *version*."""
        return RedistRelease(version, {})


class _Installer:
    """13.x builds sm_75 and newer, 12.x builds sm_61 too; 13.4.3's compiler is broken."""

    def __init__(self) -> None:
        """Start with nothing installed."""
        self.installed: list[str] = []
        self.broken: set[tuple[int, ...]] = set()

    def probe_architectures(self, release):
        """Return what the release's major builds for."""
        if release.version in self.broken:
            raise ToolkitInstallError("nvcc did not run")
        return frozenset({"75", "89"}) if release.version[0] == 13 else frozenset({"61", "89"})

    def install(self, release):
        """Record the install."""
        self.installed.append(release.label)
        return Path(release.label)


@pytest.fixture
def vendor(recording_console):
    """Return a CUDA vendor over fakes."""
    installer = _Installer()
    found = CudaVendor(lambda: None, _Index(), installer)
    found.fake_installer = installer
    return found


def test_the_vendor_answers_the_contract(vendor):
    """Check that the CUDA vendor satisfies the protocol the locator needs."""
    assert isinstance(vendor, ToolkitVendor)


def test_the_driver_ceiling_excludes_newer_releases(vendor):
    """Check that a 13.1 driver with an Ada card gets 13.1.2, not 13.4.3."""
    assert vendor.choose(NvidiaHardware(("89",), (13, 1))) == "13.1.2"


def test_a_pascal_card_gets_the_newest_12x(vendor):
    """Check that sm_61 is given 12.9.2 under a 13.4 driver."""
    assert vendor.choose(NvidiaHardware(("61",), (13, 4))) == "12.9.2"


def test_a_compiler_that_does_not_run_is_skipped(vendor):
    """Check that a broken newest compiler makes the choice fall to the next major."""
    vendor.fake_installer.broken.add((13, 4, 3))

    assert vendor.choose(NvidiaHardware(("89",), (13, 4))) == "12.9.2"


def test_an_override_prefix_names_the_newest_match(vendor):
    """Check that ``12`` resolves to 12.9.2."""
    assert vendor.resolve_override("12") == "12.9.2"


def test_an_override_that_is_not_a_version_raises(vendor):
    """Check that a word is refused with the vendor's own error."""
    with pytest.raises(RedistError):
        vendor.resolve_override("latest")


def test_install_hands_the_release_of_the_label_to_the_installer(vendor):
    """Check that a label becomes the right release."""
    vendor.install("12.6.3")

    assert vendor.fake_installer.installed == ["12.6.3"]


def test_a_root_without_nvcc_is_not_a_toolkit(vendor, tmp_path):
    """Check that an empty folder is not taken for a toolkit."""
    assert not vendor.is_toolkit_root(tmp_path)
