# sinks_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A config sink that records what it is asked to write and touches no file."""

from __future__ import annotations

from pathlib import Path


class InMemoryConfigSink:
    """Records every call a step makes on it, in order, and writes nothing.

    Args:
        target: The path this sink reports as its file.
        backup_path: What ``backup`` returns; ``None`` stands for a file with nothing to back up.

    Attributes:
        calls: The name of each method called, in call order.
        paths: The ``(platform, values)`` of each ``write_paths`` call.
        tool: The ``updates`` of each ``write_tool`` call.
    """

    def __init__(self, target: Path = Path("config.local.toml"),
                 backup_path: Path | None = None) -> None:
        """Start with no recorded calls."""
        self.target = target
        self._backup_path = backup_path
        self.calls: list[str] = []
        self.paths: list[tuple[str, dict[str, str]]] = []
        self.tool: list[dict[str, str]] = []

    def backup(self) -> Path | None:
        """Record the call and return the backup path this sink was given."""
        self.calls.append("backup")
        return self._backup_path

    def write_paths(self, platform: str, values: dict[str, str]) -> Path:
        """Record *platform* and a copy of *values*; return the target."""
        self.calls.append("write_paths")
        self.paths.append((platform, dict(values)))
        return self.target

    def write_tool(self, updates: dict[str, str]) -> Path:
        """Record a copy of *updates*; return the target."""
        self.calls.append("write_tool")
        self.tool.append(dict(updates))
        return self.target

    def clear(self) -> None:
        """Record the call."""
        self.calls.append("clear")
