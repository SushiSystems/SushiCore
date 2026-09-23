# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the installed-component registry."""

from __future__ import annotations

import pytest

from sushicore.provision.registry import Component, Registry, RegistryError


def _llvm(consumer):
    return Component("intel-llvm", "nightly-1", "/x", "intel/llvm", "2026-09-23T00:00:00Z",
                     (consumer,))


def test_empty_registry_has_no_components(tmp_path):
    reg = Registry(tmp_path / "registry.toml")
    reg.load()
    assert reg.components() == []


def test_add_save_load_round_trips(tmp_path):
    path = tmp_path / "registry.toml"
    reg = Registry(path)
    reg.load()
    reg.add(_llvm("sushidsp"))
    reg.save()
    again = Registry(path)
    again.load()
    assert again.find("intel-llvm", "nightly-1").consumers == ("sushidsp",)


def test_second_consumer_merges_instead_of_duplicating(tmp_path):
    reg = Registry(tmp_path / "r.toml")
    reg.load()
    reg.add(_llvm("sushidsp"))
    reg.add(_llvm("sushiruntime"))
    assert len(reg.components()) == 1
    assert set(reg.find("intel-llvm").consumers) == {"sushidsp", "sushiruntime"}


def test_release_keeps_a_component_another_consumer_uses(tmp_path):
    reg = Registry(tmp_path / "r.toml")
    reg.load()
    reg.add(_llvm("sushidsp"))
    reg.add(_llvm("sushiruntime"))
    assert reg.release("intel-llvm", "nightly-1", "sushidsp") is False
    assert reg.release("intel-llvm", "nightly-1", "sushiruntime") is True


def test_corrupt_registry_raises_instead_of_emptying(tmp_path):
    path = tmp_path / "registry.toml"
    path.write_text("[[component]\nname = ", encoding="utf-8")
    with pytest.raises(RegistryError, match="registry.toml"):
        Registry(path).load()


def test_save_leaves_no_temp_file(tmp_path):
    reg = Registry(tmp_path / "r.toml")
    reg.load()
    reg.add(_llvm("a"))
    reg.save()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["r.toml"]
