# pin_text.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Points the pin of one Sushi library at a new tag, in the pins file and in CI workflows."""

from __future__ import annotations

import re

from .version import Version


def pin_in_deps(text: str, library: str, version: Version, commit: str) -> str:
    """Return the pins file *text* with the table of *library* naming *version* and *commit*."""
    table = re.compile(rf"(?ms)(^\[sushisystems\.{re.escape(library)}\]\n)(.*?)(?=^\[|\Z)")

    def rewrite(match: re.Match[str]) -> str:
        body = re.sub(r'(?m)^(version\s*=\s*)"[^"]*"', rf'\g<1>"{version.tag}"', match.group(2))
        body = re.sub(r'(?m)^(commit\s*=\s*)"[^"]*"', rf'\g<1>"{commit}"', body)
        return match.group(1) + body

    return table.sub(rewrite, text, count=1)


def pin_in_workflow(text: str, library: str, version: Version) -> str:
    """Return the workflow *text* with its `<LIBRARY>_REF: v...` variable naming *version*."""
    return re.sub(rf"(?m)^(\s*{re.escape(library.upper())}_REF:\s*)v[0-9][0-9.]*", rf"\g<1>{version.tag}", text)
