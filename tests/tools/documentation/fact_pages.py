# fact_pages.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Holds the pages of facts the facts tests share, and builds the manual of made-up pages."""

from __future__ import annotations

from pathlib import Path

from sushicore.tools.checking.source_file import SourceFile
from sushicore.tools.documentation import check_docs_facts

K_HOME = (
    "# Home\n\n<!-- fact:begin shipping -->\n"
    "A topic ships when its last phase is built.\n<!-- fact:end shipping -->\n"
)
K_QUOTE = (
    "# Page\n\n<!-- quote:begin shipping -->\n"
    "A topic ships when its last phase is built.\n<!-- quote:end shipping -->\n"
)
K_FOLLOW = "# Page\n\n<!-- follows: shipping -->\nThe topic is done after its last phase.\n"
K_ROOT = Path("repo")


def manual_of(pages: dict[str, str]) -> check_docs_facts.Manual:
    """Returns the manual of a made-up repository holding the given pages, built from values."""
    return check_docs_facts.build_manual(
        K_ROOT, [SourceFile(K_ROOT / name, text) for name, text in pages.items()],
    )
