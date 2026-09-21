"""Decides whether a terminal's background is dark, from a setting and COLORFGBG."""

from __future__ import annotations

from typing import Mapping

K_DARK = "dark"
K_LIGHT = "light"
K_AUTO = "auto"
K_VALUES = (K_AUTO, K_DARK, K_LIGHT)

K_VARIABLE = "COLORFGBG"
K_DARK_INDICES = frozenset({0, 1, 2, 3, 4, 5, 6, 8})


def is_dark_background(setting: str, environ: Mapping[str, str]) -> bool:
    """Report whether the background is dark: the setting when it names one, COLORFGBG otherwise.

    Args:
        setting: One of ``auto``, ``dark`` or ``light``; anything else reads as ``auto``.
        environ: The environment to read ``COLORFGBG`` from.
    """
    if setting == K_DARK:
        return True
    if setting == K_LIGHT:
        return False
    return _names_a_dark_colour(environ.get(K_VARIABLE, ""))


def _names_a_dark_colour(value: str) -> bool:
    """Report whether COLORFGBG's last field is a colour index this module calls dark."""
    background = value.rsplit(";", 1)[-1]
    # An unreadable value is not dark.
    if not background.isdecimal():
        return False
    return int(background) in K_DARK_INDICES
