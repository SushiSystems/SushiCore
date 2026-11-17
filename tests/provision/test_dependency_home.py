# test_dependency_home.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the object that holds the provider of the dependency root."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision import home
from sushicore.provision.dependency_home import DEFAULT_HOME, DependencyHome

pytestmark = pytest.mark.small


def test_a_new_home_holds_no_provider():
    assert DependencyHome().provider is None


def test_a_bound_provider_is_returned_and_unbinding_clears_it():
    held = DependencyHome()
    held.bind(lambda: Path("/deps"))
    assert held.provider is not None
    held.bind(None)
    assert held.provider is None


def test_root_reads_the_provider_of_the_home_it_is_passed():
    held = DependencyHome(lambda: Path.cwd() / "held-root")
    assert home.root(home=held) == (Path.cwd() / "held-root").resolve()


def test_root_of_one_home_does_not_see_another_homes_provider():
    other = DependencyHome(lambda: Path.cwd() / "other")
    plain = DependencyHome()
    assert home.root(home=plain, environ={}, user_home=Path("/u")) == Path("/u") / ".sushisystems"
    assert home.root(home=other) == (Path.cwd() / "other").resolve()


def test_bind_root_warns_and_sets_the_default_home():
    try:
        with pytest.warns(DeprecationWarning, match="bind_root"):
            home.bind_root(lambda: Path.cwd() / "shim-root")
        assert home.root() == (Path.cwd() / "shim-root").resolve()
    finally:
        DEFAULT_HOME.bind(None)


def test_every_root_helper_reads_the_home_it_is_passed():
    held = DependencyHome(lambda: Path.cwd() / "held-root")
    base = (Path.cwd() / "held-root").resolve()
    assert home.toolchains_dir(home=held) == base / "toolchains"
    assert home.tools_dir(home=held) == base / "tools"
    assert home.sources_dir(home=held) == base / "sources"
    assert home.build_dir(home=held) == base / "build"
    assert home.ur_dir(home=held) == base / "ur"
    assert home.search_roots(home=held, legacy=None)[0] == base
