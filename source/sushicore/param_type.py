# param_type.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Names the type of a Click or Typer parameter, whichever generation of the two built it.

Click, and the Typer releases that build on it, give a parameter a ``type`` object. A Typer
release that ships its own parser has no such object and describes the type in a
``type_descriptor`` instead. Both shapes are read here, so no caller learns which one it holds.
"""

from __future__ import annotations

import types
import typing
from typing import Any

K_CLICK_TYPE_NAMES = {"choice": "choice", "path": "path", "boolean": "boolean",
                      "integer": "integer", "integer range": "integer",
                      "float": "number", "float range": "number"}
K_ANNOTATION_TYPE_NAMES = ((bool, "boolean"), (int, "integer"), (float, "number"))
K_DEFAULT_NAME = "string"


def type_name(param: Any) -> str:
    """Returns one of the six type names the describe contract allows for *param*."""
    click_type = getattr(param, "type", None)
    if click_type is not None:
        return K_CLICK_TYPE_NAMES.get(str(getattr(click_type, "name", "")).lower(), K_DEFAULT_NAME)
    descriptor = param.type_descriptor
    if descriptor.is_choice:
        return "choice"
    if descriptor.is_path:
        return "path"
    element = _element(descriptor.annotation)
    for python_type, name in K_ANNOTATION_TYPE_NAMES:
        if isinstance(element, type) and issubclass(element, python_type):
            return name
    return K_DEFAULT_NAME


def choices(param: Any) -> list[str] | None:
    """Returns the values of a choice parameter as strings, or None for every other type."""
    click_type = getattr(param, "type", None)
    values = getattr(click_type if click_type is not None else param.type_descriptor, "choices", None)
    if values is None:
        return None
    return [str(getattr(value, "value", value)) for value in values]


def _element(annotation: Any) -> Any:
    """Returns what a list holds, or what an optional wraps, or the annotation itself."""
    origin = typing.get_origin(annotation)
    if origin is typing.Union or origin is types.UnionType:
        present = [arg for arg in typing.get_args(annotation) if arg is not type(None)]
        return _element(present[0]) if present else annotation
    if origin is list and typing.get_args(annotation):
        return _element(typing.get_args(annotation)[0])
    return annotation
