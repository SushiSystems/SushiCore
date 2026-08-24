"""Icon/prefix sets: the text glyphs printed before a message.

Kept separate from :mod:`sushicore.theme` (which only owns color) so the two
can be swapped independently — e.g. keep the default color theme but switch
from bracketed text prefixes to emoji, or drop icons entirely on a legacy
console that cannot render them.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace


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


def register_icon_set(name: str, icons: IconSet) -> None:
    _ICON_PRESETS[name] = icons


def get_icon_set(name: str) -> IconSet:
    try:
        return _ICON_PRESETS[name]
    except KeyError:
        known = ", ".join(sorted(_ICON_PRESETS))
        raise ValueError(f"Unknown CLI icon set '{name}'. Known icon sets: {known}") from None


def known_icon_sets() -> tuple[str, ...]:
    return tuple(sorted(_ICON_PRESETS))
