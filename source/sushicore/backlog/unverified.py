# unverified.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Judges which backlog IDs are unverified, from the messages of the commits after the stamp.

The rule is in `docs/design/BACKLOG/README.md`.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

K_TRAILER = re.compile(r"^Backlog:[ \t]*(.*?)[ \t]*$", re.MULTILINE)
K_ID = re.compile(r"\b[A-Z]+-\d+\b")


def unverified_ids(messages: Iterable[str]) -> frozenset[str]:
    """Returns the IDs that the `Backlog:` lines of the given commit messages name.

    Args:
        messages: The messages of the commits after the verified commit.
    """
    return frozenset(
        ident
        for message in messages
        for line in K_TRAILER.findall(message)
        for ident in K_ID.findall(line)
    )
