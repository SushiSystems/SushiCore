# link_pointer.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Reads and edits the ``[link]`` pointer a module keeps in its local config to name its workspace."""

from __future__ import annotations

import re
from pathlib import Path

from .errors import SushiCoreError
from .files import Files
from .layered_toml import has_marker, read_toml
from .workspace import WORKSPACE_MARKER

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # Python 3.10 fallback
    import tomli as tomllib

#: Table in a module's ``config.local.toml`` naming the workspace it is linked to.
LINK_SECTION = "link"

#: File in a module's config directory that carries the link pointer.
_LOCAL_CONFIG = "config.local.toml"

#: A ``[link]`` header line, with optional inner spaces and a trailing comment.
_LINK_HEADER_RE = re.compile(r"^\s*\[\s*" + LINK_SECTION + r"\s*\]\s*(#.*)?$")


class LinkEditError(SushiCoreError, ValueError):
    """Raised when the link pointer cannot be edited without corrupting the file."""


def _link_block_span(lines: list[str]) -> tuple[int, int] | None:
    """Return the ``[start, end)`` line span of the ``[link]`` table in *lines*, or None."""
    for start, line in enumerate(lines):
        if _LINK_HEADER_RE.match(line):
            end = start + 1
            while end < len(lines) and not lines[end].lstrip().startswith("["):
                end += 1
            # Blank and comment lines just above the next header belong to that table.
            while end > start + 1 and lines[end - 1].strip()[:1] in ("", "#"):
                end -= 1
            return start, end
    return None


def _toml_string(value: str) -> str:
    """Return *value* as a quoted TOML basic string."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _splice_link(text: str, block: list[str]) -> str:
    """Return *text* with its ``[link]`` block replaced by *block*, keeping its line endings.

    An empty *block* removes the table; a missing table is appended.
    """
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines()
    span = _link_block_span(lines)
    if span is not None:
        lines[span[0]:span[1]] = block
    elif block:
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend(block)
    body = newline.join(lines).strip("\r\n")
    return body + newline if body.strip() else ""


def _parse(path: Path, text: str) -> dict:
    """Parse *text*, the content of *path*, as TOML.

    @throws LinkEditError When *text* is not valid TOML.
    """
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise LinkEditError(f"{path}: cannot edit [{LINK_SECTION}] safely ({exc}); "
                            "edit it by hand.") from exc


def _verified_link(path: Path, before: str, after: str) -> object:
    """Return the ``link`` value of *after* once every other key matches *before*.

    @throws LinkEditError When either text is invalid or they differ outside ``link``.
    """
    old = _parse(path, before)
    new = _parse(path, after)
    link = new.pop(LINK_SECTION, None)
    old.pop(LINK_SECTION, None)
    if old != new:
        raise LinkEditError(f"{path}: cannot edit [{LINK_SECTION}] without changing other "
                            "settings; edit it by hand.")
    return link


def _read_local(path: Path) -> str:
    """Return *path*'s text with its line endings intact, or "" when it does not exist."""
    return path.read_bytes().decode("utf-8") if path.is_file() else ""


def read_link(config_dir: Path, *, files: Files | None = None) -> Path | None:
    """Return the workspace this module is linked to, or None when unlinked or stale.

    @param files The file system read through; the disk when None. A path in memory is joined, not
           resolved.
    """
    table = read_toml(config_dir / _LOCAL_CONFIG, files=files).get(LINK_SECTION) or {}
    raw = table.get("workspace")
    if not raw:
        return None
    target = config_dir / raw
    if files is None:
        target = target.resolve()
    return target if has_marker(WORKSPACE_MARKER, files=files)(target) else None


def write_link(config_dir: Path, workspace: Path) -> Path:
    """Set the ``[link]`` table in *config_dir*'s local config, leaving other text untouched.

    @pre *config_dir* exists.
    @throws LinkEditError When the edit cannot be verified; the file is then left unchanged.
    @return The file written.
    """
    path = config_dir / _LOCAL_CONFIG
    value = workspace.resolve().as_posix()
    block = [f"[{LINK_SECTION}]", f"workspace = {_toml_string(value)}"]
    original = _read_local(path)
    text = _splice_link(original, block)
    link = _verified_link(path, original, text)
    if not isinstance(link, dict) or link.get("workspace") != value:
        raise LinkEditError(f"{path}: could not set [{LINK_SECTION}] workspace safely; "
                            "edit it by hand.")
    path.write_bytes(text.encode("utf-8"))
    return path


def clear_link(config_dir: Path) -> bool:
    """Remove the ``[link]`` table from *config_dir*'s local config; report whether it existed.

    The file is deleted when only blank lines remain.

    @throws LinkEditError When the edit cannot be verified; the file is then left unchanged.
    """
    path = config_dir / _LOCAL_CONFIG
    original = _read_local(path)
    if LINK_SECTION not in _parse(path, original):
        return False
    text = _splice_link(original, [])
    if _verified_link(path, original, text) is not None:
        raise LinkEditError(f"{path}: could not remove [{LINK_SECTION}] safely; "
                            "edit it by hand.")
    if text:
        path.write_bytes(text.encode("utf-8"))
    else:
        path.unlink()
    return True
