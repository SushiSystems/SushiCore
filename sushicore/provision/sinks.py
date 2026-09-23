# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Where ConfigureStep's results are written."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from ..config_base import write_toml_document, write_tool_section
from ..workspace import WORKSPACE_HEADER, read_toml, workspace_file


class ConfigSink(Protocol):
    """A destination ConfigureStep writes probed tool paths and settings to."""

    target: Path

    def write_paths(self, platform: str, values: dict[str, str]) -> Path:
        """Merge *values* into this sink's ``[tool.<platform>]`` table."""

    def write_tool(self, updates: dict[str, str]) -> Path:
        """Merge *updates* into this sink's top-level ``[tool]`` table."""

    def clear(self) -> None:
        """Remove this sink's ``[tool]`` table, leaving any other data intact."""


def write_platform_paths(
    target: Path, platform: str, values: dict[str, str], header: list[str]
) -> Path:
    """Merge *values* into *target*'s ``[tool.<platform>]`` table.

    Goes through :func:`write_toml_document`, so any other table sharing the
    file (a module registry, a workspace version) is re-emitted unchanged.

    Returns:
        The path written.
    """
    document = dict(read_toml(target))
    tool = dict(document.get("tool", {}))
    tool[platform] = {**tool.get(platform, {}), **values}
    document["tool"] = tool
    target.parent.mkdir(parents=True, exist_ok=True)
    return write_toml_document(target, document, header)


def render_local_config(platform: str, values: dict[str, str]) -> str:
    """Render *values* as a standalone ``[tool.<platform>]`` TOML document."""
    lines = [
        "# Auto-generated. Machine-specific tool paths.",
        "# Safe to edit; re-running configure backs this up first.",
        "",
        f"[tool.{platform}]",
    ]
    for key in sorted(values):
        val = values[key].replace("\\", "/")
        lines.append(f'{key} = "{val}"')
    lines.append("")
    return "\n".join(lines)


def _clear_tool_table(target: Path, header: list[str]) -> None:
    """Drop *target*'s ``[tool]`` table, deleting the file if nothing else remains."""
    document = dict(read_toml(target))
    if "tool" not in document:
        return
    del document["tool"]
    if not document:
        target.unlink(missing_ok=True)
        return
    write_toml_document(target, document, header)
    # write_toml_document always renders an empty `[tool]` header; strip it so it parses away.
    text = target.read_text(encoding="utf-8")
    target.write_text(text.replace("\n[tool]\n\n", "\n", 1), encoding="utf-8")


class WorkspaceSink:
    """A :class:`ConfigSink` writing into a workspace's shared ``workspace.toml``."""

    def __init__(self, root: Path) -> None:
        """Bind this sink to *root*'s workspace file."""
        self.target = workspace_file(root)
        self._header = WORKSPACE_HEADER

    def write_paths(self, platform: str, values: dict[str, str]) -> Path:
        """Merge *values* into this workspace's ``[tool.<platform>]`` table."""
        return write_platform_paths(self.target, platform, values, self._header)

    def write_tool(self, updates: dict[str, str]) -> Path:
        """Merge *updates* into this workspace's top-level ``[tool]`` table."""
        return write_tool_section(self.target, updates, self._header)

    def clear(self) -> None:
        """Remove the ``[tool]`` table, leaving the module registry intact."""
        _clear_tool_table(self.target, self._header)


class ModuleSink:
    """A :class:`ConfigSink` writing into a module's own ``config.local.toml``."""

    def __init__(self, config_dir: Path, header: list[str]) -> None:
        """Bind this sink to *config_dir*'s local config file, rendered with *header*."""
        self.target = config_dir / "config.local.toml"
        self._header = header

    def write_paths(self, platform: str, values: dict[str, str]) -> Path:
        """Merge *values* into this module's ``[tool.<platform>]`` table."""
        return write_platform_paths(self.target, platform, values, self._header)

    def write_tool(self, updates: dict[str, str]) -> Path:
        """Merge *updates* into this module's top-level ``[tool]`` table."""
        return write_tool_section(self.target, updates, self._header)

    def clear(self) -> None:
        """Remove the ``[tool]`` table, deleting the file if nothing else remains."""
        _clear_tool_table(self.target, self._header)
