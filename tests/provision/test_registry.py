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


def test_round_trip_preserves_unicode_and_special_characters(tmp_path):
    path = tmp_path / "r.toml"
    reg = Registry(path)
    reg.load()
    reg.add(Component("sushi", "1", 'C:\\Users\\x\\path "q"', "src",
                      "2026-09-23T00:00:00Z", ("\U0001F363",)))
    reg.save()
    again = Registry(path)
    again.load()
    component = again.find("sushi", "1")
    assert component.path == 'C:\\Users\\x\\path "q"'
    assert component.consumers == ("\U0001F363",)


def test_find_without_version_raises_when_ambiguous(tmp_path):
    reg = Registry(tmp_path / "r.toml")
    reg.load()
    reg.add(Component("intel-llvm", "nightly-1", "/x", "intel/llvm",
                      "2026-09-23T00:00:00Z", ("sushidsp",)))
    reg.add(Component("intel-llvm", "nightly-2", "/y", "intel/llvm",
                      "2026-09-23T00:00:00Z", ("sushidsp",)))
    with pytest.raises(RegistryError, match="intel-llvm"):
        reg.find("intel-llvm")


def test_entry_missing_a_field_raises_naming_the_file(tmp_path):
    path = tmp_path / "registry.toml"
    path.write_text(
        '[[component]]\nname = "intel-llvm"\nversion = "nightly-1"\n', encoding="utf-8")
    with pytest.raises(RegistryError, match="registry.toml"):
        Registry(path).load()
