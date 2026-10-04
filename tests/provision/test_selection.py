# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the toolchain selection rule."""

from __future__ import annotations

import pytest

from sushicore.provision.fragments import Dependency, IDependencySource
from sushicore.provision.selection import COMPONENTS, derive, toolchain_keys


class _Source(IDependencySource):
    """A dependency source holding a fixed list."""

    def __init__(self, deps: list[Dependency]) -> None:
        """Hold *deps* as the declared dependencies."""
        self._deps = deps

    def all(self) -> list[Dependency]:
        """Return the fixed list."""
        return list(self._deps)


def _sycl(name: str) -> Dependency:
    """Return a toolchain dependency providing the SYCL capability."""
    return Dependency(name=name, provides="sycl-toolchain", owner="sushiruntime")


_RUNTIME = _Source([_sycl("intel-llvm"), _sycl("adaptivecpp"), _sycl("oneapi")])


def test_an_unsatisfied_group_turns_on_its_first_declared_member():
    """Check that an unsatisfied group turns on its first declared member."""
    selection = derive(_RUNTIME, present={})
    assert (selection.install_intel_llvm, selection.install_acpp, selection.oneapi) == (
        True, False, False)


def test_declaration_order_decides_the_default():
    """Check that declaration order decides the default."""
    source = _Source([_sycl("adaptivecpp"), _sycl("intel-llvm")])
    selection = derive(source, present={})
    assert (selection.install_acpp, selection.install_intel_llvm) == (True, False)


def test_a_satisfied_group_turns_nothing_on():
    """Check that a satisfied group turns nothing on."""
    selection = derive(_RUNTIME, present={"oneapi": True})
    assert not (selection.install_intel_llvm or selection.install_acpp or selection.oneapi)


def test_a_requested_key_turns_on_beside_the_default():
    """Check that a requested key turns on beside the default."""
    selection = derive(_RUNTIME, present={}, requested=["adaptivecpp"])
    assert (selection.install_intel_llvm, selection.install_acpp) == (True, True)


def test_a_requested_key_turns_on_in_a_satisfied_group():
    """Check that a requested key turns on in a satisfied group."""
    selection = derive(_RUNTIME, present={"intel-llvm": True}, requested=["oneapi"])
    assert (selection.install_intel_llvm, selection.oneapi) == (False, True)


def test_an_unknown_requested_key_raises_and_names_the_valid_ones():
    """Check that an unknown requested key raises and names the valid ones."""
    with pytest.raises(ValueError) as error:
        derive(_RUNTIME, present={}, requested=["typo"])
    assert all(key in str(error.value) for key in toolchain_keys())


def test_a_source_declaring_no_toolchain_selects_none():
    """Check that a source declaring no toolchain selects none."""
    selection = derive(_Source([Dependency(name="sdl2", owner="sushidsp")]), present={})
    assert not (selection.install_intel_llvm or selection.install_acpp or selection.oneapi)


def _with_gpu_dependency() -> _Source:
    """Return the runtime's toolchains plus one GPU-only dependency."""
    return _Source([*_RUNTIME.all(), Dependency(name="cuda", gpu_only=True, owner="sushiruntime")])


def test_gpu_turns_on_when_a_gpu_only_dependency_is_declared():
    """Check that gpu turns on when a gpu only dependency is declared."""
    assert derive(_with_gpu_dependency(), present={}).gpu is True


def test_gpu_stays_off_when_the_caller_refuses_it():
    """Check that gpu stays off when the caller refuses it."""
    assert derive(_with_gpu_dependency(), present={}, gpu=False).gpu is False


def test_gpu_stays_off_when_nothing_declared_needs_one():
    """Check that gpu stays off when nothing declared needs one."""
    assert derive(_RUNTIME, present={}).gpu is False


def test_the_component_table_names_every_selection_field():
    """Check that the component table names every selection field."""
    assert [c.field for c in COMPONENTS] == [
        "install_intel_llvm", "install_acpp", "oneapi", "gpu"]
