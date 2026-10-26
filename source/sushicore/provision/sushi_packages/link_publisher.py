# link_publisher.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Points a consumer's stable link at the package its closure chose."""

from __future__ import annotations

from pathlib import Path

from .package import Package
from .package_error import PackageError
from .package_locks import PackageLocks
from .stable_link import StableLink


class LinkPublisher:
    """Sets the per-consumer link of a package under the link lock."""

    def __init__(self, locks: PackageLocks, link: StableLink) -> None:
        """Bind the publisher to the locks and the link store.

        Args:
            locks: Hands out the link lock.
            link: Moves the link.
        """
        self._locks = locks
        self._link = link

    def publish(self, package: Package, config: str, consumer: str) -> Path:
        """Point the link of *consumer* for *config* at *package*, and return the link.

        Raises:
            PackageError: The link cannot be created.
        """
        with self._locks.link(package.name, consumer):
            try:
                return self._link.point(package.name, config, consumer, package.root)
            except OSError as exc:
                raise PackageError(
                    f"cannot link {package.name} {package.digest[:12]} for {consumer}: {exc}"
                ) from exc

    def protected(self, name: str) -> set[str]:
        """Return the digests of *name* that any consumer's link points at."""
        return self._link.targets(name)
