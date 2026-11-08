# home.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Resolves the machine's dependency root and the legacy trees read alongside it."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Callable, Mapping, Sequence

from ..workspace import WORKSPACE_MARKER, has_marker, walk_up

ENV_HOME = "SUSHISYSTEMS_HOME"
DIR_NAME = ".sushisystems"
_LEGACY_ENV = "SUSHISTACK_DEPS_DIR"

_bound: Callable[[], Path] | None = None

_VARIABLE = re.compile(r"\$(\w+)|\$\{(\w+)\}|%(\w+)%")


def default_root(user_home: Path | None = None) -> Path:
    """Return ``~/.sushisystems`` of *user_home*, the current user's home when ``None``."""
    return (Path.home() if user_home is None else user_home) / DIR_NAME


def bind_root(provider: Callable[[], Path] | None) -> None:
    """Make *provider* the source of the root, overriding the env var; ``None`` unbinds."""
    global _bound
    _bound = provider


def _expand(value: str, environ: Mapping[str, str], user_home: Path | None) -> str:
    """Return *value* with a leading ``~`` and the variables of *environ* expanded."""
    home_text = str(Path.home() if user_home is None else user_home)
    if value == "~" or value.startswith(("~/", "~\\")):
        value = home_text + value[1:]
    return _VARIABLE.sub(
        lambda match: environ.get(match.group(1) or match.group(2) or match.group(3),
                                  match.group(0)), value)


def _env_path(environ: Mapping[str, str], name: str, user_home: Path | None,
              cwd: Path | None) -> Path | None:
    """Return the variable *name* as an expanded, absolute path, or None when it is unset."""
    value = environ.get(name)
    if not value:
        return None
    base = Path.cwd() if cwd is None else cwd
    return (base / _expand(value, environ, user_home)).resolve()


def root(*, environ: Mapping[str, str] | None = None, user_home: Path | None = None,
         cwd: Path | None = None, bound: Callable[[], Path] | None = None) -> Path:
    """Return the absolute dependency root: bound provider, then env var, then default.

    Args:
        environ: The environment to read; the process's when ``None``.
        user_home: The home directory ``~`` and the default root start from; the user's when ``None``.
        cwd: The folder a relative env value is taken from; the working folder when ``None``.
        bound: A provider that wins over the module's bound one; the bound one when ``None``.
    """
    provider = bound or _bound
    if provider is not None:
        return Path(provider()).expanduser().resolve()
    env = os.environ if environ is None else environ
    from_env = _env_path(env, ENV_HOME, user_home, cwd)
    return from_env if from_env is not None else default_root(user_home)


def _walk_up_workspace(start: Path) -> Path | None:
    """Return the nearest ancestor of *start*, itself included, that carries the workspace marker."""
    return walk_up(start, has_marker(WORKSPACE_MARKER))


def legacy_roots(*, environ: Mapping[str, str] | None = None, cwd: Path | None = None,
                 current: Path | None = None, is_dir: Callable[[Path], bool] | None = None,
                 workspace_of: Callable[[Path], Path | None] | None = None) -> list[Path]:
    """Return existing hub trees read as installed, excluding the current root.

    Args:
        environ: The environment to read; the process's when ``None``.
        cwd: Where the workspace search starts; the working folder when ``None``.
        current: The root to leave out; :func:`root` when ``None``.
        is_dir: Asked whether a candidate is a folder; ``Path.is_dir`` when ``None``.
        workspace_of: Finds the workspace above a folder; a walk up to the workspace marker when
            ``None``.
    """
    env = os.environ if environ is None else environ
    start = Path.cwd() if cwd is None else cwd
    found: list[Path] = []
    override = _env_path(env, _LEGACY_ENV, None, start)
    if override is not None:
        found.append(override)
    workspace = _env_path(env, "SUSHISTACK_HOME", None, start) or (
        workspace_of or _walk_up_workspace)(start)
    if workspace is not None:
        found.append((workspace / "dependencies").resolve())
    excluded = root(environ=env, cwd=start) if current is None else current
    exists = is_dir or Path.is_dir
    result: list[Path] = []
    for path in found:
        if exists(path) and path != excluded and path not in result:
            result.append(path)
    return result


def search_roots(*, current: Path | None = None,
                 legacy: Sequence[Path] | None = None) -> list[Path]:
    """Return the root followed by every legacy root, in lookup order.

    Args:
        current: The root; :func:`root` when ``None``.
        legacy: The legacy roots; :func:`legacy_roots` when ``None``.
    """
    return [root() if current is None else current,
            *(legacy_roots() if legacy is None else legacy)]


def is_removable_root(path: Path, *, user_home: Path | None = None, cwd: Path | None = None,
                      exists: Callable[[Path], bool] | None = None) -> bool:
    """Report whether *path* is safe to recursively delete as a dependency root.

    Refuses the user's home directory, a filesystem anchor, the current
    working directory, any ancestor of it, and any directory holding a
    ``.git`` or :data:`WORKSPACE_MARKER` entry.

    Args:
        user_home: The home directory to refuse; the user's when ``None``.
        cwd: The working folder to refuse, and its ancestors; the process's when ``None``.
        exists: Asked whether a marker exists; ``Path.exists`` when ``None``.
    """
    resolved = Path(path).resolve()
    home_dir = (Path.home() if user_home is None else user_home).resolve()
    if resolved in (home_dir, Path(resolved.anchor)):
        return False
    working = (Path.cwd() if cwd is None else cwd).resolve()
    if resolved == working or resolved in working.parents:
        return False
    present = exists or Path.exists
    return not (present(resolved / ".git") or present(resolved / WORKSPACE_MARKER))


def toolchains_dir(base: Path | None = None) -> Path:
    """Return ``<root>/toolchains``, the root being *base* when given."""
    return (root() if base is None else base) / "toolchains"


def tools_dir(base: Path | None = None) -> Path:
    """Return ``<root>/tools``, the root being *base* when given."""
    return (root() if base is None else base) / "tools"


def vcpkg_dir(base: Path | None = None) -> Path:
    """Return ``<root>/vcpkg``, the root being *base* when given."""
    return (root() if base is None else base) / "vcpkg"


def found_vcpkg_dir(roots: Sequence[Path] | None = None,
                    is_dir: Callable[[Path], bool] | None = None) -> Path:
    """Return the first vcpkg tree across the search roots, else ``<root>/vcpkg``.

    Args:
        roots: The roots to look through, the first being the current one; :func:`search_roots`
            when ``None``.
        is_dir: Asked whether a candidate is a folder; ``Path.is_dir`` when ``None``.
    """
    candidates = search_roots() if roots is None else list(roots)
    exists = is_dir or Path.is_dir
    for candidate in candidates:
        if exists(candidate / "vcpkg"):
            return candidate / "vcpkg"
    return vcpkg_dir(candidates[0] if candidates else None)


def ur_dir(base: Path | None = None) -> Path:
    """Return ``<root>/ur``, the root being *base* when given."""
    return (root() if base is None else base) / "ur"


def sources_dir(base: Path | None = None) -> Path:
    """Return ``<root>/sources``, where ``setup`` clones pinned Sushi libraries."""
    return (root() if base is None else base) / "sources"


def build_dir(base: Path | None = None) -> Path:
    """Return ``<root>/build``, the root being *base* when given."""
    return (root() if base is None else base) / "build"
