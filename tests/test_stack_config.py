# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the toolchain resolution of a module that consumes the shared tree."""

from __future__ import annotations

from dataclasses import dataclass

from sushicore.provision.config import ProvisionSettings
from sushicore.stack_config import StackConfig


@dataclass
class _Config(StackConfig):
    """A stack config naming one sibling."""

    sushiruntime_dir: str = ""


def _clang(root):
    """Create a clang++ under *root*'s llvm-sycl bundle and return it."""
    exe = root / "toolchains" / "llvm-sycl" / "bin" / "clang++"
    exe.parent.mkdir(parents=True)
    exe.write_text("")
    return exe


def test_a_stack_config_carries_the_provision_fields():
    """Check that a stack config carries the provision fields."""
    assert issubclass(StackConfig, ProvisionSettings)


def test_bundled_clang_is_found_under_the_provision_root(provision_home, tmp_path):
    """Check that bundled clang is found under the provision root."""
    exe = _clang(provision_home)
    assert _Config(platform="linux").bundled_clang(tmp_path) == str(exe)


def test_a_workspace_tree_wins_over_the_provision_root(provision_home, tmp_path):
    """Check that a workspace tree wins over the provision root."""
    workspace = tmp_path / "ws"
    (workspace / ".sushistack").mkdir(parents=True)
    module = workspace / "sushiblas"
    module.mkdir()
    _clang(provision_home)
    exe = _clang(workspace / "dependencies")
    assert _Config(platform="linux").bundled_clang(module) == str(exe)


def test_the_environment_override_is_the_only_root(provision_home, tmp_path, monkeypatch):
    """Check that the environment override is the only root."""
    _clang(provision_home)
    monkeypatch.setenv("SUSHISTACK_DEPS_DIR", str(tmp_path / "empty"))
    assert _Config(platform="linux").bundled_clang(tmp_path) == ""


def test_resolved_vcpkg_finds_the_provision_root_tree(provision_home, tmp_path):
    """Check that resolved vcpkg finds the provision root tree."""
    (provision_home / "vcpkg").mkdir(parents=True)
    assert _Config(platform="linux").resolved_vcpkg(tmp_path) == str(provision_home / "vcpkg")


def test_locate_sibling_returns_the_directory_beside_the_root(tmp_path):
    """Check that locate sibling returns the directory beside the root."""
    root = tmp_path / "sushiblas"
    root.mkdir()
    (tmp_path / "sushiruntime").mkdir()
    found = _Config(platform="linux").locate_sibling(root, "sushiruntime")
    assert found == (tmp_path / "sushiruntime").resolve()


def test_locate_sibling_prefers_the_configured_directory(tmp_path):
    """Check that locate sibling prefers the configured directory."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    cfg = _Config(platform="linux", sushiruntime_dir=str(elsewhere))
    assert cfg.locate_sibling(tmp_path / "sushiblas", "sushiruntime") == elsewhere.resolve()


def test_locate_sibling_is_none_without_a_checkout(tmp_path):
    """Check that locate sibling is none without a checkout."""
    assert _Config(platform="linux").locate_sibling(tmp_path / "x", "sushiruntime") is None


def test_a_linked_workspace_tree_is_searched(provision_home, tmp_path):
    """Check that a linked workspace tree is searched."""
    from sushicore.workspace import write_link

    workspace = tmp_path / "ws"
    (workspace / ".sushistack").mkdir(parents=True)
    module = tmp_path / "elsewhere" / "sushiblas"
    (module / "cli").mkdir(parents=True)
    write_link(module / "cli", workspace)
    exe = _clang(workspace / "dependencies")
    assert _Config(platform="linux").bundled_clang(module) == str(exe.resolve())


def test_a_pinned_llvm_root_wins_when_its_compiler_exists(provision_home, tmp_path):
    """Check that a pinned llvm root wins when its compiler exists."""
    _clang(provision_home)
    pinned = tmp_path / "pinned"
    exe = pinned / "bin" / "clang++"
    exe.parent.mkdir(parents=True)
    exe.write_text("")
    cfg = _Config(platform="linux", llvm_root=str(pinned))
    assert cfg.bundled_clang(tmp_path) == str(exe)
