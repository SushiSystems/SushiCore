# stable_link.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The link a consumer's flags name, which follows the package its closure chose."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .. import links
from ..host import IHost, current_host

#: What the link name starts with, so a package digest folder is never taken for a link.
K_MARK = "@"


class ILinkStore(Protocol):
    """Moves the per-consumer links and says which digests they name."""

    def point(self, name: str, config: str, consumer: str, target: Path) -> Path:
        """Make the link of *consumer* name *target*, and return the link."""

    def targets(self, name: str) -> set[str]:
        """Return the digests, as folder names, that any link of *name* points at."""


class MemoryLinks:
    """Keeps links in a dictionary and touches no folder.

    Args:
        error: What :meth:`point` raises; None for links that always succeed.
    """

    def __init__(self, error: OSError | None = None) -> None:
        """Start with no link."""
        self._error = error
        self._links: dict[Path, Path] = {}

    def point(self, name: str, config: str, consumer: str, target: Path) -> Path:
        """Keep the link of *consumer* naming *target*, and return its path.

        Raises:
            OSError: The store was made to fail.
        """
        if self._error is not None:
            raise self._error
        link = Path(name) / f"{K_MARK}{config}-{consumer}"
        self._links[link] = target
        return link

    def targets(self, name: str) -> set[str]:
        """Return the folder names the links of *name* name."""
        return {target.name for link, target in self._links.items() if link.parent.name == name}


class StableLink:
    """Reads and moves the per-consumer links under ``<packages>/<name>/``."""

    def __init__(self, root: Path, host: IHost | None = None) -> None:
        """Bind the links to the packages folder.

        Args:
            root: The ``<home>/packages`` folder.
            host: The host whose links are made; the running one's when ``None``.
        """
        self._root = root
        self._host = host or current_host()

    def path(self, name: str, config: str, consumer: str) -> Path:
        """Return ``<root>/<name>/@<config>-<consumer>``."""
        return self._root / name / f"{K_MARK}{config}-{consumer}"

    def point(self, name: str, config: str, consumer: str, target: Path) -> Path:
        """Make the link of *consumer* name *target*, and return the link.

        On Windows the junction is deleted and created again; the consumer's own build is the
        only reader of it, and the caller holds the link lock. Elsewhere the new symlink is
        created beside the old one and renamed over it, so a reader never sees it missing.

        Raises:
            OSError: The link cannot be created.
        """
        link = self.path(name, config, consumer)
        link.parent.mkdir(parents=True, exist_ok=True)
        self._host.replace_dir_link(link, target)
        return link

    def targets(self, name: str) -> set[str]:
        """Return the digests, as folder names, that any link of *name* points at."""
        folder = self._root / name
        if not folder.is_dir():
            return set()
        found = set()
        for entry in folder.iterdir():
            if entry.name.startswith(K_MARK):
                target = links.link_target(entry)
                if target is not None:
                    found.add(target.name)
        return found
