# current.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Picks the host this process runs on; the one place that reads the operating system."""

from __future__ import annotations

import os

from .base import IHost
from .posix import PosixHost
from .windows import WindowsHost


def current_host() -> IHost:
    """Return the host of the running operating system."""
    return WindowsHost() if os.name == "nt" else PosixHost()
