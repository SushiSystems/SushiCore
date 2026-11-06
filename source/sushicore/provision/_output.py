# _output.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The one console every provision module prints through, bound by the consuming CLI."""

from __future__ import annotations

from typing import Callable


class ConsoleProxy:
    """Forwards every attribute to the console the bound provider returns."""

    def __init__(self) -> None:
        """Start unbound."""
        self._provider: Callable[[], object] | None = None

    def bind(self, provider: Callable[[], object] | None) -> None:
        """Set the callable that returns the console; ``None`` unbinds."""
        self._provider = provider

    def __getattr__(self, name: str):
        """Resolve *name* on the bound console."""
        provider = self.__dict__.get("_provider")
        if provider is None:
            raise RuntimeError(
                "sushicore.provision has no console; call "
                "sushicore.provision.bind_console(provider) first.")
        return getattr(provider(), name)


console = ConsoleProxy()


def bind_console(provider: Callable[[], object] | None) -> None:
    """Set the callable that returns the console provision prints through.

    Args:
        provider: Returns a :class:`sushicore.console.Console`; called on each use,
            so a lazily built console stays lazy. ``None`` unbinds.
    """
    console.bind(provider)
