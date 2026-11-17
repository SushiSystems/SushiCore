# theme_registry.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Holds the named themes a console builder can choose from."""

from __future__ import annotations

import typing
from collections.abc import Mapping
from typing import TYPE_CHECKING

from .errors import ConfigError

if TYPE_CHECKING:
    from .theme import Theme


@typing.final
class ThemeRegistry:
    """Maps a name to a theme; each builder of a console may hold its own."""

    def __init__(self, presets: Mapping[str, Theme] | None = None) -> None:
        """Start with a copy of *presets*, or empty when omitted."""
        self._presets: dict[str, Theme] = dict(presets or {})

    def register(self, name: str, theme: Theme) -> None:
        """Add or replace the theme found under *name*."""
        self._presets[name] = theme

    def get(self, name: str) -> Theme:
        """Return the theme registered under *name*.

        Raises:
            ConfigError: If no theme has that name; the message lists the known names.
        """
        try:
            return self._presets[name]
        except KeyError:
            known = ", ".join(sorted(self._presets))
            raise ConfigError(f"Unknown CLI theme '{name}'. Known themes: {known}") from None

    def known(self) -> tuple[str, ...]:
        """Return the registered names, sorted."""
        return tuple(sorted(self._presets))
