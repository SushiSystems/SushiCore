# environment.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The environment port a config loader reads variables through, and its process adapter."""

from __future__ import annotations

import os
from typing import Protocol


class Environment(Protocol):
    """The environment variables a loader needs, read by name."""

    def get(self, name: str, default: str | None = None) -> str | None:
        """Returns a variable's value, or the default when it is not set."""

    def has(self, name: str) -> bool:
        """Returns whether a variable is set, an empty value included."""


class ProcessEnvironment:
    """The environment of the running process, read live from ``os.environ``."""

    def get(self, name: str, default: str | None = None) -> str | None:
        """Returns a variable's value, or the default when it is not set."""
        return os.environ.get(name, default)

    def has(self, name: str) -> bool:
        """Returns whether a variable is set, an empty value included."""
        return name in os.environ
