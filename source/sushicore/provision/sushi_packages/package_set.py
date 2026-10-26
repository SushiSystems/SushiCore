# package_set.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The packages chosen for a consumer's closure, and what the consumer takes from them."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .package import K_PREFIX, Package
from .package_key import PackageKey


@dataclass(frozen=True, slots=True)
class ResolvedPackage:
    """One library of the closure and the package chosen for it."""

    package: Package
    #: The key the package was found or built under; None for a package a parent forced.
    key: PackageKey | None
    built: bool
    seconds: float = 0.0
    #: The consumer's stable link to the package folder; None when none was published.
    link: Path | None = None

    @property
    def name(self) -> str:
        """Return the library's name."""
        return self.package.name

    def line(self) -> str:
        """Return ``<name>: reused <short>`` or ``<name>: built <short> in <s>s``."""
        short = self.package.digest[:12]
        if self.built:
            return f"{self.name}: built {short} in {self.seconds:.1f}s"
        return f"{self.name}: reused {short}"

    def prefix(self) -> Path:
        """Return the prefix a consumer uses: through the stable link when there is one."""
        return self.link / K_PREFIX if self.link is not None else self.package.prefix

    def config_folder(self) -> Path:
        """Return the folder of the library's CMake config, below :meth:`prefix`."""
        real = self.package.config_folder()
        return self.prefix() / real.relative_to(self.package.prefix)


@dataclass(frozen=True, slots=True)
class PackageSet:
    """The resolved packages of a closure, in dependency order, and the libraries left out."""

    packages: tuple[ResolvedPackage, ...]
    #: Libraries of the closure that the consumer asked not to resolve.
    left_out: tuple[str, ...] = ()

    def names(self) -> list[str]:
        """Return the library names in dependency order."""
        return [item.name for item in self.packages]

    def get(self, name: str) -> ResolvedPackage | None:
        """Return the resolved package of *name*, or None."""
        return next((item for item in self.packages if item.name == name), None)

    def lines(self) -> list[str]:
        """Return one ``reused`` or ``built`` line per library, in dependency order."""
        return [item.line() for item in self.packages]

    def definitions(self) -> list[str]:
        """Return ``-D<Package>_DIR=<config folder>`` for every package of the closure."""
        return [f"-D{folder.name}_DIR={folder}"
                for folder in (item.config_folder() for item in self.packages)]

    def run_dirs(self, platform: str) -> list[str]:
        """Return the run-time folders of every package, the last-resolved library first."""
        found: list[str] = []
        for item in reversed(self.packages):
            base = item.prefix()
            relative = [path.relative_to(item.package.prefix)
                        for path in item.package.run_dirs(platform)]
            found.extend(str(base / path) for path in relative)
        return found
