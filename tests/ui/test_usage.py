# test_usage.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The usage line prints its string literally."""

from sushicore.ui.usage import Usage
from tests.ui.capture import capture


def test_usage_keeps_square_brackets_literal():
    usage = Usage("hub [OPTIONS] COMMAND [ARGS]...")
    assert capture(usage) == "Usage: hub [OPTIONS] COMMAND [ARGS]...\n"
