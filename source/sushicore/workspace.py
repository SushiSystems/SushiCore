# workspace.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Names a workspace's marker and data file and keeps the ``[modules]`` table it holds.

The walk-up and TOML readers it re-exports for the module CLIs that import them here live in
``layered_toml``. What the workspace holds is in docs/architecture/OVERVIEW.md, section `workspace`.
"""

from __future__ import annotations

from pathlib import Path

from .layered_toml import has_marker, read_toml, resolve_env_path, walk_up  # noqa: F401
from .provision.moved_name import moved_attribute
from .toml_writer import write_toml_document

#: The directory `hub init` writes at a workspace root. Every Sushi CLI walks up for it.
WORKSPACE_MARKER = ".sushistack"

#: The one file inside the marker that holds what the workspace owns.
WORKSPACE_FILE = "workspace.toml"

#: The shared tool paths of a workspace hub has not upgraded; see docs/architecture/OVERVIEW.md.
LEGACY_SHARED_CONFIG = Path("sushihub") / "cli" / "config.local.toml"


def workspace_file(root: Path) -> Path:
    """The file a workspace keeps its own data in: ``<root>/.sushistack/workspace.toml``."""
    return root / WORKSPACE_MARKER / WORKSPACE_FILE


#: The value written into ``[workspace] version``, as a string so it can become "1.1".
WORKSPACE_VERSION = "1"

#: The comment block every writer puts at the top of ``workspace.toml``.
WORKSPACE_HEADER = [
    "# The SushiStack workspace's own data. `hub` locates this directory by walking up from the",
    "# working directory, and everything it records about this machine lives in this one file.",
    "#",
    "# [workspace] version  the format's version, so a later `hub` can migrate this file.",
    "# [modules]            name = path, written by `hub link`.",
    "# [tool]               tool paths and the selected toolchain, written by `hub install`.",
]


def registered_modules(root: Path) -> dict[str, str]:
    """Return the ``[modules]`` table of *root*'s workspace.toml as name -> path.

    @param root The workspace root, passed in explicitly; this never walks up.
    """
    mods = read_toml(workspace_file(root)).get("modules", {})
    return {k: str(v) for k, v in mods.items() if isinstance(v, str)}


def write_module(root: Path, name: str, path: Path) -> Path:
    """Record (or update) a ``name -> path`` entry in *root*'s ``[modules]``.

    @param root The workspace root, passed in explicitly; this never walks up.
    @return     The path written.
    """
    target = workspace_file(root)
    document = dict(read_toml(target))
    registry = dict(document.get("modules", {}))
    registry[name] = str(path)
    document["modules"] = registry
    document.setdefault("workspace", {"version": WORKSPACE_VERSION})
    target.parent.mkdir(parents=True, exist_ok=True)
    return write_toml_document(target, document, WORKSPACE_HEADER)


def remove_module(root: Path, name: str) -> bool:
    """Remove *name* from *root*'s ``[modules]`` table, and report whether it was present.

    @param root The workspace root, passed in explicitly; this never walks up.
    """
    target = workspace_file(root)
    document = dict(read_toml(target))
    registry = dict(document.get("modules", {}))
    if name not in registry:
        return False
    del registry[name]
    document["modules"] = registry
    document.setdefault("workspace", {"version": WORKSPACE_VERSION})
    target.parent.mkdir(parents=True, exist_ok=True)
    write_toml_document(target, document, WORKSPACE_HEADER)
    return True

#: Each name that left this module and the module that holds it now.
K_MOVED = {
    "LINK_SECTION": "sushicore.link_pointer",
    "LinkEditError": "sushicore.link_pointer",
    "clear_link": "sushicore.link_pointer",
    "read_link": "sushicore.link_pointer",
    "write_link": "sushicore.link_pointer",
    "load_layered": "sushicore.layered_toml",
    "merge_platform_table": "sushicore.layered_toml",
}


def __getattr__(name: str) -> object:
    """Return a name that moved to another module, with a deprecation warning."""
    return moved_attribute(globals(), K_MOVED, name)
