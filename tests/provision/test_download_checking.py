# test_download_checking.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that a download site accepts any object with the two calls of ``DownloadChecking``."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.deps_fragment import Download
from sushicore.provision.download_verifier import pinned_download, verify_download

pytestmark = pytest.mark.small

K_PIN = Download("git", "v2", "https://example.invalid/g.exe", "0" * 64)


class _RecordingChecker:
    """Records the entries it was asked to verify and pins one download."""

    def __init__(self) -> None:
        self.verified: list[str] = []

    def verify(self, name: str, path: Path) -> None:
        self.verified.append(name)

    def pinned(self, name: str) -> Download:
        return K_PIN


def test_verify_download_calls_verify_on_a_checker_it_is_passed():
    checker = _RecordingChecker()
    verify_download("git", Path("unused"), verifier=checker)
    assert checker.verified == ["git"]


def test_pinned_download_returns_the_pin_of_a_checker_it_is_passed():
    assert pinned_download("git", verifier=_RecordingChecker()) == K_PIN
