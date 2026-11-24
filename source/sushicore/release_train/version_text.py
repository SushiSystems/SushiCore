# version_text.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Rewrites the version a file declares, as the dotted number or as one macro per part."""

from __future__ import annotations

import re

from .version import Version

K_PARTS = ("MAJOR", "MINOR", "PATCH")


def bump_text(text: str, old: Version, new: Version) -> str:
    """Return *text* with each mention of *old* written as *new*.

    A mention is the dotted number standing alone, or a line that names MAJOR, MINOR or PATCH of a
    version and ends its definition with that part of *old*.
    """
    dotted = re.compile(rf"(?<![0-9.]){re.escape(str(old))}(?![0-9])")
    text = dotted.sub(str(new), text)
    for name, before, after in zip(K_PARTS, (old.major, old.minor, old.patch), (new.major, new.minor, new.patch)):
        if before != after:
            part = re.compile(rf"(?m)^(.*VERSION_{name}\b\D*?){before}(\s*;?\s*)$")
            text = part.sub(rf"\g<1>{after}\g<2>", text)
    return text
