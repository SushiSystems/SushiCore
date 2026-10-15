# errors.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The failures sushicore reports to a CLI's entry point as one line.

:func:`sushicore.entry.run` catches :class:`SushiCoreError` and nothing wider, so an error
that derives from it reaches the user as a message and anything else stays a traceback.
"""

from __future__ import annotations

from pathlib import Path


class SushiCoreError(Exception):
    """Reports a failure the user can act on, as opposed to a defect in the CLI."""


class ConfigError(SushiCoreError, ValueError):
    """Reports a configuration file or value that cannot be used."""


class DigestMismatchError(SushiCoreError):
    """Reports a downloaded file whose SHA-256 is not the one its manifest entry pins."""

    def __init__(self, path: Path, expected: str, actual: str) -> None:
        """Store the file and both digests, and name all three in the message."""
        super().__init__(
            f"{path} has SHA-256 {actual}, and the dependency manifest pins {expected}. "
            f"The file was not opened or run, and the install stopped.")
        self.path = path
        self.expected = expected
        self.actual = actual
