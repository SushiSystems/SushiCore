# test_build_types.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that a command's build types hold their default and offer themselves as Typer choices."""

import pytest

from sushicore.command_surface import BuildTypeError, BuildTypes

pytestmark = pytest.mark.small


def test_build_types_refuse_an_empty_set():
    with pytest.raises(BuildTypeError):
        BuildTypes((), "debug")


def test_build_types_refuse_a_default_outside_the_set():
    with pytest.raises(BuildTypeError, match="minsizerel"):
        BuildTypes(("debug", "release"), "minsizerel")


def test_build_types_choice_has_one_string_member_per_type():
    choice = BuildTypes(("debug", "release"), "debug").choice()
    assert [member.value for member in choice] == ["debug", "release"]
    assert choice("release") == "release"
