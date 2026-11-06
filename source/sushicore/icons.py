# icons.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Icon/prefix sets: the text glyphs printed before a message.

Kept separate from :mod:`sushicore.theme` (which only owns color) so the two
can be swapped independently — e.g. keep the default color theme but switch
from bracketed text prefixes to emoji, or drop icons entirely on a legacy
console that cannot render them.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass, fields, replace

from .errors import ConfigError


@dataclass(frozen=True)
class IconSet:
    info: str = "[INFO]"
    success: str = "[SUCCESS]"
    warn: str = "[WARN]"
    error: str = "[ERROR]"

    def merged(self, overrides: dict) -> "IconSet":
        known = {f.name for f in fields(self)}
        return replace(self, **{k: v for k, v in overrides.items() if k in known and v})


_ICON_PRESETS: dict[str, IconSet] = {
    "text": IconSet(),
    "emoji": IconSet(info="ℹ️", success="✅", warn="⚠️", error="❌"),
    "minimal": IconSet(info="i", success="+", warn="!", error="x"),
    "none": IconSet(info="", success="", warn="", error=""),
}


def register_icon_set(
    name: str, icons: IconSet, *, presets: MutableMapping[str, IconSet] | None = None,
) -> None:
    """Add or replace a named icon set.

    Args:
        name: The name the set is found under.
        icons: The set to keep.
        presets: The registry to add to; the process-wide one when None.
    """
    (_ICON_PRESETS if presets is None else presets)[name] = icons


def get_icon_set(name: str, *, presets: Mapping[str, IconSet] | None = None) -> IconSet:
    """Return the icon set registered under *name*.

    Args:
        name: The name the set was registered under.
        presets: The registry to look in; the process-wide one when None.

    Raises:
        ConfigError: If no set has that name; the message lists the known names.
    """
    registry = _ICON_PRESETS if presets is None else presets
    try:
        return registry[name]
    except KeyError:
        known = ", ".join(sorted(registry))
        raise ConfigError(f"Unknown CLI icon set '{name}'. Known icon sets: {known}") from None


def known_icon_sets(*, presets: Mapping[str, IconSet] | None = None) -> tuple[str, ...]:
    """Return the registered icon set names, sorted.

    Args:
        presets: The registry to list; the process-wide one when None.
    """
    return tuple(sorted(_ICON_PRESETS if presets is None else presets))
