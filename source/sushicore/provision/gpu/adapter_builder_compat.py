# adapter_builder_compat.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The deprecated runner names ``sushicore.provision.gpu.adapter_builder`` exported before 0.16.0."""

from __future__ import annotations

from collections.abc import Mapping

from ...deprecated_name import warn_deprecated

#: Each removed name and the name that replaces it.
K_RENAMES = {
    "CommandRunner": "BuildStepExecutor",
    "SubprocessCommandRunner": "SubprocessBuildStepExecutor",
}


def renamed_attribute(namespace: Mapping[str, object], name: str) -> object:
    """Return the object a removed name stands for in *namespace*, with a deprecation warning.

    Called from the module's ``__getattr__``, so the warning points at the code that asked.

    Raises:
        AttributeError: *name* is not a removed name of the module.
    """
    replacement = K_RENAMES.get(name)
    if replacement is None:
        raise AttributeError(f"module {namespace['__name__']!r} has no attribute {name!r}")
    warn_deprecated(name, replacement, depth=2)
    return namespace[replacement]
