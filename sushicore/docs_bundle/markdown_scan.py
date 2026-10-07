# markdown_scan.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Reads what a Markdown page links to and what it is called.

Inline links only; `docs/reference/DOCS_BUNDLE.md` records the limit.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from urllib.parse import unquote

K_FENCE = re.compile(r"^\s{0,3}(```|~~~)")
K_CODE_SPAN = re.compile(r"`[^`]*`")
K_LINK = re.compile(r"\]\(\s*(?:<([^>\n]*)>|([^\s)]+))[^)\n]*\)")
K_HEADING = re.compile(r"^#\s+(.*?)\s*#*\s*$")
K_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


@dataclass(frozen=True, slots=True)
class MarkdownLink:
    """Holds one link target and the line it stands on."""

    target: str
    line: int


def _prose_lines(text: str) -> Iterator[tuple[int, str]]:
    """Yields each line outside a fenced code block, with its number."""
    fence: str | None = None
    for number, line in enumerate(text.splitlines(), start=1):
        match = K_FENCE.match(line)
        if fence is None and match is None:
            yield number, line
        elif fence is None:
            fence = match.group(1)
        elif match is not None and match.group(1) == fence:
            fence = None


def iter_links(text: str) -> Iterator[MarkdownLink]:
    """Yields every inline link and image target outside code, in reading order.

    A link whose text wraps is reported on the line that holds its target, and a linked
    image yields the image first, then the target it links to.
    """
    lines = [""] * (text.count("\n") + 1)
    for number, line in _prose_lines(text):
        lines[number - 1] = K_CODE_SPAN.sub("", line)
    prose = "\n".join(lines)
    for match in K_LINK.finditer(prose):
        target = match.group(1) if match.group(1) is not None else match.group(2)
        yield MarkdownLink(target, prose.count("\n", 0, match.start()) + 1)


def first_heading(text: str) -> str | None:
    """Returns the text of the first level-one heading, or None when there is none."""
    for _, line in _prose_lines(text):
        match = K_HEADING.match(line)
        if match and match.group(1):
            return match.group(1)
    return None


def local_path(target: str) -> str | None:
    """Returns the file part of a link target, or None when it names no local file."""
    if K_SCHEME.match(target) or target.startswith(("#", "//")):
        return None
    path = unquote(target.split("#", 1)[0].split("?", 1)[0])
    return path or None
