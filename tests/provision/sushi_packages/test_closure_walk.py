# test_closure_walk.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the walk over a consumer's chain."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.deps_fragment import Fragment, SushiPin
from sushicore.provision.sushi_packages.closure_walk import ClosureWalk
from sushicore.provision.sushi_packages.package_error import PackageError
from sushicore.provision.sushi_packages.package_request import PackageRequest
from sushicore.provision.sushi_packages.source_locator import MemoryLocator

pytestmark = pytest.mark.small

K_ROOT = Path("ws")
K_FRAGMENT = "cli/sushistack.deps.toml"
K_NAMES = ("sushilog", "sushiruntime", "sushiblas", "sushiai")


def _fragment(depends_on=(), cli="x", pins=()) -> Fragment:
    """Return a fragment that depends on *depends_on* and pins *pins*."""
    return Fragment([], list(depends_on), list(pins), cli)


def _diamond() -> dict[Path, Fragment]:
    """Return the fragments of the diamond: AI, BLAS, Runtime and Log, by path."""
    return {
        K_ROOT / "sushilog" / K_FRAGMENT: _fragment(),
        K_ROOT / "sushiruntime" / K_FRAGMENT: _fragment(("sushilog",)),
        K_ROOT / "sushiblas" / K_FRAGMENT: _fragment(("sushiruntime", "sushilog")),
        K_ROOT / "sushiai" / K_FRAGMENT: _fragment(("sushiblas", "sushiruntime"), cli=""),
    }


def _locator() -> MemoryLocator:
    """Return a locator that knows every library of the diamond beside the consumer."""
    return MemoryLocator({name: K_ROOT / name for name in K_NAMES})


def _walk(read, locator=None):
    """Return the nodes the walk lists for the consumer, reading fragments through *read*."""
    request = PackageRequest("sushiai", K_ROOT / "sushiai", "c", "release")
    return ClosureWalk(locator or _locator(), read).walk(request)


def test_the_diamond_lists_the_runtime_once_before_blas():
    """Check the dependency order and that no library appears twice."""
    names = [node.name for node in _walk(_diamond().get)]
    assert names == ["sushilog", "sushiruntime", "sushiblas"]


def test_a_node_carries_its_cli_and_dependencies():
    """Check the fields of a node read from the fragment."""
    blas = _walk(_diamond().get)[2]
    assert (blas.cli, blas.depends_on) == ("x", ("sushiruntime", "sushilog"))
    assert blas.checkout == K_ROOT / "sushiblas"


def test_a_cycle_raises_naming_the_trail():
    """Check that two libraries depending on each other are refused."""
    fragments = _diamond()
    fragments[K_ROOT / "sushilog" / K_FRAGMENT] = _fragment(("sushiruntime",))
    with pytest.raises(PackageError, match="sushiai -> sushiblas -> sushiruntime -> sushilog"):
        _walk(fragments.get)


def _refuse(_path):
    """Read a fragment the way a reader that refuses its content does."""
    raise ValueError("cli must be a text")


def test_a_malformed_fragment_raises_a_package_error():
    """Check that a fragment the reader refuses reaches the caller as a package error."""
    with pytest.raises(PackageError, match="cli"):
        _walk(_refuse)


def test_the_pin_of_the_consumer_decides_the_version():
    """Check that the consumer's pin is the version handed to the locator."""
    fragments = _diamond()
    pin = SushiPin("sushilog", "v1.0.0", "a" * 40)
    fragments[K_ROOT / "sushiai" / K_FRAGMENT] = _fragment(("sushilog",), cli="", pins=(pin,))
    locator = _locator()
    _walk(fragments.get, locator)
    assert locator.asked == [("sushilog", "v1.0.0")]
