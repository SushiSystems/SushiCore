# package_key.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The key that names one built package of a Sushi library."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

#: How many hex digits of the digest the short form keeps.
K_SHORT_LENGTH = 12


@dataclass(frozen=True, slots=True)
class PackageKey:
    """The parts that decide whether a built package can serve a consumer.

    Args:
        name: The library's lower-case name.
        source: The hash of the library's source content.
        toolchain: The identity of the SYCL compiler the consumer builds with.
        build_type: The build type, lower case.
        recipe: The build recipe: the lean flag set and the SushiCore version that drives it.
        inputs: The hash of the configure inputs: local config, vcpkg, triplet and CMake version.
        options: The extra arguments passed to the library's ``build``, in order.
        below: The ``(name, digest)`` of each Sushi package this one was built against.
    """

    name: str
    source: str
    toolchain: str
    build_type: str
    recipe: str
    inputs: str
    options: tuple[str, ...] = ()
    below: tuple[tuple[str, str], ...] = ()

    def parts(self) -> dict[str, Any]:
        """Return the parts as plain JSON values, ``below`` sorted by name."""
        return {
            "name": self.name,
            "source": self.source,
            "toolchain": self.toolchain,
            "build_type": self.build_type,
            "recipe": self.recipe,
            "inputs": self.inputs,
            "options": list(self.options),
            "below": [list(pair) for pair in sorted(self.below)],
        }

    def digest(self) -> str:
        """Return the SHA-256, as hex, of the canonical JSON of the parts."""
        text = json.dumps(self.parts(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def short(self) -> str:
        """Return the first :data:`K_SHORT_LENGTH` hex digits of the digest."""
        return self.digest()[:K_SHORT_LENGTH]
