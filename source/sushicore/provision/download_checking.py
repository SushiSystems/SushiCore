# download_checking.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The two calls a download site makes on the verifier of its run."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from sushicore.deps_fragment import Download


class DownloadChecking(Protocol):
    """Checks a download against its pin and returns the pin of an entry."""

    def verify(self, name: str, path: Path) -> None:
        """Check the file downloaded for the manifest entry *name*."""

    def pinned(self, name: str) -> Download:
        """Return the download the manifest entry *name* pins."""
