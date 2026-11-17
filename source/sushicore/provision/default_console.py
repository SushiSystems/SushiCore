# default_console.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The console a module gets when its ``ModuleProvision`` names none, set by the deprecated ``bind_console``."""

from __future__ import annotations

import warnings
from typing import Callable

from ..errors import SushiCoreError


class ConsoleNotBoundError(SushiCoreError, RuntimeError):
    """Reports a default console that nothing has bound."""


class DefaultConsole:
    """Holds the provider that ``bind_console`` set and returns the console it builds."""

    def __init__(self) -> None:
        """Start unbound."""
        self._provider: Callable[[], object] | None = None

    def bind(self, provider: Callable[[], object] | None) -> None:
        """Set the callable that returns the console; ``None`` unbinds."""
        self._provider = provider

    def __call__(self) -> object:
        """Return the bound console.

        Raises:
            ConsoleNotBoundError: Nothing is bound.
        """
        if self._provider is None:
            raise ConsoleNotBoundError(
                "sushicore.provision has no console; pass `console=` to ModuleProvision.")
        return self._provider()


DEFAULT_CONSOLE = DefaultConsole()
"""The default console of a ``ModuleProvision`` that names none."""


def bind_console(provider: Callable[[], object] | None) -> None:
    """Set the console a ``ModuleProvision`` without one prints through.

    Deprecated: pass ``console=`` to :class:`~sushicore.provision.module_provision.ModuleProvision`.

    Args:
        provider: Returns a :class:`sushicore.console.Console`; called on each use,
            so a lazily built console stays lazy. ``None`` unbinds.
    """
    warnings.warn(
        "sushicore.provision.bind_console is deprecated; pass console= to ModuleProvision.",
        DeprecationWarning, stacklevel=2)
    DEFAULT_CONSOLE.bind(provider)
