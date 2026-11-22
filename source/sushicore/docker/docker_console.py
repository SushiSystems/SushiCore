# docker_console.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The console the docker commands print through."""

from __future__ import annotations

from typing import Protocol


class DockerConsole(Protocol):
    """The calls a docker command makes: a header, and an info, a success and an error line."""

    def header(self, title: str, /) -> None:
        """Print a section title."""
        ...

    def info(self, msg: str, /) -> None:
        """Print an informational message."""
        ...

    def success(self, msg: str, /) -> None:
        """Print a success message."""
        ...

    def error(self, msg: str, /) -> None:
        """Print an error."""
        ...
