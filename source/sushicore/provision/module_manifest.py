# module_manifest.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Reads what a module declares about itself in its manifest, where provisioning needs it."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from ..workspace import read_toml
from .closure import DEFAULT_FRAGMENT

K_MANIFEST = "sushi-module.toml"
K_FRAGMENT_KEY = "fragment"


def fragment_from(manifest: Mapping) -> str:
    """Returns the dependency fragment a parsed manifest names, relative to the module.

    The manifest's ``[module] fragment`` key names it; a manifest without the key or with a
    malformed value leaves the default.
    """
    declared = manifest.get("module", {}).get(K_FRAGMENT_KEY)
    return declared if isinstance(declared, str) and declared.strip() else DEFAULT_FRAGMENT


def fragment_path(root: Path) -> str:
    """Returns the dependency fragment of the module at *root*, relative to it.

    No manifest leaves the default; otherwise :func:`fragment_from` reads the manifest.
    """
    return fragment_from(read_toml(root / K_MANIFEST))
