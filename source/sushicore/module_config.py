# module_config.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Finds a module's project root and loads its layered config.

The reasoning is in docs/architecture/OVERVIEW.md, section `module_config`.
"""

from __future__ import annotations

import platform
from pathlib import Path
from typing import TypeVar

from .config_base import ToolConfig, load_tool_config
from .environment import Environment
from .files import Files
from .profile import ModuleProfile
from .workspace import (
    LEGACY_SHARED_CONFIG,
    WORKSPACE_MARKER,
    has_marker,
    read_link,
    resolve_env_path,
    walk_up,
    workspace_file,
)

_C = TypeVar("_C", bound=ToolConfig)


class ModuleConfig:
    """Locates one module's checkout and loads its configuration.

    Holds no state beyond the profile: it is a small facade over the shared
    workspace helpers, so a CLI states its identity once and gets root
    resolution, config-directory resolution and layered loading from it.
    """

    __slots__ = ("_profile", "_use_workspace_config")

    def __init__(self, profile: ModuleProfile, *, use_workspace_config: bool = True) -> None:
        """
        @param use_workspace_config Whether to layer the workspace-shared
               config.local.toml that ``hub install`` writes. A module with no
               toolchain of its own to pin has nothing to read from it, and
               says so by passing False rather than reading it and finding
               nothing.
        """
        self._profile = profile
        self._use_workspace_config = use_workspace_config

    @property
    def profile(self) -> ModuleProfile:
        return self._profile

    def find_project_root(self, start: Path | None = None, *, files: Files | None = None) -> Path:
        """Walk up from *start* (default cwd) to any of the profile's markers.

        The nearest directory carrying either marker wins, so the same walk
        finds a checkout and an unpacked release.

        @param files The file system the markers are looked up in; the disk when None. A start
               path in memory is walked as given, not resolved.

        @raise SystemExit when run outside a checkout. Callers that can work
               without a project -- the console, ``--help`` -- catch it; that is
               deliberate, and why it is SystemExit rather than a return of None.
        """
        root = walk_up(start or Path.cwd(), has_marker(*self._profile.markers(), files=files),
                       resolve=files is None)
        if root is None:
            raise SystemExit(self._profile.not_a_project_message())
        return root

    def presence(self, root: Path | None = None) -> str:
        """Report how this module is present: "binary" or "source".

        @param root The module root, or None to walk up from the cwd for it.
        """
        return self._profile.presence(root or self.find_project_root())

    def config_dir(self, root: Path | None = None) -> Path:
        """Directory holding config.toml / config.local.toml (the repo's cli/)."""
        return (root or self.find_project_root()) / "cli"

    def workspace_home(self, root: Path | None = None, *, environment: Environment | None = None,
                       files: Files | None = None) -> Path | None:
        """The SushiStack workspace root, or None when the module is standalone.

        ``SUSHISTACK_HOME`` wins; then the module's ``[link]`` pointer; otherwise
        walk up from the project root for the ``.sushistack`` marker.

        @param environment The variables read; the process environment when None.
        @param files       The file system read through; the disk when None.
        """
        home = resolve_env_path("SUSHISTACK_HOME", environment=environment, resolve=files is None)
        if home:
            return home
        try:
            start = root or self.find_project_root(files=files)
        except SystemExit:
            return None
        linked = read_link(self.config_dir(start), files=files)
        if linked is not None:
            return linked
        return walk_up(start, has_marker(WORKSPACE_MARKER, files=files), resolve=files is None)

    def _shared_config_local(self, root: Path | None, environment: Environment | None,
                             files: Files | None) -> Path | None:
        """The workspace-shared config ``hub install`` writes, if any.

        Inside a workspace the machine-specific tool paths (compiler, vcpkg,
        cmake) are resolved once by ``hub`` and written to the workspace's own
        file, so nothing is configured twice. Since 2026-09-22 that is
        ``<home>/.sushistack/workspace.toml``; before it, ``sushihub/cli/
        config.local.toml`` in the checkout. The older path is read when the
        newer one is absent, so a workspace no ``hub`` command has upgraded yet
        still hands its paths to `sr`, `se`, `sa` and `sb`.
        """
        home = self.workspace_home(root, environment=environment, files=files)
        if home is None:
            return None
        is_file = Path.is_file if files is None else (lambda path: files.is_file(path))
        current = workspace_file(home)
        if is_file(current):
            return current
        legacy = home / LEGACY_SHARED_CONFIG
        return legacy if is_file(legacy) else None

    def sources(self, root: Path | None = None, *, environment: Environment | None = None,
                files: Files | None = None) -> list[Path]:
        """The config files to layer, lowest precedence first.

        @param root        The module root, or None to walk up from the cwd for it.
        @param environment The variables read; the process environment when None.
        @param files       The file system read through; the disk when None.
        """
        root = root or self.find_project_root(files=files)
        cfg_dir = self.config_dir(root)
        shared = (self._shared_config_local(root, environment, files)
                  if self._use_workspace_config else None)
        sources = [cfg_dir / "config.toml"]
        if shared is not None:
            sources.append(shared)
        sources.append(cfg_dir / "config.local.toml")
        return sources

    def load(self, config_cls: type[_C], *, root: Path | None = None,
             environment: Environment | None = None, files: Files | None = None) -> _C:
        """Load and resolve *config_cls* for the current platform.

        Precedence, low to high: repo config.toml -> workspace-shared
        config.local.toml -> repo config.local.toml -> environment.

        @param root        The module root, or None to walk up from the cwd for it.
        @param environment The variables read; the process environment when None.
        @param files       The file system read through; the disk when None.
        """
        plat = platform.system().lower()  # 'windows' | 'linux' | 'darwin'
        return load_tool_config(
            config_cls, self.sources(root, environment=environment, files=files), plat,
            self._profile.env_overrides(), environment=environment, files=files
        )
