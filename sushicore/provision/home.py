# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Resolves the machine's dependency root and the legacy trees read alongside it."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from ..workspace import WORKSPACE_MARKER, has_marker, resolve_env_path, walk_up

ENV_HOME = "SUSHISYSTEMS_HOME"
DIR_NAME = ".sushisystems"
_LEGACY_ENV = "SUSHISTACK_DEPS_DIR"

_bound: Callable[[], Path] | None = None


def default_root() -> Path:
    """Return ``~/.sushisystems``."""
    return Path.home() / DIR_NAME


def bind_root(provider: Callable[[], Path] | None) -> None:
    """Make *provider* the source of the root, overriding the env var; ``None`` unbinds."""
    global _bound
    _bound = provider


def root() -> Path:
    """Return the absolute dependency root: bound provider, then env var, then default."""
    if _bound is not None:
        return Path(_bound()).expanduser().resolve()
    value = os.environ.get(ENV_HOME)
    if value:
        return Path(os.path.expandvars(os.path.expanduser(value))).resolve()
    return default_root()


def legacy_roots() -> list[Path]:
    """Return existing hub trees read as installed, excluding the current root."""
    found: list[Path] = []
    override = resolve_env_path(_LEGACY_ENV)
    if override is not None:
        found.append(override)
    workspace = resolve_env_path("SUSHISTACK_HOME") or walk_up(
        Path.cwd(), has_marker(WORKSPACE_MARKER))
    if workspace is not None:
        found.append((workspace / "dependencies").resolve())
    current = root()
    result: list[Path] = []
    for path in found:
        if path.is_dir() and path != current and path not in result:
            result.append(path)
    return result


def search_roots() -> list[Path]:
    """Return the root followed by every legacy root, in lookup order."""
    return [root(), *legacy_roots()]


def is_removable_root(path: Path) -> bool:
    """Report whether *path* is safe to recursively delete as a dependency root.

    Refuses the user's home directory, a filesystem anchor, the current
    working directory, any ancestor of it, and any directory holding a
    ``.git`` or :data:`WORKSPACE_MARKER` entry.
    """
    resolved = Path(path).resolve()
    if resolved in (Path.home().resolve(), Path(resolved.anchor)):
        return False
    cwd = Path.cwd().resolve()
    if resolved == cwd or resolved in cwd.parents:
        return False
    if (resolved / ".git").exists() or (resolved / WORKSPACE_MARKER).exists():
        return False
    return True


def toolchains_dir() -> Path:
    """Return ``<root>/toolchains``."""
    return root() / "toolchains"


def tools_dir() -> Path:
    """Return ``<root>/tools``."""
    return root() / "tools"


def vcpkg_dir() -> Path:
    """Return ``<root>/vcpkg``."""
    return root() / "vcpkg"


def ur_dir() -> Path:
    """Return ``<root>/ur``."""
    return root() / "ur"


def build_dir() -> Path:
    """Return ``<root>/build``."""
    return root() / "build"
