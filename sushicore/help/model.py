"""The data a help screen is drawn from."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HelpSection:
    """Holds a heading and the term and text pairs listed under it."""

    heading: str
    entries: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class HelpModel:
    """Holds everything one help screen shows."""

    name: str
    description: str
    usage: str
    is_root: bool
    commands: tuple[HelpSection, ...]
    arguments: tuple[tuple[str, str], ...]
    options: tuple[tuple[str, str], ...]
    examples: tuple[tuple[str, str], ...]
