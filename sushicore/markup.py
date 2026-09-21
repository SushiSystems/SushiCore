"""Escapes the brackets in a string that do not name a style, so Rich markup keeps them as text.

A bracket is markup only when what it names is a style. ``escape_unknown_tags`` reads
no console and no global state; it is the only place that decides which brackets those are.
"""

from __future__ import annotations

import re
from collections.abc import Collection

from rich.errors import StyleSyntaxError
from rich.style import Style

K_BRACKET = re.compile(r"(\\*)\[([^\[\]]*)\]")
K_CLOSE = "/"


def escape_unknown_tags(text: str, known_styles: Collection[str]) -> str:
    """Return ``text`` with every bracket escaped that does not open or close a known style.

    A backslash is put before the ``[`` of each such bracket. A bracket that follows an odd
    number of backslashes is already escaped and is left as it is, as Rich reads it.

    Args:
        text: Markup that may hold brackets which are plain data.
        known_styles: Style names the caller's console knows besides Rich's own.

    Returns:
        The markup with every bracket that names no style turned into text.
    """
    open_names: list[str] = []

    def judge(match: re.Match[str]) -> str:
        """Return the matched bracket as it must appear in the escaped text."""
        backslashes, tag = match.groups()
        if len(backslashes) % 2:
            return match.group(0)
        if _is_tag(tag, known_styles, open_names):
            return match.group(0)
        return f"{backslashes}\\[{tag}]"

    return K_BRACKET.sub(judge, text)


def _is_tag(tag: str, known_styles: Collection[str], open_names: list[str]) -> bool:
    """Return whether the text between brackets opens or closes a style, tracking open names."""
    if tag.startswith(K_CLOSE):
        return _is_closing_tag(tag[len(K_CLOSE) :].strip(), known_styles, open_names)
    if not _names_style(tag.replace("=", " ", 1), known_styles):
        return False
    if tag.strip():
        open_names.append(Style.normalize(tag.partition("=")[0]))
    return True


def _is_closing_tag(name: str, known_styles: Collection[str], open_names: list[str]) -> bool:
    """Return whether ``name`` closes everything, a known style or a tag still open."""
    if not name:
        return True
    normal = Style.normalize(name)
    if normal in open_names:
        open_names.remove(normal)
        return True
    return _names_style(name, known_styles)


def _names_style(name: str, known_styles: Collection[str]) -> bool:
    """Return whether ``name`` is a known style name or a style Rich can parse."""
    if name in known_styles:
        return True
    try:
        Style.parse(name)
    except StyleSyntaxError:
        return False
    return True
