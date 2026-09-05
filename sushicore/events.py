"""The event vocabulary the JSON renderer writes: kind names and one serialisation."""

from __future__ import annotations

import json

EVENT_KINDS: frozenset[str] = frozenset({
    "line", "command", "header", "panel", "table", "progress", "result", "prompt",
})


def event_line(kind: str, **fields) -> str:
    """Serialise one event as a single JSON object with ``event`` as its first key.

    Args:
        kind: One of ``EVENT_KINDS``.
        **fields: The event's payload, kept in the order given.

    Returns:
        The JSON text without a trailing newline; embedded newlines are escaped.

    Raises:
        ValueError: If ``kind`` is not in ``EVENT_KINDS``.
    """
    if kind not in EVENT_KINDS:
        raise ValueError(f"unknown event kind {kind!r}; known kinds: {', '.join(sorted(EVENT_KINDS))}")
    return json.dumps({"event": kind, **fields}, ensure_ascii=False, separators=(",", ":"))
