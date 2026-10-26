# forced_packages.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Reads the packages a parent CLI handed to a nested build."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Mapping, Sequence

from .package import Package
from .package_environment import K_MARKER, package_variable
from .package_error import PackageError
from .package_store import PackageStore


class ForcedPackages:
    """Turns the ``<NAME>_PACKAGE`` variables of a nested build into stored packages."""

    def __init__(self, env: Mapping[str, str], store: PackageStore,
                 warn: Callable[[str], None] = lambda _text: None) -> None:
        """Bind the reader to the environment and the store.

        Args:
            env: The environment of the running CLI.
            store: Finds the package a variable names.
            warn: Receives the warning for a variable that is ignored.
        """
        self._env = {key.upper(): value for key, value in env.items()}
        self._store = store
        self._warn = warn

    def read(self, names: Sequence[str], toolchain: str, build_type: str) -> dict[str, Package]:
        """Return the forced package of each library in *names* that has a variable.

        Without the nested marker every variable is ignored, with one warning each: a stale
        variable in a shell must not choose a package.

        Args:
            names: The libraries of the closure.
            toolchain: The toolchain identity of the request.
            build_type: The build type of the request, lower case.

        Raises:
            PackageError: A package is not in the store, or has another toolchain or build type.
        """
        nested = self._env.get(K_MARKER) == "1"
        forced: dict[str, Package] = {}
        for name in names:
            value = self._env.get(package_variable(name))
            if not value:
                continue
            if not nested:
                self._warn(f"{package_variable(name)} is set but this is not a nested build; "
                           "it is ignored.")
                continue
            forced[name] = self._take(name, Path(value), toolchain, build_type)
        return forced

    def _take(self, name: str, prefix: Path, toolchain: str, build_type: str) -> Package:
        """Return the stored package whose prefix is *prefix*, checked against the request."""
        digest = prefix.parent.name
        package = self._store.find_digest(name, digest)
        if package is None:
            raise PackageError(
                f"{package_variable(name)} names {digest[:12]}, which is not a complete package "
                "of the store.")
        if package.toolchain != toolchain or package.build_type != build_type:
            raise PackageError(
                f"{package_variable(name)} names a package of toolchain {package.toolchain} and "
                f"build type {package.build_type}; the request is toolchain {toolchain} and "
                f"build type {build_type}.")
        return package
