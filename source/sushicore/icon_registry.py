# icon_registry.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Holds the named icon sets a console builder can choose from."""

from __future__ import annotations

import typing
from collections.abc import Mapping
from typing import TYPE_CHECKING

from .errors import ConfigError

if TYPE_CHECKING:
    from .icons import IconSet


@typing.final
class IconRegistry:
    """Maps a name to an icon set; each builder of a console may hold its own."""

    def __init__(self, presets: Mapping[str, IconSet] | None = None) -> None:
        """Start with a copy of *presets*, or empty when omitted."""
        self._presets: dict[str, IconSet] = dict(presets or {})

    def register(self, name: str, icons: IconSet) -> None:
        """Add or replace the set found under *name*."""
        self._presets[name] = icons

    def get(self, name: str) -> IconSet:
        """Return the set registered under *name*.

        Raises:
            ConfigError: If no set has that name; the message lists the known names.
        """
        try:
            return self._presets[name]
        except KeyError:
            known = ", ".join(sorted(self._presets))
            raise ConfigError(f"Unknown CLI icon set '{name}'. Known icon sets: {known}") from None

    def known(self) -> tuple[str, ...]:
        """Return the registered names, sorted."""
        return tuple(sorted(self._presets))
