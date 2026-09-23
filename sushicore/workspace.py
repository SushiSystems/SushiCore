"""Shared, domain-agnostic config plumbing for the Sushi* developer CLIs.

Every module CLI (`sr`, `se`, `hub`) resolves its config the same way — walk up
for a marker file, merge a ``[tool]`` table with its ``[tool.<platform>]``
override, then let ``PREFIX_*`` environment variables win. That plumbing used to
be copy-pasted into each repo's ``config.py``; it lives here so there is one seam.

This module knows nothing about SYCL, toolchains, or any module's schema. It only
locates directories and merges TOML the caller hands it — each CLI keeps its own
``Config`` dataclass and passes its markers, section name, and env-var map in.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Iterable

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # Python 3.10 fallback
    import tomli as tomllib


#: The directory `hub init` writes at a workspace root. Every Sushi CLI walks up for it.
WORKSPACE_MARKER = ".sushistack"

#: The one file inside the marker that holds what the workspace owns.
WORKSPACE_FILE = "workspace.toml"

#: Where `hub install` wrote the shared tool paths before 2026-09-22, relative to the root.
#: Read as a fallback so a workspace that no `hub` command has upgraded yet still resolves.
LEGACY_SHARED_CONFIG = Path("sushihub") / "cli" / "config.local.toml"


def workspace_file(root: Path) -> Path:
    """The file a workspace keeps its own data in: ``<root>/.sushistack/workspace.toml``."""
    return root / WORKSPACE_MARKER / WORKSPACE_FILE


def read_toml(path: Path) -> dict:
    """Parse a TOML file, or return ``{}`` when it does not exist."""
    if not path.is_file():
        return {}
    with path.open("rb") as fh:
        return tomllib.load(fh)


def walk_up(start: Path, predicate: Callable[[Path], bool]) -> Path | None:
    """Return the nearest ancestor of *start* (inclusive) satisfying *predicate*.

    The CLIs are installed outside their checkout, so the invocation directory —
    not the package location — tells us where the project/workspace lives.
    """
    cur = start.resolve()
    for d in (cur, *cur.parents):
        if predicate(d):
            return d
    return None


def has_marker(*names: str) -> Callable[[Path], bool]:
    """Predicate: a directory contains any of the named marker files or dirs."""
    def _pred(d: Path) -> bool:
        return any((d / name).exists() for name in names)
    return _pred


def resolve_env_path(name: str) -> Path | None:
    """Return an env var as an expanded, resolved path, or None when unset."""
    val = os.environ.get(name)
    if not val:
        return None
    return Path(os.path.expandvars(os.path.expanduser(val))).resolve()


def merge_platform_table(doc: dict, plat: str, section: str = "tool") -> dict:
    """Merge a document's ``[section]`` with ``[section.<platform>]``.

    Scalar keys from the common section are taken first; the platform-specific
    sub-table wins on any key it repeats. Nested tables other than the platform
    one are dropped (callers that need override tables handle them explicitly).
    """
    table = dict(doc.get(section, {}))
    merged = {k: v for k, v in table.items() if not isinstance(v, dict)}
    plat_table = table.get(plat, {})
    if isinstance(plat_table, dict):
        merged.update({k: v for k, v in plat_table.items() if not isinstance(v, dict)})
    return merged


def load_layered(paths: Iterable[Path], plat: str, env_map: dict[str, str],
                 section: str = "tool", bool_keys: Iterable[str] = ()) -> dict:
    """Merge ``[section]`` from each path (low → high) then apply env overrides.

    @param paths     Config files in ascending precedence (later wins).
    @param plat      Platform key selecting the ``[section.<platform>]`` override.
    @param env_map   ``field -> ENV_VAR``; a set env var overrides that field.
    @param section   Top-level table name to read (default ``tool``).
    @param bool_keys Fields to coerce from string ("1"/"true"/…) to bool.
    @return          The merged ``field -> value`` mapping (unknown keys included;
                     the caller filters to its dataclass fields).
    """
    values: dict = {}
    for path in paths:
        doc = read_toml(path)
        if doc:
            values.update(merge_platform_table(doc, plat, section))
    for field_name, env_var in env_map.items():
        if env_var in os.environ:
            values[field_name] = os.environ[env_var]
    for key in bool_keys:
        if isinstance(values.get(key), str):
            values[key] = values[key].strip().lower() in ("1", "true", "yes", "on")
    return values


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
    from .config_base import write_toml_document

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
    from .config_base import write_toml_document

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
