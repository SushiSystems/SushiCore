# gtest_filter.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Narrows one GoogleTest filter by another: the cases both of them select."""

from __future__ import annotations

from functools import lru_cache


def _split(text: str) -> tuple[list[str], list[str]]:
    """Return the positive and the negative patterns of a GoogleTest filter.

    An empty positive part selects everything, as GoogleTest reads it.
    """
    positive, _, negative = text.partition("-")
    return [pattern for pattern in positive.split(":") if pattern] or ["*"], \
        [pattern for pattern in negative.split(":") if pattern]


@lru_cache(maxsize=None)
def _both(first: str, second: str) -> frozenset[str]:
    """Return glob patterns whose union is exactly what *first* and *second* both match.

    ``*`` matches any run of characters and ``?`` any one, as GoogleTest reads them.
    """
    if not first and not second:
        return frozenset({""})
    if not first or not second:
        rest = first or second
        return frozenset({""}) if set(rest) == {"*"} else frozenset()
    one, two = first[0], second[0]
    if one == "*" and two == "*":
        return frozenset("*" + rest.lstrip("*") for rest in _both(first[1:], second) | _both(first, second[1:]))
    if one == "*":
        return _both(first[1:], second) | {two + rest for rest in _both(first, second[1:])}
    if two == "*":
        return _both(first, second[1:]) | {one + rest for rest in _both(first[1:], second)}
    if one == two or two == "?":
        head = one
    elif one == "?":
        head = two
    else:
        return frozenset()
    return frozenset(head + rest for rest in _both(first[1:], second[1:]))


def intersect_filters(size_filter: str, user_filter: str) -> str | None:
    """Return the GoogleTest filter that selects the cases *size_filter* and *user_filter* both select.

    GoogleTest filters cannot be joined by AND, so each pair of positive patterns, one from each
    filter, is replaced by the glob patterns that both of them match, and the negative patterns of
    both filters are kept.

    Args:
        size_filter: The filter a shard registers, such as ``Small_*:*/Small_*-Small_Slow.*``.
        user_filter: The filter the caller asked for, such as ``Small_Rect*``.

    Returns:
        The joined filter, or None when no case can match both.
    """
    if not user_filter:
        return size_filter
    wanted, unwanted = _split(size_filter)
    asked, refused = _split(user_filter)
    positive = sorted({pattern for one in wanted for two in asked for pattern in _both(one, two)})
    if not positive:
        return None
    negative = list(dict.fromkeys([*unwanted, *refused]))
    return ":".join(positive) + ("-" + ":".join(negative) if negative else "")
