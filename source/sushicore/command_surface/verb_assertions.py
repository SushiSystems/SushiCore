# verb_assertions.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Asserts, for a CLI's own tests, that its application registers each canonical verb it applies."""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from ..command_groups import missing_groups
from .errors import UnknownVerbError
from .verbs import K_CANONICAL_VERBS

if TYPE_CHECKING:
    import typer


def assert_registers_verbs(app: "typer.Typer", *, excluded: Iterable[str] = ()) -> None:
    """Fails when *app* lacks a canonical verb that is not in *excluded*.

    Args:
        app: The CLI's Typer application.
        excluded: The canonical verbs that do not apply to the CLI's repository, such as ``bench``
            in one with no benchmarks.

    Raises:
        UnknownVerbError: *excluded* names a verb that is not canonical.
        AssertionError: *app* lacks a verb that applies; the message names each one.
    """
    left_out = tuple(excluded)
    unknown = [verb for verb in left_out if verb not in K_CANONICAL_VERBS]
    if unknown:
        raise UnknownVerbError(f"{', '.join(unknown)} is not a canonical verb, so it cannot be excluded.")
    missing = missing_groups(app, [verb for verb in K_CANONICAL_VERBS if verb not in left_out])
    if missing:
        raise AssertionError(f"the application does not register the canonical verbs {', '.join(missing)}.")
