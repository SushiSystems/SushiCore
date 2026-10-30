# module_manifest.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Reads what a module declares about itself in its manifest, where provisioning needs it."""

from __future__ import annotations

from pathlib import Path

from ..workspace import read_toml
from .closure import DEFAULT_FRAGMENT

K_MANIFEST = "sushi-module.toml"
K_FRAGMENT_KEY = "fragment"


def fragment_path(root: Path) -> str:
    """Returns the dependency fragment of the module at *root*, relative to it.

    The manifest's ``[module] fragment`` key names it; a manifest without the key, a malformed
    value or no manifest leaves the default.
    """
    declared = read_toml(root / K_MANIFEST).get("module", {}).get(K_FRAGMENT_KEY)
    return declared if isinstance(declared, str) and declared.strip() else DEFAULT_FRAGMENT
