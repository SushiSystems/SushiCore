# package_locks.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The three locks around a package build: the checkout, the key and the consumer's link."""

from __future__ import annotations

import contextlib
import hashlib
import re
from pathlib import Path
from typing import Callable, ContextManager, Iterator

from ..lock import ProvisionLock
from .package_error import PackageError

#: The folder, below the packages root, that holds the lock files.
K_LOCKS = ".locks"

#: The rank of each lock. A lock may be taken only while no higher rank is held.
K_CHECKOUT, K_KEY, K_LINK = 0, 1, 2

#: The ranks by name, for the message of a refused order.
_NAMES = {K_CHECKOUT: "checkout", K_KEY: "key", K_LINK: "link"}

#: Opens the lock at a path, waiting at most a number of seconds.
LockFactory = Callable[[Path, float], ContextManager[object]]


def _file_safe(text: str) -> str:
    """Return *text* with every character a file name should not hold replaced by ``_``."""
    return re.sub(r"[^a-z0-9._-]", "_", text.lower())


class PackageLocks:
    """Hands out the locks in the one order the design allows: checkout, key, link."""

    def __init__(self, root: Path, timeout: float = 600.0,
                 factory: LockFactory = ProvisionLock) -> None:
        """Bind the locks to the packages folder.

        Args:
            root: The ``<home>/packages`` folder.
            timeout: Seconds to wait for a lock another process holds.
            factory: Opens a lock file; replaced in tests.
        """
        self._root = root
        self._timeout = timeout
        self._factory = factory
        self._held: list[int] = []

    def checkout(self, name: str, checkout: Path) -> ContextManager[None]:
        """Return the lock held while a build runs in *checkout*."""
        where = hashlib.sha256(str(checkout.resolve()).encode("utf-8")).hexdigest()[:12]
        return self._take(K_CHECKOUT, f"{name}-{where}.lock")

    def key(self, name: str, digest: str) -> ContextManager[None]:
        """Return the lock held while the package *digest* of *name* is installed."""
        return self._take(K_KEY, f"{name}-{digest}.lock")

    def link(self, name: str, consumer: str) -> ContextManager[None]:
        """Return the lock held while *consumer*'s link to *name* changes."""
        return self._take(K_LINK, f"{name}-link-{_file_safe(consumer)}.lock")

    @contextlib.contextmanager
    def _take(self, rank: int, file_name: str) -> Iterator[None]:
        """Take the lock *file_name* of *rank*, refusing an order the design forbids."""
        if self._held and max(self._held) > rank:
            raise PackageError(
                f"the {_NAMES[rank]} lock was asked for while the {_NAMES[max(self._held)]} "
                "lock is held; the order is checkout, key, link.")
        with self._factory(self._root / K_LOCKS / file_name, self._timeout):
            self._held.append(rank)
            try:
                yield
            finally:
                self._held.pop()
