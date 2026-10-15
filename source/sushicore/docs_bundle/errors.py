# errors.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The failures the documentation bundle producer reports as one line."""

from __future__ import annotations

from pathlib import Path

from ..errors import SushiCoreError


class DocsBundleError(SushiCoreError):
    """Reports a documentation tree that cannot be bundled."""


class PublishListError(DocsBundleError):
    """Reports a `docs/publish.toml` that is missing or cannot be used."""


class PageError(DocsBundleError):
    """Reports a published page that breaks a rule, with its file and line."""

    def __init__(self, path: Path, line: int, message: str) -> None:
        """Stores the location and puts it in front of the message."""
        super().__init__(f"{path}:{line}: {message}")
        self.path = path
        self.line = line


class ApiReferenceError(DocsBundleError):
    """Reports an API reference that could not be built or found."""


class ReleaseError(DocsBundleError):
    """Reports a release or a commit the bundle cannot be named after."""
