"""Shared build-tool config schema and load/write skeleton for the Sushi* CLIs.

Every module CLI (`sr`, `se`, `hub`) shells out to the same host build tools —
cmake, ninja, vcpkg, a vcvars batch on Windows — and so carries the same handful
of tool-path fields plus the same layered-load and ``[tool]``-write skeleton.
That generic part lives here as :class:`ToolConfig` and the two helpers below.

This module deliberately knows nothing about SYCL, toolchains, or any module's
compute schema: a CLI that provisions a SYCL toolchain subclasses ``ToolConfig``
and adds those fields in its own repo. The split keeps the shared seam
domain-agnostic while removing the tool-path duplication the three repos had.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Iterable, Type, TypeVar

from .workspace import load_layered, read_toml


@dataclass
class ToolConfig:
    """Host build-tool paths shared by every Sushi* CLI.

    Empty string means "not pinned — discover it / resolve from PATH". A module
    that needs more (a SYCL toolchain, a sibling checkout) subclasses this and
    adds its own fields; the load/write helpers below operate on any subclass.
    """

    # The C++ compiler driving the build. Empty means "discover it".
    cxx: str = ""
    generator: str = "Ninja"
    use_vcpkg: bool = False

    # Tool roots / paths (mostly Windows-specific absolutes).
    vcpkg_root: str = ""
    vs_vcvars: str = ""
    ninja_exe: str = ""
    # cmake/ctest are resolved from PATH when empty. They are configurable because
    # VS BuildTools does not ship the CMake component, so on Windows cmake commonly
    # lives in a scoop/standalone install that is not on PATH.
    cmake_exe: str = ""
    ctest_exe: str = ""
    # rc (resource compiler) is resolved from CMAKE_RC_COMPILER's own default when
    # empty; configurable because clang-cl/intel-llvm toolchains often don't probe
    # for rc.exe correctly on Windows.
    rc_exe: str = ""
    pkgconf_exe: str = ""
    # doxygen is resolved from PATH when empty; configurable because on Windows it
    # commonly installs outside PATH (winget/choco shims or Program Files).
    doxygen_exe: str = ""
    vcpkg_triplet: str = "x64-windows"

    # Run defaults. Subclasses override the default for their primary binary.
    target_bin: str = ""

    # Derived at load time.
    platform: str = ""

    @property
    def is_windows(self) -> bool:
        return self.platform == "windows"

    def expand(self, value: str) -> str:
        """Expand ~ and env vars in a path-like config value."""
        return os.path.expandvars(os.path.expanduser(value)) if value else value


C = TypeVar("C", bound=ToolConfig)


def load_tool_config(cls: Type[C], sources: Iterable[Path], plat: str,
                     env_map: dict[str, str],
                     bool_keys: Iterable[str] = ("use_vcpkg",)) -> C:
    """Load *cls* from layered TOML sources, keeping only fields it declares.

    @param cls       The ``ToolConfig`` subclass to instantiate.
    @param sources   Config files in ascending precedence (later wins).
    @param plat      Platform key selecting the ``[tool.<platform>]`` override.
    @param env_map   ``field -> ENV_VAR``; a set env var overrides that field.
    @param bool_keys Fields to coerce from string to bool.
    @return          A populated instance with ``platform`` set.
    """
    values = load_layered(sources, plat, env_map, bool_keys=bool_keys)
    known = {f.name for f in fields(cls)}
    cfg = cls(**{k: v for k, v in values.items() if k in known})
    cfg.platform = plat
    return cfg


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


def write_tool_section(target: Path, updates: dict, header_lines: Iterable[str]) -> Path:
    """Merge *updates* into ``[tool]`` of *target* and rewrite the file.

    Every other top-level table already in the file — one this function was not
    asked to write — is carried through unchanged, so a caller sharing the file
    with another writer never loses that writer's data. Used to persist small,
    deliberate edits — e.g. the selected toolchain — while leaving the
    auto-discovered path tables and sibling tables untouched. Returns the path
    written.
    """
    doc = read_toml(target)
    tool = dict(doc.get("tool", {}))
    tool.update(updates)
    tables = dict(doc)
    tables["tool"] = tool
    return write_toml_document(target, tables, header_lines)
