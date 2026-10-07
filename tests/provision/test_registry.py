# test_registry.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the installed-component registry."""

from __future__ import annotations

import pytest

from sushicore.provision.registry import Component, Registry, RegistryError


def _llvm(consumer):
    """Check that llvm."""
    return Component("intel-llvm", "nightly-1", "/x", "intel/llvm", "2026-09-23T00:00:00Z",
                     (consumer,))


def test_empty_registry_has_no_components(tmp_path):
    """Check that empty registry has no components."""
    reg = Registry(tmp_path / "registry.toml")
    reg.load()
    assert reg.components() == []


def test_add_save_load_round_trips(tmp_path):
    """Check that add save load round trips."""
    path = tmp_path / "registry.toml"
    reg = Registry(path)
    reg.load()
    reg.add(_llvm("sushidsp"))
    reg.save()
    again = Registry(path)
    again.load()
    assert again.find("intel-llvm", "nightly-1").consumers == ("sushidsp",)


def test_second_consumer_merges_instead_of_duplicating(tmp_path):
    """Check that second consumer merges instead of duplicating."""
    reg = Registry(tmp_path / "r.toml")
    reg.load()
    reg.add(_llvm("sushidsp"))
    reg.add(_llvm("sushiruntime"))
    assert len(reg.components()) == 1
    assert set(reg.find("intel-llvm").consumers) == {"sushidsp", "sushiruntime"}


def test_release_keeps_a_component_another_consumer_uses(tmp_path):
    """Check that release keeps a component another consumer uses."""
    reg = Registry(tmp_path / "r.toml")
    reg.load()
    reg.add(_llvm("sushidsp"))
    reg.add(_llvm("sushiruntime"))
    assert reg.release("intel-llvm", "nightly-1", "sushidsp") is False
    assert reg.release("intel-llvm", "nightly-1", "sushiruntime") is True


def test_corrupt_registry_raises_instead_of_emptying(tmp_path):
    """Check that corrupt registry raises instead of emptying."""
    path = tmp_path / "registry.toml"
    path.write_text("[[component]\nname = ", encoding="utf-8")
    with pytest.raises(RegistryError, match="registry.toml"):
        Registry(path).load()


def test_save_leaves_no_temp_file(tmp_path):
    """Check that save leaves no temp file."""
    reg = Registry(tmp_path / "r.toml")
    reg.load()
    reg.add(_llvm("a"))
    reg.save()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["r.toml"]


def test_round_trip_preserves_unicode_and_special_characters(tmp_path):
    """Check that round trip preserves unicode and special characters."""
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
    """Check that find without version raises when ambiguous."""
    reg = Registry(tmp_path / "r.toml")
    reg.load()
    reg.add(Component("intel-llvm", "nightly-1", "/x", "intel/llvm",
                      "2026-09-23T00:00:00Z", ("sushidsp",)))
    reg.add(Component("intel-llvm", "nightly-2", "/y", "intel/llvm",
                      "2026-09-23T00:00:00Z", ("sushidsp",)))
    with pytest.raises(RegistryError, match="intel-llvm"):
        reg.find("intel-llvm")


def test_entry_missing_a_field_raises_naming_the_file(tmp_path):
    """Check that entry missing a field raises naming the file."""
    path = tmp_path / "registry.toml"
    path.write_text(
        '[[component]]\nname = "intel-llvm"\nversion = "nightly-1"\n', encoding="utf-8")
    with pytest.raises(RegistryError, match="registry.toml"):
        Registry(path).load()


def test_seed_records_each_component_with_its_stamp_version(tmp_path):
    """Check that seed records each component with the tag its stamp holds."""
    root = tmp_path / "root"
    llvm = root / "toolchains" / "llvm-sycl"
    llvm.mkdir(parents=True)
    (llvm / ".sushi_toolchain.json").write_text('{"tag": "2026-07-28"}', encoding="utf-8")
    (root / "tools" / "cmake").mkdir(parents=True)
    (root / "ur" / "cuda-d5f649b").mkdir(parents=True)
    (root / "vcpkg").mkdir()
    reg = Registry(root / "registry.toml")
    added = reg.seed_from_tree(root, consumer="hub")
    found = {(c.name, c.version) for c in added}
    assert found == {
        ("llvm-sycl", "2026-07-28"),
        ("cmake", "unversioned"),
        ("cuda-d5f649b", "unversioned"),
        ("vcpkg", "unversioned"),
    }
    assert reg.find("llvm-sycl").path == llvm.as_posix()
    assert reg.find("llvm-sycl").source == "migrated"
    assert reg.find("llvm-sycl").consumers == ("hub",)


def test_seed_skips_components_already_recorded(tmp_path):
    """Check that seed skips components already recorded."""
    root = tmp_path / "root"
    (root / "vcpkg").mkdir(parents=True)
    reg = Registry(root / "registry.toml")
    reg.seed_from_tree(root, consumer="hub")
    assert reg.seed_from_tree(root, consumer="hub") == []


def test_seed_of_an_empty_tree_adds_nothing(tmp_path):
    """Check that seed of a tree with no component adds nothing."""
    reg = Registry(tmp_path / "registry.toml")
    assert reg.seed_from_tree(tmp_path, consumer="hub") == []
