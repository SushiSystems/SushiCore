# default_console.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The console a module gets when its ``ModuleProvision`` names none, set by the deprecated ``bind_console``."""

from __future__ import annotations

import warnings
from typing import Callable, TypeVar, cast, final

from ..errors import SushiCoreError
from ..deprecated_name import warn_deprecated
from .provision_console import ProvisionConsole

_ConsoleT = TypeVar("_ConsoleT")


class ConsoleNotBoundError(SushiCoreError, RuntimeError):
    """Reports a default console that nothing has bound."""


@final
class DefaultConsole:
    """Holds the provider that ``bind_console`` set and returns the console it builds."""

    def __init__(self) -> None:
        """Start unbound."""
        self._provider: Callable[[], ProvisionConsole] | None = None

    def bind(self, provider: Callable[[], ProvisionConsole] | None) -> None:
        """Set the callable that returns the console; ``None`` unbinds."""
        self._provider = provider

    def __call__(self) -> ProvisionConsole:
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


def bind_console(provider: Callable[[], ProvisionConsole] | None) -> None:
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


@final
class _DefaultConsoleProxy:
    """Forwards each attribute to the default console as it is read, so it may be bound later."""

    def __getattr__(self, name: str) -> object:
        """Return *name* of the console the default provider returns now."""
        return getattr(DEFAULT_CONSOLE(), name)


def console_or_default(console: _ConsoleT | None, owner: str, *, depth: int = 2) -> _ConsoleT:
    """Return *console*, or the default console with a deprecation warning when it is ``None``.

    The default is read on each use. Called as the first line of a deprecated-optional
    ``console=`` argument, so the warning points at the caller of *owner*.

    Args:
        owner: The name of the constructor or function that took it.
        depth: The frames from the warning to the caller of *owner*.
    """
    if console is not None:
        return console
    warn_deprecated(f"{owner} without console=", "passing console=", depth=depth)
    return cast(_ConsoleT, _DefaultConsoleProxy())
