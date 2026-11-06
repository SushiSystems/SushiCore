# test_cuda_vendor_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the in-memory redistributable index and installer promise as stand-ins for their ports."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.gpu.cuda_release import RedistRelease
from sushicore.provision.gpu.cuda_toolkit_installer import ToolkitInstallError
from sushicore.provision.gpu.cuda_vendor_memory import (
    InMemoryRedistIndex,
    InMemoryRedistInstaller,
)

pytestmark = pytest.mark.small

K_ARCHITECTURES = {13: frozenset({"75"}), 12: frozenset({"61"})}


def test_the_index_lists_the_versions_it_was_given_in_order():
    """Check that the versions come back as given."""
    assert InMemoryRedistIndex([(13, 1, 2), (12, 6, 3)]).versions() == [(13, 1, 2), (12, 6, 3)]


def test_the_index_releases_hold_the_version_and_no_archive():
    """Check that a release carries its version and an empty archive table."""
    release = InMemoryRedistIndex([(13, 1, 2)]).release((13, 1, 2), "linux-x86_64")

    assert release == RedistRelease((13, 1, 2), {})


def test_the_installer_probe_answers_the_architectures_of_the_releases_major():
    """Check that the probe answers the table row of the release's major."""
    installer = InMemoryRedistInstaller(K_ARCHITECTURES)

    assert installer.probe_architectures(RedistRelease((12, 9, 1), {})) == frozenset({"61"})


def test_the_installer_probe_raises_for_a_broken_compiler():
    """Check that a version listed as broken raises ToolkitInstallError."""
    installer = InMemoryRedistInstaller(K_ARCHITECTURES, broken=[(13, 4, 3)])

    with pytest.raises(ToolkitInstallError):
        installer.probe_architectures(RedistRelease((13, 4, 3), {}))


def test_the_installer_records_the_label_and_returns_the_release_folder():
    """Check that an install records the label and returns the folder under the base."""
    installer = InMemoryRedistInstaller(K_ARCHITECTURES, base_dir=Path("base"))

    root = installer.install(RedistRelease((12, 6, 3), {}))

    assert installer.installed == ["12.6.3"]
    assert root == Path("base") / "12.6.3"
