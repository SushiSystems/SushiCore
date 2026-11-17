# events.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The event vocabulary the JSON renderer writes: kind names and one serialisation."""

from __future__ import annotations

import json

from .errors import SushiCoreError

EVENT_KINDS: frozenset[str] = frozenset({
    "line", "command", "header", "panel", "table", "progress", "result", "prompt",
})


class UnknownEventKindError(SushiCoreError, ValueError):
    """Reports an event kind that ``EVENT_KINDS`` does not list."""


def event_line(kind: str, **fields) -> str:
    """Serialise one event as a single JSON object with ``event`` as its first key.

    Args:
        kind: One of ``EVENT_KINDS``.
        **fields: The event's payload, kept in the order given.

    Returns:
        The JSON text without a trailing newline; embedded newlines are escaped.

    Raises:
        UnknownEventKindError: If ``kind`` is not in ``EVENT_KINDS``.
    """
    if kind not in EVENT_KINDS:
        raise UnknownEventKindError(f"unknown event kind {kind!r}; known kinds: {', '.join(sorted(EVENT_KINDS))}")
    return json.dumps({"event": kind, **fields}, ensure_ascii=False, separators=(",", ":"))
