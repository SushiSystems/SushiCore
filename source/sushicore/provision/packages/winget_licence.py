# winget_licence.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Reads the licence link of a winget package from what ``winget show`` prints."""

from __future__ import annotations

import typing
from collections.abc import Callable

from ..licence_consent import Licence

#: What a package's licence is shown as when winget publishes no link for it.
K_NO_LICENCE_LINK = "no licence link published"

#: The field of ``winget show`` that holds the link, compared in lower case.
_LICENCE_FIELD = "license url"


@typing.runtime_checkable
class IWingetLicences(typing.Protocol):
    """Names the licence a winget package is installed under."""

    def licence_of(self, pkg: str) -> Licence:
        """Returns the licence of the winget package *pkg*."""


def parse_licence_url(shown: str) -> str | None:
    """Returns the ``License Url`` field of a ``winget show`` output, or None when it has none."""
    for line in shown.splitlines():
        field, separator, value = line.partition(":")
        if separator and field.strip().lower() == _LICENCE_FIELD and value.strip():
            return value.strip()
    return None


def read_licence(pkg: str, show: Callable[[list[str]], str]) -> Licence:
    """Returns the licence of *pkg*, its link read through *show*.

    Args:
        show: Runs a command and returns what it printed.
    """
    link = parse_licence_url(show(["winget", "show", "--id", pkg, "-e"]))
    return Licence(pkg, link or K_NO_LICENCE_LINK)
