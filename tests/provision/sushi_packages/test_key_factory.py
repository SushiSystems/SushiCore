# test_key_factory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the composition of a package key."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.sushi_packages.configure_inputs import (
    ConfigureInputs,
    MemoryCMakeVersion,
    MemoryVcpkgHead,
)
from sushicore.provision.sushi_packages.key_factory import KeyFactory
from sushicore.provision.sushi_packages.library_node import LibraryNode
from sushicore.provision.sushi_packages.package_request import PackageRequest
from sushicore.provision.sushi_packages.source_state import MemoryInspector
from sushicore.provision.sushi_packages.toolchain_identity import MemoryIdentity

pytestmark = pytest.mark.medium


@pytest.fixture
def node(tmp_path):
    """Return a library node over a checkout with one source file."""
    (tmp_path / "a.cpp").write_text("x", encoding="utf-8")
    return LibraryNode("sushiruntime", tmp_path, "sr", (), ())


def _factory_for(node, version="1", identity=None):
    """Return a factory whose inspector lists the one source file of *node*."""
    inspector = MemoryInspector({node.checkout: [Path("a.cpp")]})
    return KeyFactory(inspector, ConfigureInputs(MemoryCMakeVersion(), MemoryVcpkgHead()),
                      identity or MemoryIdentity(), version)


def _request(tmp_path, **changes):
    """Return a request for a consumer at *tmp_path*."""
    values = {"owner": "sushiai", "root": tmp_path, "compiler": "clang++", "build_type": "Release"}
    values.update(changes)
    return PackageRequest(**values)


def test_the_key_names_the_library_of_the_node(node, tmp_path):
    """Check that the key carries the name of the node."""
    assert _factory_for(node).make(node, _request(tmp_path), ()).name == "sushiruntime"


def test_the_key_lowers_the_build_type(node, tmp_path):
    """Check that the build type of the request is written in lower case."""
    assert _factory_for(node).make(node, _request(tmp_path), ()).build_type == "release"


def test_the_key_carries_the_identity_of_the_compiler(node, tmp_path):
    """Check that the toolchain of the key is the identity of the request's compiler."""
    factory = _factory_for(node, identity=MemoryIdentity("tc9"))
    assert factory.make(node, _request(tmp_path), ()).toolchain == "tc9"


def test_the_key_takes_the_options_of_its_library(node, tmp_path):
    """Check that the key holds the options the request names for the node's library."""
    request = _request(tmp_path, options={"sushiruntime": ("--distributed",),
                                          "sushiblas": ("--other",)})
    assert _factory_for(node).make(node, request, ()).options == ("--distributed",)


def test_the_key_records_the_packages_below(node, tmp_path):
    """Check that the key holds the packages it was built against."""
    key = _factory_for(node).make(node, _request(tmp_path), (("sushilog", "d"),))
    assert key.below == (("sushilog", "d"),)


def test_the_sushicore_version_is_part_of_the_recipe(node, tmp_path):
    """Check that another SushiCore version gives another digest."""
    request = _request(tmp_path)
    assert (_factory_for(node, "1").make(node, request, ()).digest()
            != _factory_for(node, "2").make(node, request, ()).digest())


def test_the_compiler_is_probed_once(node, tmp_path):
    """Check that two keys for one compiler run one probe."""
    identity = MemoryIdentity()
    factory = _factory_for(node, identity=identity)
    factory.make(node, _request(tmp_path), ())
    factory.make(node, _request(tmp_path), ())
    assert identity.asked == ["clang++"]
