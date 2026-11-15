# checkout_finder.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Finds the SushiCore checkout the shared tools are read from."""

from __future__ import annotations

from pathlib import Path

from ..provision.sushi_sources import resolve
from .errors import CheckoutNotFoundError

K_LIBRARY = "sushicore"


def find_checkout(root: Path, tag: str, explicit: Path | None = None) -> Path:
    """Returns the SushiCore checkout to read.

    That is *explicit* when given, else the sibling of *root* or the copy `setup` fetched for the tag.
    Raises CheckoutNotFoundError when there is none.
    """
    if explicit is not None:
        if not explicit.is_dir():
            raise CheckoutNotFoundError(f"--from {explicit} is not a directory")
        return explicit
    for version in (tag, tag.removeprefix("v")):
        found = resolve(root, K_LIBRARY, version)
        if found is not None:
            return found.path
    raise CheckoutNotFoundError(
        f"no SushiCore checkout beside {root} or fetched for {tag}; pass --from PATH"
    )
