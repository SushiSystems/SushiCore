# toml_writer.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Writes the small TOML documents the workspace file and the local config files are."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


def _emit_table(name: str, table: dict) -> list[str]:
    """Render one top-level table of string values as TOML lines.

    Backslashes become forward slashes, as they do for the ``[tool.<platform>]``
    paths above: a Windows path written raw into a basic string is an invalid
    escape, and the file would not parse the next time it is read.

    @pre *table* is a table of string values; anything else raises, because
        silently dropping it is how a caller loses data it thought was saved.
    """
    if not isinstance(table, dict):
        raise TypeError(
            f"[{name}]: only tables are preserved, got {type(table).__name__}")
    lines = ["", f"[{name}]"]
    for key in sorted(table):
        value = table[key]
        if not isinstance(value, str):
            raise TypeError(
                f"[{name}] {key}: only string values are preserved, got {type(value).__name__}")
        lines.append(f'{key} = "{value.replace(chr(92), "/")}"')
    return lines


def write_toml_document(target: Path, tables: dict, header_lines: Iterable[str]) -> Path:
    """Render *tables* as a whole TOML document and write it to *target*.

    ``tool`` is rendered first — its scalars under ``[tool]``, its sub-tables
    (the machine-specific paths a probe wrote) as ``[tool.<platform>]`` — then
    every other table follows, sorted by name. Backslashes become forward
    slashes throughout, and a value the emitter cannot render raises rather
    than disappearing. Returns the path written.

    @pre Every table in *tables* holds only strings, bools, or nested tables
        of strings; anything else raises.
    """
    tool = dict(tables.get("tool", {}))
    scalars = {k: v for k, v in tool.items() if not isinstance(v, dict)}
    subtables = {k: v for k, v in tool.items() if isinstance(v, dict)}

    lines = list(header_lines) + ["", "[tool]"]
    for key in sorted(scalars):
        val = scalars[key]
        if isinstance(val, bool):
            lines.append(f"{key} = {'true' if val else 'false'}")
        else:
            lines.append(f'{key} = "{val}"')
    for tname in sorted(subtables):
        lines.append("")
        lines.append(f"[tool.{tname}]")
        for key in sorted(subtables[tname]):
            val = str(subtables[tname][key]).replace("\\", "/")
            lines.append(f'{key} = "{val}"')

    for name in sorted(k for k in tables if k != "tool"):
        lines.extend(_emit_table(name, tables[name]))
    lines.append("")

    target.write_text("\n".join(lines), encoding="utf-8")
    return target
