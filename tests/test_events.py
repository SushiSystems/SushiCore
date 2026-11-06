# test_events.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The vocabulary every renderer speaks, and its one serialisation."""

import json

import pytest

from sushicore.events import event_line


pytestmark = pytest.mark.small


def test_event_line_is_one_json_object_with_the_kind_first():
    text = event_line("line", level="info", message="hello")
    assert "\n" not in text
    assert json.loads(text) == {"event": "line", "level": "info", "message": "hello"}
    assert text.startswith('{"event":"line"')


def test_event_line_keeps_non_ascii_characters_unescaped():
    assert "ş" in event_line("panel", title="ş", body="b")


def test_event_line_escapes_embedded_newlines():
    text = event_line("panel", title="t", body="a\nb")
    assert "\n" not in text
    assert json.loads(text)["body"] == "a\nb"


def test_unknown_kind_is_refused():
    with pytest.raises(ValueError):
        event_line("spinner")
