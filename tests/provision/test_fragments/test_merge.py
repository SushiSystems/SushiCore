# test_merge.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests two modules declaring one dependency and what the merge does with both."""

from __future__ import annotations

import pytest

from sushicore.provision.fragments import Dependency, TomlDependencySource


pytestmark = pytest.mark.medium

K_DIGEST = "3f" * 32
K_OTHER_DIGEST = "a0" * 32


def _merged(tmp_path, *declarations: tuple[str, str]) -> Dependency:
    """Writes one fragment per (owner, sdl2 table body), in order, and returns the merged sdl2."""
    sources = []
    for owner, body in declarations:
        path = tmp_path / f"{owner}.deps.toml"
        path.write_text(f"[sdl2]\n{body}", encoding="utf-8")
        sources.append((path, owner))
    (dependency,) = TomlDependencySource(sources).all()
    return dependency


@pytest.mark.parametrize(
    "declarations",
    [
        (("a", 'windows_vcpkg = ["sdl2"]\n'), ("b", 'windows_vcpkg = ["sdl2[vulkan]"]\n')),
        (("b", 'windows_vcpkg = ["sdl2[vulkan]"]\n'), ("a", 'windows_vcpkg = ["sdl2"]\n')),
    ],
    ids=["plain first", "featured first"],
)
def test_the_order_of_the_two_does_not_decide(tmp_path, declarations):
    """Merging either way round keeps the feature, so file order decides nothing."""
    assert _merged(tmp_path, *declarations).windows_vcpkg == ["sdl2[vulkan]"]


def test_the_module_that_requires_it_owns_it(tmp_path):
    """Ownership follows need: the optional declarer read first does not claim the entry."""
    merged = _merged(tmp_path, ("sushidsp", "required = false\n"), ("sushiruntime", "required = true\n"))
    assert (merged.owner, merged.required) == ("sushiruntime", True)


def test_gpu_only_holds_only_when_both_say_so(tmp_path):
    """One module needing it on every machine settles it for the workspace."""
    assert _merged(tmp_path, ("a", "gpu_only = true\n"), ("b", "gpu_only = false\n")).gpu_only is False


def test_two_different_check_commands_are_reported(tmp_path, recording_console):
    """A field that cannot be merged keeps the first and is named rather than dropped in silence."""
    merged = _merged(
        tmp_path, ("a", 'check_cmd = ["which", "sdl2-config"]\n'), ("b", 'check_cmd = ["pkg-config", "sdl2"]\n'),
    )
    (warning,) = recording_console.texts("warn")
    assert merged.check_cmd == ["which", "sdl2-config"]
    assert ("check_cmd" in warning, "a" in warning, "b" in warning) == (True, True, True)


def test_ports_of_different_names_both_survive(tmp_path):
    """The union is per port, not a choice between the two lists."""
    merged = _merged(tmp_path, ("a", 'windows_vcpkg = ["gtest"]\n'), ("b", 'windows_vcpkg = ["sdl2[vulkan]"]\n'))
    assert merged.windows_vcpkg == ["gtest", "sdl2[vulkan]"]


def test_features_from_both_sides_are_collected(tmp_path):
    """Two modules asking for different features get a port carrying both."""
    merged = _merged(tmp_path, ("a", 'windows_vcpkg = ["sdl2[vulkan]"]\n'), ("b", 'windows_vcpkg = ["sdl2[x11]"]\n'))
    assert merged.windows_vcpkg == ["sdl2[vulkan,x11]"]


def test_the_aggregation_keeps_the_feature_across_two_fragments(tmp_path):
    """The required declarer read first keeps the entry, and the other's feature joins it."""
    merged = _merged(
        tmp_path,
        ("sushidsp", 'required = true\nwindows_vcpkg = ["sdl2"]\n'),
        ("sushiengine", 'required = false\nwindows_vcpkg = ["sdl2[vulkan]"]\n'),
    )
    assert (merged.windows_vcpkg, merged.required, merged.owner) == (["sdl2[vulkan]"], True, "sushidsp")


def test_a_digest_declared_by_one_module_survives(tmp_path):
    """A module that pins nothing does not unpin what another module pinned."""
    merged = _merged(tmp_path, ("a", ""), ("b", f'sha256 = {{ windows = "{K_DIGEST}" }}\n'))
    assert merged.sha256 == {"windows": K_DIGEST}


def test_digests_for_different_platforms_are_both_kept(tmp_path):
    """Two modules pinning one platform each leave both platforms pinned."""
    merged = _merged(
        tmp_path,
        ("a", f'sha256 = {{ windows = "{K_DIGEST}" }}\n'),
        ("b", f'sha256 = {{ linux = "{K_OTHER_DIGEST}" }}\n'),
    )
    assert merged.sha256 == {"windows": K_DIGEST, "linux": K_OTHER_DIGEST}


def test_two_different_digests_for_one_platform_are_reported(tmp_path, recording_console):
    """Two pins for one file cannot both hold, so the first is kept and the clash is named."""
    merged = _merged(
        tmp_path,
        ("a", f'sha256 = {{ windows = "{K_DIGEST}" }}\n'),
        ("b", f'sha256 = {{ windows = "{K_OTHER_DIGEST}" }}\n'),
    )
    (warning,) = recording_console.texts("warn")
    assert merged.sha256 == {"windows": K_DIGEST}
    assert ("sha256" in warning, "a" in warning, "b" in warning) == (True, True, True)
