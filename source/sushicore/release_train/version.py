# version.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A release version and the next one."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import final

from .errors import ReleaseTrainError

K_PATTERN = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


@final
@dataclass(frozen=True, slots=True, order=True)
class Version:
    """A MAJOR.MINOR.PATCH version."""

    major: int
    minor: int
    patch: int

    @staticmethod
    def parse(text: str) -> "Version":
        """Return the version *text* names, with or without a leading v; raises ReleaseTrainError otherwise."""
        match = K_PATTERN.match(text.strip())
        if match is None:
            raise ReleaseTrainError(f"'{text}' is not a MAJOR.MINOR.PATCH version")
        return Version(*(int(part) for part in match.groups()))

    def next(self, part: str) -> "Version":
        """Return the version after this one, raising *part*: major, minor or patch."""
        if part == "major":
            return Version(self.major + 1, 0, 0)
        if part == "minor":
            return Version(self.major, self.minor + 1, 0)
        if part == "patch":
            return Version(self.major, self.minor, self.patch + 1)
        raise ReleaseTrainError(f"'{part}' is not major, minor or patch")

    @property
    def tag(self) -> str:
        """The git tag of the version, v and the dotted number."""
        return f"v{self}"

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
