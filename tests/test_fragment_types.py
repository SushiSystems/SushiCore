# test_fragment_types.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What an entry says about the packages and the download it declares, per platform."""

from __future__ import annotations

import pytest

from sushicore import deps_fragment, fragment_types
from sushicore.fragment_types import Dependency, Download

K_URL = "https://example.invalid/c.zip"
K_DIGEST = "3f" * 32


@pytest.mark.small
def test_download_for_names_the_pin_of_a_platform_the_entry_covers():
    """An entry with a url and a digest for a platform answers the download of that platform."""
    dep = Dependency(name="cmake", version="v1", url={"windows": K_URL},
                     sha256={"windows": K_DIGEST})
    assert dep.download_for("windows") == Download("cmake", "v1", K_URL, K_DIGEST)


@pytest.mark.small
def test_download_for_answers_none_for_a_platform_the_entry_leaves_out():
    """A platform with no url or no digest has no download to verify."""
    dep = Dependency(name="cmake", version="v1", url={"windows": K_URL},
                     sha256={"windows": K_DIGEST})
    assert dep.download_for("linux") is None


@pytest.mark.small
@pytest.mark.parametrize(("platform", "expected"), [("windows", ["port"]), ("linux", ["pkg"])])
def test_packages_for_picks_vcpkg_on_windows_and_apt_elsewhere(platform, expected):
    """The platform string selects the column of package names."""
    dep = Dependency(name="x", windows_vcpkg=["port"], linux_apt=["pkg"])
    assert dep.packages_for(platform) == expected


@pytest.mark.small
def test_the_reader_module_still_exports_the_types_callers_import_from_it():
    """The types moved, and an import from deps_fragment keeps resolving to them."""
    assert deps_fragment.Dependency is fragment_types.Dependency
    assert deps_fragment.Download is fragment_types.Download
