# settings_reads.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Finds the `K_` settings the shared tools read that a repository's `tools/settings.py` lacks."""

from __future__ import annotations

import ast
import re
from collections.abc import Iterable

from .errors import SharedToolsError

K_READ = re.compile(r"""getattr\(\s*settings\s*,\s*["'](K_\w+)["']|\bsettings\.(K_\w+)""")


def missing_settings(
    tools: Iterable[str], target_settings: str | None, core_settings: str | None,
) -> dict[str, str | None]:
    """Returns each setting the tools read and the target lacks, with SushiCore's value text.

    Args:
        tools: The texts of the copied Python tools.
        target_settings: The text of the repository's `tools/settings.py`, or None when it has none.
        core_settings: The text of SushiCore's `tools/settings.py` at the tag.

    Returns:
        The names in order, each with the source of its value in SushiCore, or None when SushiCore
        does not define it either.
    """
    read = {name for text in tools for pair in K_READ.findall(text) for name in pair if name}
    held = _definitions(target_settings or "")
    core = _definitions(core_settings or "")
    return {name: core.get(name) for name in sorted(read - held.keys())}


def _definitions(text: str) -> dict[str, str]:
    """Returns each module-level `K_` name of a settings text with the source of its value."""
    try:
        tree = ast.parse(text)
    except SyntaxError as error:
        raise SharedToolsError(f"a settings file is not Python: {error}") from error
    found = {}
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else [getattr(node, "target", None)]
        value = getattr(node, "value", None)
        for target in targets:
            if isinstance(target, ast.Name) and target.id.startswith("K_") and value is not None:
                found[target.id] = ast.get_source_segment(text, value) or ""
    return found
