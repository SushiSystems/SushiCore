# moved_name.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Resolves a name that moved to another module, warning that its old module path is deprecated."""

from __future__ import annotations

import importlib
from collections.abc import Mapping

from .deprecated_name import warn_deprecated


def moved_attribute(namespace: Mapping[str, object], moves: Mapping[str, str], name: str) -> object:
    """Return the object *name* now is, in the module *moves* names for it, with a warning.

    Called from a module's ``__getattr__``, so the warning points at the code that asked.

    Args:
        namespace: The module's globals; its ``__name__`` words the error.
        moves: Each moved name and the dotted path of the module that now holds it.
        name: The name asked for.

    Raises:
        AttributeError: *name* did not move out of the module.
    """
    destination = moves.get(name)
    if destination is None:
        raise AttributeError(f"module {namespace['__name__']!r} has no attribute {name!r}")
    warn_deprecated(f"{namespace['__name__']}.{name}", f"{destination}.{name}", depth=2)
    return getattr(importlib.import_module(destination), name)
