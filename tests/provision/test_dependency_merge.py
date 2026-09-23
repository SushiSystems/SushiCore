# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests two modules declaring one dependency and what the merge does with both."""

from __future__ import annotations

from sushicore.provision.fragments import Dependency, TomlDependencySource, _merge, _merge_ports


def _dep(owner: str, **overrides) -> Dependency:
    """Build a dependency named sdl2, owned by *owner*, with fields overridden."""
    fields = dict(name="sdl2", description="", required=False, gpu_only=False,
                  linux_apt=[], windows_vcpkg=[], check_cmd=[], owner=owner, provides="")
    fields.update(overrides)
    return Dependency(**fields)


def test_a_feature_set_survives_a_plainer_declaration():
    """sdl2 and sdl2[vulkan] name one port at two strengths; the features stay."""
    merged, warning = _merge(_dep("sushidsp", windows_vcpkg=["sdl2"]),
                             _dep("sushiengine", windows_vcpkg=["sdl2[vulkan]"]))

    assert merged.windows_vcpkg == ["sdl2[vulkan]"]
    assert warning == ""


def test_the_order_of_the_two_does_not_decide():
    """Merging either way round gives the same answer, so alphabet decides nothing."""
    one = _merge(_dep("a", windows_vcpkg=["sdl2"]), _dep("b", windows_vcpkg=["sdl2[vulkan]"]))[0]
    two = _merge(_dep("b", windows_vcpkg=["sdl2[vulkan]"]), _dep("a", windows_vcpkg=["sdl2"]))[0]

    assert one.windows_vcpkg == two.windows_vcpkg == ["sdl2[vulkan]"]


def test_required_by_one_is_required():
    """A module that can do without it does not excuse the module that cannot."""
    merged, _ = _merge(_dep("sushidsp", required=False), _dep("sushiruntime", required=True))

    assert merged.required is True


def test_the_module_that_requires_it_owns_it():
    """Ownership follows need: the optional declarer does not claim the entry."""
    merged, _ = _merge(_dep("sushidsp", required=False), _dep("sushiruntime", required=True))

    assert merged.owner == "sushiruntime"


def test_gpu_only_holds_only_when_both_say_so():
    """One module needing it on every machine settles it for the workspace."""
    merged, _ = _merge(_dep("a", gpu_only=True), _dep("b", gpu_only=False))

    assert merged.gpu_only is False


def test_two_different_check_commands_are_reported():
    """A field that cannot be merged is named rather than dropped in silence."""
    merged, warning = _merge(_dep("a", check_cmd=["which", "sdl2-config"]),
                             _dep("b", check_cmd=["pkg-config", "sdl2"]))

    assert merged.check_cmd == ["which", "sdl2-config"]
    assert "check_cmd" in warning
    assert "a" in warning and "b" in warning


def test_ports_of_different_names_both_survive():
    """The union is per port, not a choice between the two lists."""
    assert _merge_ports(["gtest"], ["sdl2[vulkan]"]) == ["gtest", "sdl2[vulkan]"]


def test_features_from_both_sides_are_collected():
    """Two modules asking for different features get a port carrying both."""
    assert _merge_ports(["sdl2[vulkan]"], ["sdl2[x11]"]) == ["sdl2[vulkan,x11]"]


def test_the_aggregation_keeps_the_feature_across_two_fragments(tmp_path, recording_console):
    """Merges two fragment files declaring the same dependency with different features."""
    dsp = tmp_path / "dsp.deps.toml"
    dsp.write_text('[sdl2]\nrequired = true\nwindows_vcpkg = ["sdl2"]\n', encoding="utf-8")
    engine = tmp_path / "engine.deps.toml"
    engine.write_text('[sdl2]\nrequired = false\nwindows_vcpkg = ["sdl2[vulkan]"]\n',
                      encoding="utf-8")

    by_name = {d.name: d
               for d in TomlDependencySource([(dsp, "sushidsp"), (engine, "sushiengine")]).all()}

    assert by_name["sdl2"].windows_vcpkg == ["sdl2[vulkan]"]
    assert by_name["sdl2"].required is True
    assert by_name["sdl2"].owner == "sushidsp"
