# changelog_section.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Closes the Unreleased section of a changelog into the section of a release."""

from __future__ import annotations

import re

from .version import Version

K_UNRELEASED = re.compile(r"(?ms)^## Unreleased\n\n(.*?)(?=^## |\Z)")


def close_changelog(text: str, version: Version, date: str, extra: tuple[str, ...] = ()) -> str:
    """Return the changelog *text* holding only the section of *version*.

    The section takes the entries of Unreleased and then each line of *extra*; older sections go,
    since the tag of each release holds them.
    """
    match = K_UNRELEASED.search(text)
    entries = [line for line in (match.group(1).strip().splitlines() if match else []) if line.strip()]
    entries.extend(f"- {date} — {line}" for line in extra)
    title = text.split("\n", 1)[0] if text.startswith("# ") else "# Changelog"
    return f"{title}\n\n## {version.tag} — {date}\n\n" + "".join(f"{line}\n" for line in entries)
