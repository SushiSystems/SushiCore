# pypi_index.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Waits for a version of a package to appear on PyPI."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import final

from .version import Version

K_URL = "https://pypi.org/pypi/{package}/json"
K_POLL_SECONDS = 30.0
K_MAX_POLLS = 60


def _fetch(package: str) -> dict[str, object]:
    """Return the JSON PyPI holds for *package*, or an empty mapping when it cannot be read."""
    try:
        with urllib.request.urlopen(K_URL.format(package=package), timeout=30) as response:
            return json.load(response)
    except (urllib.error.URLError, OSError, ValueError):
        return {}


@final
class PyPiIndex:
    """Polls PyPI until a release of a package is listed."""

    def __init__(self, sleep: Callable[[float], None], fetch: Callable[[str], dict[str, object]] = _fetch) -> None:
        self._sleep = sleep
        self._fetch = fetch

    def wait_for(self, package: str, version: Version) -> bool:
        for _ in range(K_MAX_POLLS):
            releases = self._fetch(package).get("releases", {})
            if isinstance(releases, dict) and str(version) in releases:
                return True
            self._sleep(K_POLL_SECONDS)
        return False
