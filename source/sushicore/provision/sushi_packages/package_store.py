# package_store.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The folder of built Sushi packages: find one by key, stage an install, keep the most used."""

from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import Callable, Collection

from .package import K_PREFIX, Package
from .package_error import PackageError
from .package_key import PackageKey

#: The file that marks an install as complete and records the key's parts.
K_STAMP = "package.stamp.json"

#: The file whose content is the time a package was last chosen.
K_USED = ".used"

#: The suffix of a folder an install is still writing.
K_PARTIAL = ".partial"

#: The suffix of a folder that is being deleted.
K_TRASH = ".trash"

#: How many packages of one library the store keeps unless told otherwise.
K_DEFAULT_KEEP = 3

#: Seconds after which a ``.partial`` folder is taken for an interrupted install.
K_STALE_PARTIAL = 24 * 3600.0

#: How many times a rename is tried, and the seconds waited between tries.
K_RENAME_TRIES, K_RENAME_WAIT = 5, 0.2


class PackageStore:
    """Packages under ``<root>/<name>/<digest>/``, each complete only once its stamp exists."""

    def __init__(self, root: Path, keep: int = K_DEFAULT_KEEP,
                 clock: Callable[[], float] = time.time,
                 sleep: Callable[[float], None] = time.sleep,
                 warn: Callable[[str], None] = lambda _text: None) -> None:
        """Bind the store to *root*.

        Args:
            root: The ``<home>/packages`` folder.
            keep: How many packages of one library :meth:`prune` keeps.
            clock: Returns the time in seconds; replaced in tests.
            sleep: Waits between two rename tries; replaced in tests.
            warn: Receives the warning for a folder that could not be removed.

        Raises:
            PackageError: *keep* is below 1.
        """
        if keep < 1:
            raise PackageError(f"package_keep is {keep}; the store keeps at least one package.")
        self._root = root
        self._keep = keep
        self._clock = clock
        self._sleep = sleep
        self._warn = warn

    def find(self, key: PackageKey) -> Package | None:
        """Return the complete package of *key*, or None when there is none."""
        return self.find_digest(key.name, key.digest())

    def find_digest(self, name: str, digest: str) -> Package | None:
        """Return the complete package of *name* at *digest*, or None."""
        folder = self._root / name / digest
        try:
            stamp = json.loads((folder / K_STAMP).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return Package(name, digest, folder, stamp) if isinstance(stamp, dict) else None

    def stage(self, key: PackageKey) -> Path:
        """Return the empty prefix inside a fresh ``<digest>.partial`` folder for *key*.

        The caller holds the key lock, so a folder of that name is this key's own earlier
        attempt and is replaced.
        """
        partial = self._partial(key)
        shutil.rmtree(partial, ignore_errors=True)
        partial.mkdir(parents=True)
        return partial / K_PREFIX

    def commit(self, key: PackageKey, seconds: float) -> Package:
        """Write the stamp into the staged folder of *key* and rename it into place.

        Raises:
            PackageError: Nothing was installed into the staged prefix, or the rename keeps
                failing.
        """
        partial = self._partial(key)
        if not (partial / K_PREFIX).is_dir():
            raise PackageError(f"nothing was installed for {key.name} {key.short()}.")
        stamp = {"parts": key.parts(), "digest": key.digest(),
                 "installed_at": self._clock(), "build_seconds": round(seconds, 1)}
        (partial / K_STAMP).write_text(json.dumps(stamp, indent=2), encoding="utf-8")
        final = self._root / key.name / key.digest()
        self._replace(partial, final)
        package = Package(key.name, key.digest(), final, stamp)
        self.touch(package)
        return package

    def discard(self, key: PackageKey) -> None:
        """Delete the staged folder of *key*, which the caller made."""
        shutil.rmtree(self._partial(key), ignore_errors=True)

    def touch(self, package: Package) -> None:
        """Record that *package* was chosen now."""
        (package.root / K_USED).write_text(repr(self._clock()), encoding="utf-8")

    def prune(self, name: str, protect: Collection[str] = ()) -> list[str]:
        """Remove the least recently chosen packages of *name* beyond the keep count.

        A package is never removed when its digest is in *protect*, when a package of another
        library lists it in its ``below``, or while it is a fresh ``.partial`` of another
        process. A folder that cannot be renamed is skipped with a warning and retried at the
        next prune. Leftover ``.trash`` folders and day-old ``.partial`` folders are swept first.

        Returns:
            The digests removed.
        """
        folder = self._root / name
        if not folder.is_dir():
            return []
        self._sweep(folder)
        held = set(protect) | self._referenced(name)
        packages = [package for package in (
            self.find_digest(name, entry.name) for entry in folder.iterdir()
            if _is_package_folder(entry)) if package is not None]
        packages.sort(key=self._last_used, reverse=True)
        removed = []
        for package in packages[self._keep:]:
            if package.digest not in held and self._trash(package.root):
                removed.append(package.digest)
        return removed

    def _last_used(self, package: Package) -> float:
        """Return when *package* was last chosen, or its install time without a ``.used``."""
        try:
            return float((package.root / K_USED).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return float(package.stamp.get("installed_at", 0.0))

    def _referenced(self, name: str) -> set[str]:
        """Return the digests of *name* that a package of another library lists in its ``below``."""
        found: set[str] = set()
        for library in self._root.iterdir() if self._root.is_dir() else ():
            if not library.is_dir() or library.name == name or library.name.startswith("."):
                continue
            for entry in library.iterdir():
                package = (self.find_digest(library.name, entry.name)
                           if _is_package_folder(entry) else None)
                if package is not None:
                    found.update(digest for below, digest in package.below() if below == name)
        return found

    def _trash(self, folder: Path) -> bool:
        """Rename *folder* to ``.trash`` and delete it; report whether it is gone from the store."""
        trash = folder.with_name(folder.name + K_TRASH)
        try:
            shutil.rmtree(trash, ignore_errors=True)
            os.replace(folder, trash)
        except OSError as exc:
            self._warn(f"{folder} could not be removed now ({exc}); the next prune retries.")
            return False
        shutil.rmtree(trash, ignore_errors=True)
        return True

    def _sweep(self, folder: Path) -> None:
        """Delete the ``.trash`` folders of *folder* and the ``.partial`` folders past a day."""
        for entry in folder.iterdir():
            if entry.name.endswith(K_TRASH):
                shutil.rmtree(entry, ignore_errors=True)
            elif entry.name.endswith(K_PARTIAL):
                try:
                    age = self._clock() - entry.stat().st_mtime
                except OSError:
                    continue
                if age > K_STALE_PARTIAL:
                    shutil.rmtree(entry, ignore_errors=True)

    def _replace(self, source: Path, destination: Path) -> None:
        """Rename *source* over *destination*, trying again where a scanner holds the folder."""
        for attempt in range(K_RENAME_TRIES):
            try:
                if destination.exists():
                    shutil.rmtree(destination)
                os.replace(source, destination)
                return
            except OSError as exc:
                if attempt == K_RENAME_TRIES - 1:
                    raise PackageError(f"cannot move {source} to {destination}: {exc}") from exc
                self._sleep(K_RENAME_WAIT)

    def _partial(self, key: PackageKey) -> Path:
        """Return the staging folder of *key*."""
        return self._root / key.name / (key.digest() + K_PARTIAL)


def _is_package_folder(entry: Path) -> bool:
    """Report whether *entry* can be a package: a folder that is no link, partial or trash."""
    return (entry.is_dir() and not entry.name.startswith("@")
            and not entry.name.endswith((K_PARTIAL, K_TRASH)))
