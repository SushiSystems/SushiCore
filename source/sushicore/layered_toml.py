# layered_toml.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Reads TOML files, walks up to a marker and merges the layered ``[tool]`` tables the Sushi CLIs share."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Iterable

from .environment import Environment, ProcessEnvironment
from .errors import ConfigError
from .files import Files

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # Python 3.10 fallback
    import tomli as tomllib


def read_toml(path: Path, *, files: Files | None = None) -> dict:
    """Parse a TOML file, or return ``{}`` when it does not exist.

    @param files The file system the file is read through; the disk when None.
    @throws ConfigError When the file is not valid TOML.
    """
    if files is not None:
        return _parse_toml(path, files.read_text(path)) if files.is_file(path) else {}
    if not path.is_file():
        return {}
    try:
        with path.open("rb") as fh:
            return tomllib.load(fh)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{path}: {exc}") from exc


def _parse_toml(path: Path, text: str) -> dict:
    """Parse TOML *text* read from *path*.

    @throws ConfigError When the text is not valid TOML.
    """
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{path}: {exc}") from exc


def walk_up(start: Path, predicate: Callable[[Path], bool], *, resolve: bool = True) -> Path | None:
    """Return the nearest ancestor of *start* (inclusive) satisfying *predicate*.

    The CLIs are installed outside their checkout, so the invocation directory —
    not the package location — tells us where the project/workspace lives.

    @param resolve Whether *start* is resolved on the disk first; False keeps the path as given,
           for a path that names a place in memory.
    """
    cur = start.resolve() if resolve else start
    for d in (cur, *cur.parents):
        if predicate(d):
            return d
    return None


def has_marker(*names: str, files: Files | None = None) -> Callable[[Path], bool]:
    """Predicate: a directory contains any of the named marker files or dirs.

    @param files The file system the markers are looked up in; the disk when None.
    """
    def _pred(d: Path) -> bool:
        if files is not None:
            return any(files.exists(d / name) for name in names)
        return any((d / name).exists() for name in names)
    return _pred


def resolve_env_path(name: str, *, environment: Environment | None = None,
                     resolve: bool = True) -> Path | None:
    """Return an env var as an expanded, resolved path, or None when unset.

    @param environment The variables read; the process environment when None.
    @param resolve     Whether the path is resolved on the disk; False keeps it as expanded.
    """
    val = (ProcessEnvironment() if environment is None else environment).get(name)
    if not val:
        return None
    path = Path(os.path.expandvars(os.path.expanduser(val)))
    return path.resolve() if resolve else path


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
                 section: str = "tool", bool_keys: Iterable[str] = (), *,
                 environment: Environment | None = None, files: Files | None = None) -> dict:
    """Merge ``[section]`` from each path (low → high) then apply env overrides.

    @param paths     Config files in ascending precedence (later wins).
    @param plat      Platform key selecting the ``[section.<platform>]`` override.
    @param env_map   ``field -> ENV_VAR``; a set env var overrides that field.
    @param section   Top-level table name to read (default ``tool``).
    @param bool_keys Fields to coerce from string ("1"/"true"/…) to bool.
    @param environment The variables read for the overrides; the process environment when None.
    @param files     The file system the files are read through; the disk when None.
    @return          The merged ``field -> value`` mapping (unknown keys included;
                     the caller filters to its dataclass fields).
    """
    env = ProcessEnvironment() if environment is None else environment
    values: dict = {}
    for path in paths:
        doc = read_toml(path, files=files)
        if doc:
            values.update(merge_platform_table(doc, plat, section))
    for field_name, env_var in env_map.items():
        if env.has(env_var):
            values[field_name] = env.get(env_var, "")
    for key in bool_keys:
        if isinstance(values.get(key), str):
            values[key] = values[key].strip().lower() in ("1", "true", "yes", "on")
    return values
