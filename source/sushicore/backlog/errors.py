# errors.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The failures the backlog commands report as one line."""

from __future__ import annotations

from ..errors import SushiCoreError


class BacklogError(SushiCoreError):
    """Reports a backlog that cannot be read or a change the backlog refuses."""


class RowError(BacklogError):
    """Reports a table row that is not in the shape the tool writes."""


class EntryNotFoundError(BacklogError):
    """Reports an ID that names no open entry."""


class RefusedChangeError(BacklogError):
    """Reports a change that would break a rule of the backlog, such as closing a cited entry."""
