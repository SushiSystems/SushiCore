"""The vocabulary every renderer speaks, and its one serialisation."""

import json

import pytest

from sushicore.events import EVENT_KINDS, event_line


def test_every_kind_is_named():
    assert EVENT_KINDS == {"line", "command", "header", "panel",
                           "table", "progress", "result", "prompt"}


def test_event_line_is_one_json_object_with_the_kind_first():
    text = event_line("line", level="info", message="hello")
    assert "\n" not in text
    assert json.loads(text) == {"event": "line", "level": "info", "message": "hello"}
    assert text.startswith('{"event":"line"')


def test_event_line_keeps_non_ascii_and_embedded_newlines_escaped():
    text = event_line("panel", title="ş", body="a\nb")
    assert "\n" not in text
    assert json.loads(text)["body"] == "a\nb"
    assert "ş" in text


def test_unknown_kind_is_refused():
    with pytest.raises(ValueError):
        event_line("spinner")
