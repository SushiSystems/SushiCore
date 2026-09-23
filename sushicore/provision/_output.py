# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The one console every provision module prints through, bound by the consuming CLI."""

from __future__ import annotations

from typing import Callable

_provider: Callable[[], object] | None = None


def bind_console(provider: Callable[[], object] | None) -> None:
    """Set the callable that returns the console provision prints through.

    Args:
        provider: Returns a :class:`sushicore.console.Console`; called on each use,
            so a lazily built console stays lazy. ``None`` unbinds.
    """
    global _provider
    _provider = provider


class _ConsoleProxy:
    """Forwards every attribute to the console the bound provider returns."""

    def __getattr__(self, name: str):
        """Resolve *name* on the bound console."""
        if _provider is None:
            raise RuntimeError(
                "sushicore.provision has no console; call "
                "sushicore.provision.bind_console(provider) first.")
        return getattr(_provider(), name)


console = _ConsoleProxy()
