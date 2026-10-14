# rocm_package.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""One ROCm SDK tarball: a release built for one family of AMD cards."""

from __future__ import annotations

import dataclasses
import typing

Version = tuple[int, ...]

#: The character a family name uses for "any digit here", as in ``gfx110X``.
K_WILDCARD = "X"


@typing.final
@dataclasses.dataclass(frozen=True, slots=True)
class RocmPackage:
    """A tarball AMD publishes.

    Args:
        version: The ROCm release, such as ``(7, 13, 0)``.
        family: The family it is built for, such as ``gfx110X-all`` or ``gfx1151``.
        url: Where it is served.
    """

    version: Version
    family: str
    url: str

    @property
    def label(self) -> str:
        """Return the name its install folder takes, such as ``7.13.0-gfx110X-all``."""
        return f"{'.'.join(str(part) for part in self.version)}-{self.family}"

    @property
    def pattern(self) -> str:
        """Return the ISA pattern of the family without its variant: ``gfx110X``."""
        return self.family.split("-", 1)[0]

    def builds_for(self, target: str) -> bool:
        """Report whether the family covers the ISA *target*, such as ``gfx1103``."""
        pattern = self.pattern
        return len(pattern) == len(target) and all(
            p == t or p == K_WILDCARD for p, t in zip(pattern, target))

    def specificity(self) -> int:
        """Return how few cards beyond the named ones it carries code for; higher is leaner."""
        return -self.pattern.count(K_WILDCARD)
