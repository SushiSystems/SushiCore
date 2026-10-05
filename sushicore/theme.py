# theme.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026 Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Color theme: the only piece of the presentation layer that knows about styles.

A ``Theme`` is pure data (SRP) — it has no idea how it gets rendered. New themes
are added by registering a preset (OCP); nothing here needs to change to
support a new color scheme.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace

from .errors import ConfigError


@dataclass(frozen=True)
class Theme:
    """Style tokens used by :class:`sushicore.console.Console`.

    Values are Rich style strings (e.g. ``"bold blue"``), kept as plain
    strings so a theme can be fully described in TOML with no code.
    """

    info: str = "bold blue"
    success: str = "bold green"
    warn: str = "bold yellow"
    error: str = "bold red"
    cmd: str = "cyan"
    header: str = "bold #f0a500"
    panel_border: str = "red"
    # The dashes beside a rule title, in the terminal's own colour; docs/architecture/OVERVIEW.md.
    rule_line: str = "default"
    # Secondary text and the rule under a table header.
    muted: str = "dim"

    def merged(self, overrides: dict) -> "Theme":
        """Return a copy with only the recognized keys in ``overrides`` applied."""
        known = {f.name for f in fields(self)}
        return replace(self, **{k: v for k, v in overrides.items() if k in known and v})

    def as_rich_styles(self) -> dict:
        """Style map for ``rich.theme.Theme`` (drop fields Rich doesn't map 1:1)."""
        return {
            "info": self.info,
            "success": self.success,
            "warn": self.warn,
            "error": self.error,
            "cmd": self.cmd,
            "header": self.header,
            "rule.line": self.rule_line,
            "muted": self.muted,
            # rich.progress reads these keys directly; see docs/architecture/OVERVIEW.md, theme.
            "bar.complete": self.header,
            "bar.finished": self.success,
            "bar.pulse": self.header,
            "progress.description": "",
            "progress.percentage": self.header,
            "progress.elapsed": "dim",
            "progress.spinner": self.header,
        }


# The sushiweb palette: grey text and one amber accent; see docs/architecture/OVERVIEW.md.
_SUSHIWEB = Theme(
    info="bold #9a9a94",
    success="bold #6bbf59",
    warn="bold #d9a441",
    error="bold #e0575c",
    cmd="bold #f0a500",
    header="bold #f0a500",
    panel_border="#e0575c",
    rule_line="default",
)

_THEME_PRESETS: dict[str, Theme] = {
    "default": _SUSHIWEB,
    "sushiweb": _SUSHIWEB,
    "mono": Theme(
        info="bold", success="bold", warn="bold", error="bold",
        cmd="bold", header="bold", panel_border="bold",
    ),
    "muted": Theme(
        info="blue", success="green", warn="yellow", error="red",
        cmd="dim cyan", header="#f0a500", panel_border="red",
    ),
}


def register_theme(name: str, theme: Theme) -> None:
    """Add or replace a named theme preset. Lets a downstream CLI ship its own."""
    _THEME_PRESETS[name] = theme


def get_theme(name: str) -> Theme:
    try:
        return _THEME_PRESETS[name]
    except KeyError:
        known = ", ".join(sorted(_THEME_PRESETS))
        raise ConfigError(f"Unknown CLI theme '{name}'. Known themes: {known}") from None


def known_themes() -> tuple[str, ...]:
    return tuple(sorted(_THEME_PRESETS))
