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
from typing import final

from .deprecated_name import warn_deprecated
from .icon_registry import IconRegistry


@final
@dataclass(frozen=True)
class IconSet:
    info: str = "[INFO]"
    success: str = "[SUCCESS]"
    warn: str = "[WARN]"
    error: str = "[ERROR]"

    def merged(self, overrides: dict) -> "IconSet":
        known = {f.name for f in fields(self)}
        return replace(self, **{k: v for k, v in overrides.items() if k in known and v})


DEFAULT_ICON_REGISTRY = IconRegistry({
    "text": IconSet(),
    "emoji": IconSet(info="ℹ️", success="✅", warn="⚠️", error="❌"),
    "minimal": IconSet(info="i", success="+", warn="!", error="x"),
    "none": IconSet(info="", success="", warn="", error=""),
})
"""The registry the module-level functions read when their caller passes none."""


def register_icon_set(
    name: str, icons: IconSet, *, presets: MutableMapping[str, IconSet] | None = None,
) -> None:
    """Add or replace a named icon set.

    Deprecated without *presets*: hold an :class:`~sushicore.icon_registry.IconRegistry` and
    pass it to ``build_console`` as ``icon_registry=``.

    Args:
        name: The name the set is found under.
        icons: The set to keep.
        presets: The mapping to add to; the default registry when None.
    """
    if presets is not None:
        presets[name] = icons
        return
    warn_deprecated("register_icon_set", "IconRegistry.register on a registry passed to build_console")
    DEFAULT_ICON_REGISTRY.register(name, icons)


def get_icon_set(name: str, *, presets: Mapping[str, IconSet] | None = None) -> IconSet:
    """Return the icon set registered under *name*.

    Args:
        name: The name the set was registered under.
        presets: The mapping to look in; the default registry when None.

    Raises:
        ConfigError: If no set has that name; the message lists the known names.
    """
    return (DEFAULT_ICON_REGISTRY if presets is None else IconRegistry(presets)).get(name)


def known_icon_sets(*, presets: Mapping[str, IconSet] | None = None) -> tuple[str, ...]:
    """Return the registered icon set names, sorted.

    Args:
        presets: The mapping to list; the default registry when None.
    """
    return (DEFAULT_ICON_REGISTRY if presets is None else IconRegistry(presets)).known()
