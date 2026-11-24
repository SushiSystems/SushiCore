# test_changelog_section.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for closing the Unreleased section of a changelog."""

import pytest

from sushicore.release_train.changelog_section import close_changelog
from sushicore.release_train.version import Version

pytestmark = pytest.mark.small


def test_unreleased_becomes_the_release_and_older_sections_go():
    text = "# Changelog\n\n## Unreleased\n\n- a\n- b\n\n## v0.5.1 — 2026-11-22\n\n- old\n"
    assert close_changelog(text, Version(0, 5, 2), "2026-11-24", ("deps: c",)) == (
        "# Changelog\n\n## v0.5.2 — 2026-11-24\n\n- a\n- b\n- 2026-11-24 — deps: c\n")


def test_a_changelog_without_unreleased_holds_the_extra_lines_alone():
    text = "# Changelog\n\n## v0.5.1 — 2026-11-22\n\n- old\n"
    assert close_changelog(text, Version(0, 5, 2), "2026-11-24", ("deps: c",)) == (
        "# Changelog\n\n## v0.5.2 — 2026-11-24\n\n- 2026-11-24 — deps: c\n")
