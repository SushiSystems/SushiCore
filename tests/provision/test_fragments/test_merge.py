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


def _merged(tmp_path, *declarations: tuple[str, str], console) -> Dependency:
    """Writes one fragment per (owner, sdl2 table body), in order, and returns the merged sdl2."""
    sources = []
    for owner, body in declarations:
        path = tmp_path / f"{owner}.deps.toml"
        path.write_text(f"[sdl2]\n{body}", encoding="utf-8")
        sources.append((path, owner))
    (dependency,) = TomlDependencySource(sources, console=console).all()
    return dependency


@pytest.mark.parametrize(
    "declarations",
    [
        (("a", 'windows_vcpkg = ["sdl2"]\n'), ("b", 'windows_vcpkg = ["sdl2[vulkan]"]\n')),
        (("b", 'windows_vcpkg = ["sdl2[vulkan]"]\n'), ("a", 'windows_vcpkg = ["sdl2"]\n')),
    ],
    ids=["plain first", "featured first"],
)
def test_the_order_of_the_two_does_not_decide(tmp_path, declarations, recording_console):
    """Merging either way round keeps the feature, so file order decides nothing."""
    assert _merged(tmp_path, *declarations,
                   console=recording_console).windows_vcpkg == ["sdl2[vulkan]"]


def test_the_module_that_requires_it_owns_it(tmp_path, recording_console):
    """Ownership follows need: the optional declarer read first does not claim the entry."""
    merged = _merged(tmp_path, ("sushidsp", "required = false\n"), ("sushiruntime",
                                                                    "required = true\n"),
                                                                    console=recording_console)
    assert (merged.owner, merged.required) == ("sushiruntime", True)


def test_gpu_only_holds_only_when_both_say_so(tmp_path, recording_console):
    """One module needing it on every machine settles it for the workspace."""
    assert _merged(tmp_path, ("a", "gpu_only = true\n"), ("b", "gpu_only = false\n"),
                   console=recording_console).gpu_only is False


def test_two_different_check_commands_are_reported(tmp_path, recording_console):
    """A field that cannot be merged keeps the first and is named rather than dropped in silence."""
    merged = _merged(
        tmp_path, ("a", 'check_cmd = ["which", "sdl2-config"]\n'), ("b", 'check_cmd = ["pkg-config", "sdl2"]\n'),
     console=recording_console)
    (warning,) = recording_console.texts("warn")
    assert merged.check_cmd == ["which", "sdl2-config"]
    assert ("check_cmd" in warning, "a" in warning, "b" in warning) == (True, True, True)


def test_ports_of_different_names_both_survive(tmp_path, recording_console):
    """The union is per port, not a choice between the two lists."""
    merged = _merged(tmp_path, ("a", 'windows_vcpkg = ["gtest"]\n'),
                     ("b", 'windows_vcpkg = ["sdl2[vulkan]"]\n'), console=recording_console)
    assert merged.windows_vcpkg == ["gtest", "sdl2[vulkan]"]


def test_features_from_both_sides_are_collected(tmp_path, recording_console):
    """Two modules asking for different features get a port carrying both."""
    merged = _merged(tmp_path, ("a", 'windows_vcpkg = ["sdl2[vulkan]"]\n'),
                     ("b", 'windows_vcpkg = ["sdl2[x11]"]\n'), console=recording_console)
    assert merged.windows_vcpkg == ["sdl2[vulkan,x11]"]


def test_the_aggregation_keeps_the_feature_across_two_fragments(tmp_path, recording_console):
    """The required declarer read first keeps the entry, and the other's feature joins it."""
    merged = _merged(
        tmp_path,
        ("sushidsp", 'required = true\nwindows_vcpkg = ["sdl2"]\n'),
        ("sushiengine", 'required = false\nwindows_vcpkg = ["sdl2[vulkan]"]\n'),
     console=recording_console)
    assert (merged.windows_vcpkg, merged.required, merged.owner) == (["sdl2[vulkan]"], True, "sushidsp")


def _download(platform: str, digest: str, version: str = "v1") -> str:
    """Return the keys of a whole download for *platform*, pinned to *digest*."""
    return (f'version = "{version}"\n'
            f'url = {{ {platform} = "https://example.invalid/{platform}.zip" }}\n'
            f'sha256 = {{ {platform} = "{digest}" }}\n')


def test_a_digest_declared_by_one_module_survives(tmp_path, recording_console):
    """A module that pins nothing does not unpin what another module pinned."""
    merged = _merged(tmp_path, ("a", ""), ("b", _download("windows", K_DIGEST)),
                     console=recording_console)
    assert merged.sha256 == {"windows": K_DIGEST}


def test_digests_for_different_platforms_are_both_kept(tmp_path, recording_console):
    """Two modules pinning one platform each leave both platforms pinned."""
    merged = _merged(
        tmp_path,
        ("a", _download("windows", K_DIGEST)),
        ("b", _download("linux", K_OTHER_DIGEST)),
     console=recording_console)
    assert merged.sha256 == {"windows": K_DIGEST, "linux": K_OTHER_DIGEST}


def test_two_different_digests_for_one_platform_are_reported(tmp_path, recording_console):
    """Two pins for one file cannot both hold, so the first is kept and the clash is named."""
    merged = _merged(
        tmp_path,
        ("a", _download("windows", K_DIGEST)),
        ("b", _download("windows", K_OTHER_DIGEST)),
     console=recording_console)
    (warning,) = recording_console.texts("warn")
    assert merged.sha256 == {"windows": K_DIGEST}
    assert ("sha256" in warning, "a" in warning, "b" in warning) == (True, True, True)


def test_a_url_and_a_version_declared_by_one_module_survive(tmp_path, recording_console):
    """A module that pins nothing does not unpin the download another module pinned."""
    merged = _merged(tmp_path, ("a", ""), ("b", _download("windows", K_DIGEST, "v2")),
                     console=recording_console)
    assert (merged.version, merged.url) == ("v2", {"windows": "https://example.invalid/windows.zip"})


def test_two_versions_of_one_download_are_reported(tmp_path, recording_console):
    """Two pins of different versions cannot both hold, so the first is kept and the clash named."""
    merged = _merged(
        tmp_path,
        ("a", _download("windows", K_DIGEST, "v1")),
        ("b", _download("windows", K_DIGEST, "v2")),
     console=recording_console)
    (warning,) = recording_console.texts("warn")
    assert merged.version == "v1"
    assert "version" in warning
