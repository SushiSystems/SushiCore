# test_key_factory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the composition of a package key."""

from __future__ import annotations

import pytest

from sushicore.provision.sushi_packages.configure_inputs import ConfigureInputs
from sushicore.provision.sushi_packages.key_factory import KeyFactory
from sushicore.provision.sushi_packages.library_node import LibraryNode
from sushicore.provision.sushi_packages.package_request import PackageRequest

from .package_fakes import ListInspector

pytestmark = pytest.mark.medium


def _factory(version="1", identity="tc", calls=None):
    """Return a factory whose compiler identity is *identity*."""
    def identify(compiler):
        """Count the probes and answer the identity."""
        if calls is not None:
            calls.append(compiler)
        return identity

    return KeyFactory(ListInspector(), ConfigureInputs(lambda: "3.28.1", lambda _r: ""),
                      identify, version)


@pytest.fixture
def node(tmp_path):
    """Return a library node over a checkout with one source file."""
    (tmp_path / "a.cpp").write_text("x", encoding="utf-8")
    return LibraryNode("sushiruntime", tmp_path, "sr", (), ())


def _request(tmp_path, **changes):
    """Return a request for a consumer at *tmp_path*."""
    values = {"owner": "sushiai", "root": tmp_path, "compiler": "clang++", "build_type": "Release"}
    values.update(changes)
    return PackageRequest(**values)


def test_the_key_composes_every_part(node, tmp_path):
    """Check name, build type in lower case, toolchain, options and below."""
    request = _request(tmp_path, options={"sushiruntime": ("--distributed",)})
    key = _factory().make(node, request, (("sushilog", "d"),))
    assert (key.name, key.build_type, key.toolchain) == ("sushiruntime", "release", "tc")
    assert key.options == ("--distributed",) and key.below == (("sushilog", "d"),)


def test_the_sushicore_version_is_part_of_the_recipe(node, tmp_path):
    """Check that another SushiCore version gives another digest."""
    request = _request(tmp_path)
    assert (_factory("1").make(node, request, ()).digest()
            != _factory("2").make(node, request, ()).digest())


def test_the_compiler_is_probed_once(node, tmp_path):
    """Check that two keys for one compiler run one probe."""
    calls: list[str] = []
    factory = _factory(calls=calls)
    factory.make(node, _request(tmp_path), ())
    factory.make(node, _request(tmp_path), ())
    assert calls == ["clang++"]


def test_a_docs_only_difference_leaves_the_digest(node, tmp_path):
    """Check that a page next to the source does not change the key."""
    request = _request(tmp_path)
    before = _factory().make(node, request, ()).digest()
    (tmp_path / "NOTES.md").write_text("n", encoding="utf-8")
    assert _factory().make(node, request, ()).digest() == before
