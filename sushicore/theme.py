"""Color theme: the only piece of the presentation layer that knows about styles.

A ``Theme`` is pure data (SRP) — it has no idea how it gets rendered. New themes
are added by registering a preset (OCP); nothing here needs to change to
support a new color scheme.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace


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
    # The dashes either side of a `console.rule()` title (and, via Rich's
    # theme-wide "rule.line" key, anything else that asks for that style).
    # "default" means "the terminal's own foreground color" rather than a
    # fixed color — it renders white on a dark terminal, black on a light
    # one, instead of a color chosen without knowing the user's background.
    rule_line: str = "default"

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
            # rich.progress.Progress's built-in columns (SpinnerColumn,
            # BarColumn, the [progress.*] TextColumn templates) read these
            # theme keys directly — override them so `rich.progress.track()`
            # and any bare `Progress(...)` in a downstream CLI is themed for
            # free, with no call site changes.
            "bar.complete": self.header,
            "bar.finished": self.success,
            "bar.pulse": self.header,
            "progress.description": "",
            "progress.percentage": self.header,
            "progress.elapsed": "dim",
            "progress.spinner": self.header,
        }


# Lifted from sushiweb's palette (D:/Projects/sushiweb/src/styles/global.css):
# near-monochrome (grey text on near-black/near-white) plus a single amber
# accent (#f0a500), rather than the rainbow-of-hues terminal default. Semantic
# colors are desaturated to sit alongside that accent instead of competing
# with it; the accent itself is reused for both header rules and inline
# commands, matching the site's one-accent-does-everything branding.
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
        raise ValueError(f"Unknown CLI theme '{name}'. Known themes: {known}") from None


def known_themes() -> tuple[str, ...]:
    return tuple(sorted(_THEME_PRESETS))
