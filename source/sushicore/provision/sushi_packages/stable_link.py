# stable_link.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The link a consumer's flags name, which follows the package its closure chose."""

from __future__ import annotations

import os
from pathlib import Path

from .. import links

#: What the link name starts with, so a package digest folder is never taken for a link.
K_MARK = "@"


class StableLink:
    """Reads and moves the per-consumer links under ``<packages>/<name>/``."""

    def __init__(self, root: Path, windows: bool = os.name == "nt") -> None:
        """Bind the links to the packages folder.

        Args:
            root: The ``<home>/packages`` folder.
            windows: Whether a link is a directory junction; a symlink otherwise.
        """
        self._root = root
        self._windows = windows

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
        if self._windows:
            if links.is_dir_link(link):
                links.remove_dir_link(link)
            links.make_dir_link(link, target)
            return link
        beside = link.with_name(link.name + ".new")
        if beside.is_symlink():
            beside.unlink()
        os.symlink(target.resolve(), beside, target_is_directory=True)
        os.replace(beside, link)
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
