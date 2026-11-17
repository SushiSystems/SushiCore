# test_adapter_builder_compat.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the deprecated runner names of the adapter builder."""

from __future__ import annotations

import pytest

from sushicore.provision.gpu import adapter_builder
from sushicore.provision.gpu.adapter_builder_compat import K_RENAMES

pytestmark = pytest.mark.small


@pytest.mark.parametrize("old, new", sorted(K_RENAMES.items()))
def test_a_removed_name_resolves_to_the_object_that_replaced_it(old, new):
    """Check that the old name is the current object, not a copy."""
    with pytest.warns(DeprecationWarning):
        assert getattr(adapter_builder, old) is getattr(adapter_builder, new)


@pytest.mark.parametrize("old, new", sorted(K_RENAMES.items()))
def test_a_removed_name_warns_with_its_replacement_and_points_at_the_caller(old, new):
    """Check that the message names the replacement and the warning points at this file."""
    with pytest.warns(DeprecationWarning, match=new) as caught:
        getattr(adapter_builder, old)
    assert caught[0].filename == __file__


def test_the_removed_names_are_the_two_the_consumers_imported():
    """Check the table lists the command runner protocol and its subprocess implementation."""
    assert set(K_RENAMES) == {"CommandRunner", "SubprocessCommandRunner"}


def test_a_name_the_module_never_had_is_still_an_attribute_error():
    """Check that the module's fallback does not answer every name."""
    with pytest.raises(AttributeError, match="no_such_name"):
        adapter_builder.no_such_name


def test_a_current_name_is_found_without_a_warning(recwarn):
    """Check that the fallback is never reached for a name the module defines."""
    adapter_builder.BuildStepExecutor
    assert len(recwarn) == 0
