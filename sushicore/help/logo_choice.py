# logo_choice.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026 Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Chooses which logo, if any, fits a console."""

from __future__ import annotations

from ..ui.logo import Logo


def choose_logo(*, width: int, dark_background: bool) -> Logo | None:
    """Return the widest logo that fits ``width`` columns, or None when none does."""
    candidates = (Logo(glow=dark_background), Logo(wordmark=False, glow=dark_background))
    for logo in candidates:
        if logo.width <= width:
            return logo
    return None
