# test_param_type.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that a parameter's type is named the same from a Click type and from a Typer descriptor."""

from __future__ import annotations

import enum
from types import SimpleNamespace
from typing import Optional

import pytest

from sushicore.param_type import choices, type_name


pytestmark = pytest.mark.small


class _Kind(enum.Enum):
    """Two values a choice parameter offers."""

    A = "a"
    B = "b"


def _click_param(name: str, values: tuple | None = None) -> SimpleNamespace:
    """Returns a parameter that carries a Click ``type`` object, as Click and older Typer build it."""
    return SimpleNamespace(type=SimpleNamespace(name=name, choices=values))


def _descriptor_param(annotation, *, values: tuple | None = None, is_path: bool = False) -> SimpleNamespace:
    """Returns a parameter that carries only a ``type_descriptor``, as a Typer with its own parser builds it."""
    descriptor = SimpleNamespace(annotation=annotation, choices=values,
                                 is_choice=values is not None, is_path=is_path)
    return SimpleNamespace(type_descriptor=descriptor)


@pytest.mark.parametrize(("param", "expected"), [
    (_click_param("text"), "string"),
    (_click_param("integer"), "integer"),
    (_click_param("integer range"), "integer"),
    (_click_param("float range"), "number"),
    (_click_param("boolean"), "boolean"),
    (_click_param("path"), "path"),
    (_click_param("choice", ("a", "b")), "choice"),
    (_descriptor_param(str), "string"),
    (_descriptor_param(int), "integer"),
    (_descriptor_param(float), "number"),
    (_descriptor_param(bool), "boolean"),
    (_descriptor_param(Optional[int]), "integer"),
    (_descriptor_param(list[float]), "number"),
    (_descriptor_param(str, is_path=True), "path"),
    (_descriptor_param(_Kind, values=(_Kind.A, _Kind.B)), "choice"),
])
def test_type_name_gives_one_of_the_contract_names_for_both_shapes(param, expected):
    assert type_name(param) == expected


@pytest.mark.parametrize(("param", "expected"), [
    (_click_param("choice", ("a", "b")), ["a", "b"]),
    (_click_param("text"), None),
    (_descriptor_param(_Kind, values=(_Kind.A, _Kind.B)), ["a", "b"]),
    (_descriptor_param(str), None),
])
def test_choices_lists_the_values_of_a_choice_for_both_shapes(param, expected):
    assert choices(param) == expected
