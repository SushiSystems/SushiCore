# stack_config.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Resolves the toolchain of a module that consumes the shared dependency tree.

The reasoning is in docs/architecture/OVERVIEW.md, section `stack_config`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Callable, ClassVar, Collection, Mapping

from . import deps_fragment
from .provision import home as provision_home
from .provision import sushi_sources
from .provision.sushi_packages import PackageRequest, PackageSet, default_resolver
from .provision.module_manifest import fragment_path
from .provision.config import ProvisionSettings


@dataclass
class StackConfig(ProvisionSettings):
    """A module config that resolves its toolchain from the shared tree.

    Subclasses declare their sibling checkouts as fields. Everything below is
    the same for all of them.
    """

    #: The fragment below the project root when a subclass names one; None reads the module's manifest.
    fragment: ClassVar[str | None] = None

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
        """Return the checkout of the Sushi library *name*, or None when there is none.

        The order is ``<NAME>_DIR``, the sibling ``../<name>``, then the copy
        ``setup`` fetched at the version the fragment pins.

        @param root This module's project root.
        @param name The library's directory name, e.g. ``"sushiruntime"``.
        """
        found = self.resolve_sushi(root, name)
        return found.path if found is not None else None

    def sushi_pins(self, root: Path) -> list[deps_fragment.SushiPin]:
        """Return the pins of this module's fragment, none when it has no fragment.

        @param root This module's project root.
        """
        return deps_fragment.pins_at(root / (self.fragment or fragment_path(root)))

    def resolve_sushi(self, root: Path, name: str) -> sushi_sources.ResolvedSource | None:
        """Return the checkout of the Sushi library *name* and where it was found.

        @param root This module's project root.
        @param name The library's directory name.
        """
        versions = {pin.name: pin.version for pin in self.sushi_pins(root)}
        configured = getattr(self, f"{name}_dir", "")
        return sushi_sources.resolve(root, name, versions.get(name, ""),
                                     self.expand(configured) if configured else "")

    def sushi_definitions(self, root: Path, packaged: PackageSet | None = None) -> list[str]:
        """Return ``-D<NAME>_DIR=<path>`` for each pinned Sushi library that resolves.

        A library in *packaged* is consumed as a built package and is skipped: its
        ``-D<Package>_DIR`` comes from :meth:`PackageSet.definitions`. A library the package
        set left out is skipped as well, since the consumer asked not to link it. The CLI hands these to
        the CMake configure; CMake never downloads.

        @param root This module's project root.
        @param packaged The packages :meth:`sushi_packages` resolved, or None.
        """
        skipped = ({*packaged.names(), *packaged.left_out}
                   if packaged is not None else set())
        definitions = []
        for pin in self.sushi_pins(root):
            found = self.resolve_sushi(root, pin.name)
            if found is not None and pin.name not in skipped:
                variable = sushi_sources.directory_variable(pin.name)
                definitions.append(f"-D{variable}={found.path}")
        return definitions

    def sushi_packages(self, root: Path, build_type: str,
                       options: Mapping[str, tuple[str, ...]] | None = None,
                       report: Callable[[str], None] = print,
                       warn: Callable[[str], None] = print,
                       compiler: str = "",
                       libraries: Collection[str] | None = None) -> PackageSet:
        """Return a built package of every Sushi library this module's chain links, or of *libraries*.

        A package that the store lacks is built through the library's own CLI. One line per
        library goes to *report*: ``reused <short>`` or ``built <short> in <s>s``.

        @param root      This module's project root.
        @param build_type The build type of this configure, such as ``release``.
        @param options   The extra ``build`` arguments of a library, by library name.
        @param report    Receives one line per library.
        @param warn      Receives the warnings.
        @param compiler  The compiler of this build; :meth:`resolved_compiler` when empty.
        @param libraries The libraries to resolve, with what each depends on; None resolves every
                         library of the closure. The package key of a library does not change.
        @raises sushicore.provision.sushi_packages.PackageError A package cannot be chosen.
        """
        vcpkg = self.resolved_vcpkg(root)
        configured = {item.name[:-len("_dir")]: self.expand(getattr(self, item.name))
                      for item in fields(self)
                      if item.name.endswith("_dir") and getattr(self, item.name)}
        request = PackageRequest(
            owner=root.name.lower(), root=root, compiler=compiler or self.resolved_compiler(root),
            build_type=build_type, options=dict(options or {}), configured=configured,
            fragment=self.fragment or fragment_path(root), vcpkg_root=Path(vcpkg) if vcpkg else None,
            triplet=self.vcpkg_triplet, libraries=libraries)
        cmake = self.expand(self.cmake_exe) if self.cmake_exe else "cmake"
        return default_resolver(self.package_keep, report, warn, cmake=cmake).resolve(request)

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
        """The vcpkg root: explicit, then the first tree a dependency root holds, else ''.

        A config that sets ``use_vcpkg`` to false resolves none, whatever tree is present: the hub's
        defaults turn vcpkg off on Linux, where apt holds the libraries.
        """
        if self.use_vcpkg is False:
            return ""
        if self.vcpkg_root:
            return self.expand(self.vcpkg_root)
        for tree in self.dependency_roots(root):
            if (tree / "vcpkg").is_dir():
                return str(tree / "vcpkg")
        return ""
