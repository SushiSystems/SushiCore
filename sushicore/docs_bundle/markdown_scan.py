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
K_LINK = re.compile(r"\[[^\]]*\]\(\s*<?([^)\s>]+)>?[^)]*\)")
K_HEADING = re.compile(r"^#\s+(.*?)\s*#*\s*$")
K_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


@dataclass(frozen=True, slots=True)
class MarkdownLink:
    """Holds one link target and the line it stands on."""

    target: str
    line: int


def _prose_lines(text: str) -> Iterator[tuple[int, str]]:
    """Yields each line outside a fenced code block, with its number."""
    fenced = False
    for number, line in enumerate(text.splitlines(), start=1):
        if K_FENCE.match(line):
            fenced = not fenced
            continue
        if not fenced:
            yield number, line


def iter_links(text: str) -> Iterator[MarkdownLink]:
    """Yields every inline link and image target outside code, in reading order."""
    for number, line in _prose_lines(text):
        for match in K_LINK.finditer(K_CODE_SPAN.sub("", line)):
            yield MarkdownLink(match.group(1), number)


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
