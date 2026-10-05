# stack_config.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026 Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Resolves the toolchain of a module that consumes the shared dependency tree.

The reasoning is in docs/architecture/OVERVIEW.md, section `stack_config`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .provision import home as provision_home
from .provision.config import ProvisionSettings


@dataclass
class StackConfig(ProvisionSettings):
    """A module config that resolves its toolchain from the shared tree.

    Subclasses declare their sibling checkouts as fields. Everything below is
    the same for all of them.
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

    def locate_sibling(self, root: Path, name: str) -> Path | None:
        """Return the checkout of the sibling module *name*, or None when there is none.

        @param root This module's project root.
        @param name The sibling's directory name, e.g. ``"sushiruntime"``.
        """
        found = self.sibling_dir(root, name, getattr(self, f"{name}_dir", ""))
        return found if found.is_dir() else None

    def standalone_deps_dir(self, root: Path) -> Path:
        """Return the machine's dependency root.

        Deprecated: nothing reads this any more; :meth:`dependency_roots` is the
        search order. It stays one release for subclasses that still call it.
        """
        del root
        return provision_home.root()

    def workspace_home(self, root: Path) -> Path | None:
        """The SushiStack workspace root, or None when standalone.

        ``SUSHISTACK_HOME`` wins; then the module's ``[link]`` pointer; otherwise
        a walk up from *root* for the ``.sushistack`` marker.
        """
        from .workspace import has_marker, read_link, resolve_env_path, walk_up

        home = resolve_env_path("SUSHISTACK_HOME")
        if home:
            return home
        linked = read_link(root / "cli")
        if linked is not None:
            return linked
        return walk_up(root, has_marker(".sushistack"))

    # Historical name kept so existing call sites and diagnostics keep working.
    sushistack_home = workspace_home

    def dependency_roots(self, root: Path) -> list[Path]:
        """Return every dependency tree this build may resolve from, first match wins.

        ``SUSHISTACK_DEPS_DIR`` is the only root when set. Otherwise the
        workspace's own tree comes first when the module sits in or is linked to
        one, then the machine root and the legacy trees beside it.
        """
        override = os.environ.get("SUSHISTACK_DEPS_DIR")
        if override:
            return [Path(self.expand(override))]
        roots: list[Path] = []
        workspace = self.workspace_home(root)
        if workspace:
            roots.append((workspace / "dependencies").resolve())
        for candidate in provision_home.search_roots():
            if candidate not in roots:
                roots.append(candidate)
        return roots

    def deps_dir(self, root: Path) -> Path:
        """Return the first of :meth:`dependency_roots`."""
        return self.dependency_roots(root)[0]

    def bundled_llvm_root(self, root: Path) -> Path | None:
        """Return the intel/llvm bundle holding a clang++, or None when there is none.

        An explicit ``llvm_root`` wins when its clang++ exists; otherwise the
        first ``toolchains/llvm-sycl`` across :meth:`dependency_roots`.
        """
        exe = "clang++.exe" if self.is_windows else "clang++"
        candidates = [Path(self.expand(self.llvm_root))] if self.llvm_root else []
        candidates += [tree / "toolchains" / "llvm-sycl" for tree in self.dependency_roots(root)]
        for bundle in candidates:
            if (bundle / "bin" / exe).is_file():
                return bundle
        return None

    def bundled_clang(self, root: Path) -> str:
        """The bundled clang++ under the shared toolchain, or '' if absent."""
        bundle = self.bundled_llvm_root(root)
        if bundle is None:
            return ""
        return str(bundle / "bin" / ("clang++.exe" if self.is_windows else "clang++"))

    def resolved_compiler(self, root: Path) -> str:
        """The compiler to drive the build: explicit, then bundled, then PATH."""
        if self.cxx:
            return self.expand(self.cxx)
        return self.bundled_clang(root) or "clang++"

    def resolved_vcpkg(self, root: Path) -> str:
        """The vcpkg root: explicit, then the first tree a dependency root holds, else ''."""
        if self.vcpkg_root:
            return self.expand(self.vcpkg_root)
        for tree in self.dependency_roots(root):
            if (tree / "vcpkg").is_dir():
                return str(tree / "vcpkg")
        return ""
