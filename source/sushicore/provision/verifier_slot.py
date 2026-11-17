# verifier_slot.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Holds the verifier a run binds for the download sites, in place of a module-level binding."""

from __future__ import annotations

import typing
from collections.abc import Callable, Iterator
from contextlib import contextmanager

from .download_checking import DownloadChecking


@typing.final
class VerifierSlot:
    """Holds the verifier of the current run, or a fresh fallback that pins nothing."""

    def __init__(self, fallback: Callable[[], DownloadChecking]) -> None:
        """Start holding a verifier built by *fallback*, which also builds each one used after an unbind."""
        self._fallback = fallback
        self._current = fallback()

    def current(self) -> DownloadChecking:
        """Return the bound verifier, or the fallback one when nothing is bound."""
        return self._current

    def bind(self, verifier: DownloadChecking | None) -> None:
        """Make *verifier* the current one; ``None`` swaps in a new fallback verifier."""
        self._current = self._fallback() if verifier is None else verifier

    @contextmanager
    def holding(self, verifier: DownloadChecking) -> Iterator[None]:
        """Hold *verifier* for the duration of the block, then return to the fallback."""
        self.bind(verifier)
        try:
            yield
        finally:
            self.bind(None)
