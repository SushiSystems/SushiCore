# build_tree.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Names the build tree of a configuration: one tree for every source state of it."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

#: The folder, below the library's ``build``, that holds package build trees.
K_PREFIX = "pkg-"

#: How many hex digits of the configuration hash the tree name keeps.
K_ID_LENGTH = 12


@dataclass(frozen=True, slots=True)
class BuildTree:
    """The configuration identity of a package build: build type, options and toolchain."""

    build_type: str
    options: tuple[str, ...]
    toolchain: str

    @property
    def id(self) -> str:
        """Return the first :data:`K_ID_LENGTH` hex digits of the hash of the three parts."""
        text = json.dumps([self.build_type, list(self.options), self.toolchain],
                          separators=(",", ":"))
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:K_ID_LENGTH]

    @property
    def folder(self) -> str:
        """Return the folder name, ``pkg-<id>``."""
        return f"{K_PREFIX}{self.id}"
