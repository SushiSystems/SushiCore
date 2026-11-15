# errors.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The failures `sushicore.shared_tools` reports as one line."""

from __future__ import annotations

from ..errors import SushiCoreError


class SharedToolsError(SushiCoreError):
    """Reports a sync or a check that cannot go on."""


class CheckoutNotFoundError(SharedToolsError):
    """Reports that no SushiCore checkout was found to read the shared tools from."""


class TagNotFoundError(SharedToolsError):
    """Reports a release tag the SushiCore checkout does not hold."""


class NoLockError(SharedToolsError):
    """Reports a repository that holds no `tools/shared_tools.lock`."""


class LocalEditsError(SharedToolsError):
    """Reports shared files that hold text no SushiCore version ever held."""

    def __init__(self, files: list[str]) -> None:
        """Stores the files and names them in the message."""
        super().__init__(", ".join(files))
        self.files = files
