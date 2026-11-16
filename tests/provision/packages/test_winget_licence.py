# test_winget_licence.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The licence link of a winget package is the one `winget show` prints, or none."""

from __future__ import annotations

import pytest

from sushicore.provision.licence_consent import Licence
from sushicore.provision.packages.winget_licence import (
    K_NO_LICENCE_LINK,
    parse_licence_url,
    read_licence,
)

pytestmark = pytest.mark.small

K_SHOWN = """Found Git [Git.Git]
Version: 2.47.1
Publisher: The Git Development Community
License: GNU General Public License, version 2
License Url: https://github.com/git-for-windows/git/blob/main/COPYING
Installer:
  Installer Type: inno
  Installer Url: https://example.invalid/git.exe
"""

K_SHOWN_WITHOUT_LICENCE_URL = """Found Tool [Some.Tool]
Version: 1.0
License: Proprietary
Installer:
  Installer Url: https://example.invalid/tool.exe
"""


def test_the_parser_returns_the_licence_url_field_of_a_winget_show_output():
    """Check that the License Url value is returned and Installer Url is not mistaken for it."""
    assert parse_licence_url(K_SHOWN) == "https://github.com/git-for-windows/git/blob/main/COPYING"


def test_the_parser_returns_none_when_the_output_has_no_licence_url():
    """Check that an output without the field, or with it empty, has no link."""
    assert (parse_licence_url(K_SHOWN_WITHOUT_LICENCE_URL), parse_licence_url("License Url:\n")) == (
        None, None)


def test_a_package_with_no_licence_url_is_shown_by_its_id_and_the_missing_link():
    """Check that the licence of a package winget publishes no link for says so."""
    held = read_licence("Some.Tool", lambda command: K_SHOWN_WITHOUT_LICENCE_URL)

    assert held == Licence("Some.Tool", K_NO_LICENCE_LINK)
    assert K_NO_LICENCE_LINK == "no licence link published"
