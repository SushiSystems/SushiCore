"""Toolchain resolution for a module that consumes the shared dependency tree.

SushiEngine, SushiAI and SushiBLAS are heads of the stack: they select no SYCL
toolchain of their own, they consume the one ``ss install`` provisions into
``<workspace>/dependencies``. Resolving the compiler and vcpkg from that tree
is identical work in all three, and each carried its own copy of it.

SushiRuntime is deliberately not a subclass. It owns the bundle rather than
consuming it, selects between toolchains (acpp / clang++ / icpx), and resolves
deps with a different signature. Forcing it into this shape would mean bending
the base class around a case it does not describe.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .config_base import ToolConfig


@dataclass
class StackConfig(ToolConfig):
    """A module config that resolves its toolchain from the shared tree.

    Subclasses declare their sibling checkouts as fields and implement
    :meth:`standalone_deps_dir`. Everything below is the same for all of them.
    """

    def sibling_dir(self, root: Path, name: str, configured: str = "") -> Path:
        """Resolve a sibling module checkout.

        @param root       This module's project root.
        @param name       The sibling's directory name, e.g. ``"sushiruntime"``.
        @param configured An explicit override from config or environment.
        @return ``configured`` if set, else ``<root>/../<name>`` -- the same
                default the module's cmake uses, and the workspace layout.
        """
        if configured:
            return Path(self.expand(configured)).resolve()
        return (root / ".." / name).resolve()

    def standalone_deps_dir(self, root: Path) -> Path:
        """The dependency tree to use when not inside a workspace.

        Subclass responsibility: a head of the stack falls back to the bundle
        shipped with the SushiRuntime checkout it builds against.
        """
        raise NotImplementedError

    def workspace_home(self, root: Path) -> Path | None:
        """The SushiStack workspace root, or None when standalone.

        Kept as a method on the config (rather than only on ModuleConfig) because
        every caller here already holds a config and a root.
        """
        from .workspace import has_marker, resolve_env_path, walk_up

        home = resolve_env_path("SUSHISTACK_HOME")
        if home:
            return home
        return walk_up(root, has_marker(".sushistack"))

    # Historical name kept so existing call sites and diagnostics keep working.
    sushistack_home = workspace_home

    def deps_dir(self, root: Path) -> Path:
        """The dependency tree this build resolves its toolchain from.

        Inside a workspace that is ``<workspace>/dependencies``, shared by every
        module. ``SUSHISTACK_DEPS_DIR`` overrides both that and the standalone
        fallback.
        """
        override = os.environ.get("SUSHISTACK_DEPS_DIR")
        if override:
            return Path(self.expand(override))
        home = self.workspace_home(root)
        if home:
            return home / "dependencies"
        return self.standalone_deps_dir(root)

    def bundled_clang(self, root: Path) -> str:
        """The bundled clang++ under the shared toolchain, or '' if absent."""
        exe = "clang++.exe" if self.is_windows else "clang++"
        candidate = self.deps_dir(root) / "toolchains" / "llvm-sycl" / "bin" / exe
        return str(candidate) if candidate.is_file() else ""

    def resolved_compiler(self, root: Path) -> str:
        """The compiler to drive the build: explicit, then bundled, then PATH."""
        if self.cxx:
            return self.expand(self.cxx)
        return self.bundled_clang(root) or "clang++"

    def resolved_vcpkg(self, root: Path) -> str:
        """The vcpkg root: explicit, then the shared bundled tree, else ''."""
        if self.vcpkg_root:
            return self.expand(self.vcpkg_root)
        bundled = self.deps_dir(root) / "vcpkg"
        return str(bundled) if bundled.is_dir() else ""
