# test_registry.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The toolchain registry lists the declared toolchains in install order and rejects duplicates."""

from __future__ import annotations

import pytest

from sushicore.provision.pipeline import ToolchainSelection
from sushicore.provision.toolchains.adaptivecpp import AdaptiveCppToolchain
from sushicore.provision.toolchains.intel_llvm import IntelLlvmToolchain
from sushicore.provision.toolchains.oneapi import OneApiToolchain
from sushicore.provision.toolchains.registry import DEFAULT_REGISTRY, ToolchainRegistry
from sushicore.provision.toolchains.toolchain import Toolchain

pytestmark = pytest.mark.small


def test_the_declared_toolchains_install_in_the_order_llvm_acpp_oneapi():
    """Check that the declared set is intel-llvm, then AdaptiveCpp, then oneAPI."""
    assert [t.key for t in DEFAULT_REGISTRY.all()] == ["intel-llvm", "adaptivecpp", "oneapi"]


def test_every_declared_toolchain_selects_through_a_field_of_the_selection():
    """Check that each toolchain's selection field is a field the selection holds."""
    fields = ToolchainSelection().as_dict()
    assert [t.selection_field in fields for t in DEFAULT_REGISTRY.all()] == [True, True, True]


@pytest.mark.parametrize("toolchain", [IntelLlvmToolchain(), AdaptiveCppToolchain(), OneApiToolchain()])
def test_each_toolchain_answers_the_toolchain_contract(toolchain):
    """Check that each toolchain class satisfies the Toolchain protocol."""
    assert isinstance(toolchain, Toolchain)


def test_a_registered_toolchain_is_found_by_its_key():
    """Check that for_key returns the toolchain and None for an unknown key."""
    registry = ToolchainRegistry(DEFAULT_REGISTRY.all())
    assert (registry.for_key("oneapi"), registry.for_key("missing")) == (
        DEFAULT_REGISTRY.all()[2], None)


def test_a_duplicate_toolchain_is_refused():
    """Check that registering one toolchain twice raises ValueError."""
    first = DEFAULT_REGISTRY.all()[0]
    with pytest.raises(ValueError):
        ToolchainRegistry((first, first))
