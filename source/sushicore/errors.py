# errors.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
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


class ProjectRootNotFoundError(SushiCoreError):
    """Reports a working directory that lies outside any checkout or unpacked release."""


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


class CommitMismatchError(SushiCoreError):
    """Reports a git checkout or compiler whose commit is not the one its manifest entry pins."""

    def __init__(self, subject: str, expected: str, actual: str) -> None:
        """Store what was read and both commits, and name all three in the message."""
        found = actual or "no readable commit"
        super().__init__(
            f"{subject} is at {found}, and the dependency manifest pins {expected}. "
            f"The source was not built or run, and the step stopped.")
        self.subject = subject
        self.expected = expected
        self.actual = actual


class KeyFingerprintMismatchError(SushiCoreError):
    """Reports a downloaded signing key that does not carry the fingerprint its entry pins."""

    def __init__(self, path: Path, expected: str, found: list[str]) -> None:
        """Store the key file, the pinned fingerprint and the ones the file holds."""
        listed = ", ".join(found) if found else "no fingerprint"
        super().__init__(
            f"{path} holds {listed}, and the dependency manifest pins {expected}. "
            f"The key was not installed, and the repository was not configured.")
        self.path = path
        self.expected = expected
        self.found = found
