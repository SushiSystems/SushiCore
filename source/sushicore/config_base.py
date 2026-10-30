# config_base.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Declares the build-tool config the Sushi CLIs share, and loads and writes it.

The reasoning is in docs/architecture/OVERVIEW.md, section `config_base`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Iterable, Type, TypeVar

from .toml_writer import write_toml_document
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
    #: Whether the build uses vcpkg. None means the config never said, which keeps today's lookup.
    use_vcpkg: bool | None = None

    # Tool roots / paths (mostly Windows-specific absolutes).
    vcpkg_root: str = ""
    vs_vcvars: str = ""
    ninja_exe: str = ""
    # Resolved from PATH when empty; see docs/architecture/OVERVIEW.md, config_base.
    cmake_exe: str = ""
    ctest_exe: str = ""
    # Resolved from CMAKE_RC_COMPILER's default when empty; see docs/architecture/OVERVIEW.md.
    rc_exe: str = ""
    pkgconf_exe: str = ""
    # Resolved from PATH when empty; see docs/architecture/OVERVIEW.md, config_base.
    doxygen_exe: str = ""
    # The compiler cache host compiles run through; see docs/architecture/OVERVIEW.md, build_admission.
    ccache_exe: str = ""
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
