# plain_text.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Removes Rich markup tags from text, for the readers that are programs."""

from __future__ import annotations


def plain_text(text: str) -> str:
    """Returns *text* with its Rich markup tags removed, or *text* as it is when it holds no valid markup.

    Rich loads on the first call, so importing this module costs a program that never calls it nothing.
    """
    from rich.errors import MarkupError
    from rich.text import Text

    try:
        return Text.from_markup(text).plain
    except MarkupError:
        return text
