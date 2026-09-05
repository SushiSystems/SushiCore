"""Finding a module's project root, and loading its layered config.

Every Sushi* CLI is installed outside the repository it builds -- pip or pipx
puts it in a venv -- so the package's own location says nothing about where the
project lives. The invocation directory does. Each CLI therefore walks up from
the cwd looking for one of its markers -- the checkout's marker file, or the
release manifest an unpacked binary install carries -- then layers config.toml,
the workspace-shared config.local.toml that ``ss install`` writes, and the repo's
own config.local.toml, in that order.

That is the same procedure five times over, differing only in the marker, the
project's name in the error message, and the prefix on the environment
overrides -- all three of which a :class:`~sushicore.profile.ModuleProfile`
already states.
"""

from __future__ import annotations

import platform
from pathlib import Path
from typing import TypeVar

from .config_base import ToolConfig, load_tool_config
from .profile import ModuleProfile
from .workspace import has_marker, resolve_env_path, walk_up

# The marker `ss init` writes at the root of a workspace.
_WORKSPACE_MARKER = ".sushistack"

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
               config.local.toml that ``ss install`` writes. A module with no
               toolchain of its own to pin has nothing to read from it, and
               says so by passing False rather than reading it and finding
               nothing.
        """
        self._profile = profile
        self._use_workspace_config = use_workspace_config

    @property
    def profile(self) -> ModuleProfile:
        return self._profile

    def find_project_root(self, start: Path | None = None) -> Path:
        """Walk up from *start* (default cwd) to any of the profile's markers.

        The nearest directory carrying either marker wins, so the same walk
        finds a checkout and an unpacked release.

        @raise SystemExit when run outside a checkout. Callers that can work
               without a project -- the console, ``--help`` -- catch it; that is
               deliberate, and why it is SystemExit rather than a return of None.
        """
        root = walk_up(start or Path.cwd(), has_marker(*self._profile.markers()))
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

    def workspace_home(self, root: Path | None = None) -> Path | None:
        """The SushiStack workspace root, or None when the module is standalone.

        ``SUSHISTACK_HOME`` wins; otherwise walk up from the project root for the
        ``.sushistack`` marker.
        """
        home = resolve_env_path("SUSHISTACK_HOME")
        if home:
            return home
        try:
            start = root or self.find_project_root()
        except SystemExit:
            return None
        return walk_up(start, has_marker(_WORKSPACE_MARKER))

    def _shared_config_local(self) -> Path | None:
        """The workspace-shared config.local.toml ``ss install`` writes, if any.

        Inside a workspace the machine-specific tool paths (compiler, vcpkg,
        cmake) are resolved once by ``ss`` and written to
        ``<home>/cli/config.local.toml``, so nothing is configured twice.
        """
        home = self.workspace_home()
        return (home / "cli" / "config.local.toml") if home else None

    def sources(self) -> list[Path]:
        """The config files to layer, lowest precedence first."""
        cfg_dir = self.config_dir()
        shared = self._shared_config_local() if self._use_workspace_config else None
        sources = [cfg_dir / "config.toml"]
        if shared is not None:
            sources.append(shared)
        sources.append(cfg_dir / "config.local.toml")
        return sources

    def load(self, config_cls: type[_C]) -> _C:
        """Load and resolve *config_cls* for the current platform.

        Precedence, low to high: repo config.toml -> workspace-shared
        config.local.toml -> repo config.local.toml -> environment.
        """
        plat = platform.system().lower()  # 'windows' | 'linux' | 'darwin'
        return load_tool_config(
            config_cls, self.sources(), plat, self._profile.env_overrides()
        )
