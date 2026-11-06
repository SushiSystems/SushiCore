# test_cuda_vendor.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""NVIDIA's answers: the driver ceiling, the compiler's architectures and the override."""

from __future__ import annotations

import pytest

from sushicore.provision.gpu.cuda_hardware import NvidiaHardware
from sushicore.provision.gpu.cuda_redist import RedistError
from sushicore.provision.gpu.cuda_vendor import CudaVendor
from sushicore.provision.gpu.cuda_vendor_memory import (
    InMemoryRedistIndex,
    InMemoryRedistInstaller,
)

K_VERSIONS = [(13, 4, 3), (13, 1, 2), (12, 9, 2), (12, 6, 3)]

#: 13.x builds sm_75 and newer, 12.x builds sm_61 too.
K_ARCHITECTURES = {13: frozenset({"75", "89"}), 12: frozenset({"61", "89"})}


def _vendor(**installer_options) -> tuple[CudaVendor, InMemoryRedistInstaller]:
    """Return a CUDA vendor over the in-memory index and installer, and the installer."""
    installer = InMemoryRedistInstaller(K_ARCHITECTURES, **installer_options)
    return CudaVendor(lambda: None, InMemoryRedistIndex(K_VERSIONS), installer), installer


@pytest.mark.small
@pytest.mark.parametrize(("cards", "ceiling", "expected"), [
    (("89",), (13, 1), "13.1.2"),
    (("61",), (13, 4), "12.9.2"),
], ids=["driver-ceiling-excludes-newer", "pascal-gets-the-newest-12x"])
def test_choose_gives_the_newest_release_the_driver_runs_and_the_cards_fit(
        recording_console, cards, ceiling, expected):
    """Check that the driver ceiling and the cards' architectures pick the release."""
    vendor, _installer = _vendor()

    assert vendor.choose(NvidiaHardware(cards, ceiling)) == expected


@pytest.mark.small
def test_a_compiler_that_does_not_run_is_skipped(recording_console):
    """Check that a broken newest compiler makes the choice fall to the next major."""
    vendor, _installer = _vendor(broken=[(13, 4, 3)])

    assert vendor.choose(NvidiaHardware(("89",), (13, 4))) == "12.9.2"


@pytest.mark.small
def test_a_skipped_compiler_is_reported(recording_console):
    """Check that the console says which release was skipped and why."""
    vendor, _installer = _vendor(broken=[(13, 4, 3)])

    vendor.choose(NvidiaHardware(("89",), (13, 4)))

    assert recording_console.texts("warn") == ["CUDA 13.4.3 skipped: nvcc did not run"]


@pytest.mark.small
def test_an_override_prefix_names_the_newest_match():
    """Check that ``12`` resolves to 12.9.2."""
    vendor, _installer = _vendor()

    assert vendor.resolve_override("12") == "12.9.2"


@pytest.mark.small
def test_an_override_that_is_not_a_version_raises():
    """Check that a word is refused with the vendor's own error."""
    vendor, _installer = _vendor()

    with pytest.raises(RedistError):
        vendor.resolve_override("latest")


@pytest.mark.small
def test_install_hands_the_release_of_the_label_to_the_installer():
    """Check that a label becomes the right release."""
    vendor, installer = _vendor()

    vendor.install("12.6.3")

    assert installer.installed == ["12.6.3"]


@pytest.mark.medium
def test_a_root_without_nvcc_is_not_a_toolkit(tmp_path):
    """Check that an empty folder is not taken for a toolkit."""
    vendor, _installer = _vendor()

    assert not vendor.is_toolkit_root(tmp_path)
