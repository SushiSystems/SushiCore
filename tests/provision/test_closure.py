# test_closure.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the dependency closure."""

from __future__ import annotations

import pytest

from sushicore.provision.closure import DEFAULT_FRAGMENT, resolve


def _module(tmp_path, name, depends_on=()):
    """Create a checkout named *name* whose fragment depends on *depends_on*."""
    root = tmp_path / name
    fragment = root / DEFAULT_FRAGMENT
    fragment.parent.mkdir(parents=True)
    names = ", ".join(f'"{dep}"' for dep in depends_on)
    fragment.write_text(f"[module]\ndepends_on = [{names}]\n", encoding="utf-8")
    return root


def _sibling(tmp_path):
    """Return a locator that finds a module as a directory under *tmp_path*."""
    def locate(name):
        """Return the sibling directory when it exists."""
        path = tmp_path / name
        return path if path.is_dir() else None
    return locate


def test_a_module_with_no_dependencies_is_its_own_closure(tmp_path):
    """Check that a module with no dependencies is its own closure."""
    root = _module(tmp_path, "sushiruntime")
    closure = resolve("sushiruntime", root, _sibling(tmp_path))
    assert closure.sources == ((root / DEFAULT_FRAGMENT, "sushiruntime"),)
    assert closure.missing == ()


def test_a_chain_is_ordered_dependencies_first(tmp_path):
    """Check that a chain is ordered dependencies first."""
    _module(tmp_path, "sushiruntime")
    _module(tmp_path, "sushiblas", ["sushiruntime"])
    root = _module(tmp_path, "sushiai", ["sushiruntime", "sushiblas"])
    closure = resolve("sushiai", root, _sibling(tmp_path))
    assert [owner for _path, owner in closure.sources] == [
        "sushiruntime", "sushiblas", "sushiai"]


def test_shared_fragments_come_first(tmp_path):
    """Check that shared fragments come first."""
    root = _module(tmp_path, "sushiruntime")
    base = tmp_path / "base.deps.toml"
    base.write_text("", encoding="utf-8")
    closure = resolve("sushiruntime", root, _sibling(tmp_path), shared=[(base, "shared")])
    assert closure.sources[0] == (base, "shared")


def test_a_missing_checkout_is_reported_with_who_wanted_it(tmp_path):
    """Check that a missing checkout is reported with who wanted it."""
    root = _module(tmp_path, "sushiblas", ["sushiruntime"])
    closure = resolve("sushiblas", root, _sibling(tmp_path))
    assert closure.missing == (("sushiruntime", "sushiblas"),)
    assert [owner for _path, owner in closure.sources] == ["sushiblas"]


def test_a_missing_middle_module_hides_nothing_above_it(tmp_path):
    """Check that a missing middle module hides nothing above it."""
    _module(tmp_path, "sushiruntime")
    root = _module(tmp_path, "sushiai", ["sushiruntime", "sushiblas"])
    closure = resolve("sushiai", root, _sibling(tmp_path))
    assert closure.missing == (("sushiblas", "sushiai"),)
    assert [owner for _path, owner in closure.sources] == ["sushiruntime", "sushiai"]


def test_a_checkout_without_a_fragment_is_present_and_empty(tmp_path):
    """Check that a checkout without a fragment is present and empty."""
    (tmp_path / "sushiruntime").mkdir()
    root = _module(tmp_path, "sushiblas", ["sushiruntime"])
    closure = resolve("sushiblas", root, _sibling(tmp_path))
    assert closure.missing == ()
    assert [owner for _path, owner in closure.sources] == ["sushiblas"]


def test_a_cycle_raises(tmp_path):
    """Check that a cycle raises."""
    _module(tmp_path, "a", ["b"])
    root = _module(tmp_path, "b", ["a"])
    with pytest.raises(ValueError, match="cycle"):
        resolve("b", root, _sibling(tmp_path))


def test_a_module_without_its_own_fragment_resolves_to_shared_only(tmp_path):
    """Check that a module without its own fragment resolves to shared only."""
    root = tmp_path / "bare"
    root.mkdir()
    assert resolve("bare", root, _sibling(tmp_path)).sources == ()
