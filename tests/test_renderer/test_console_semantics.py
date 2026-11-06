# test_console_semantics.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Each renderer speaks the four new calls in its own idiom."""

import io
import json

import pytest

from sushicore.console import Console
from sushicore.icons import IconSet
from sushicore.renderer import JsonRenderer, PlainRenderer, RichRenderer
from sushicore.theme import Theme


pytestmark = pytest.mark.small


def test_plain_table_prints_title_header_and_rows():
    out = io.StringIO()
    r = PlainRenderer(stream=out)
    r.table("Modules", ["Module", "State"], [["sushiruntime", "cloned"]], header_style="bold")
    text = out.getvalue()
    assert "Modules" in text and "Module" in text and "sushiruntime" in text and "cloned" in text


def test_plain_progress_prints_index_of_count():
    out = io.StringIO()
    PlainRenderer(stream=out).progress("install-deps", 2, 4, 0.5)
    assert "install-deps" in out.getvalue() and "2/4" in out.getvalue()


def test_plain_result_prints_nothing():
    out = io.StringIO()
    PlainRenderer(stream=out).result(True, {"x": 1})
    assert out.getvalue() == ""


def test_plain_prompt_returns_default_on_empty_line():
    renderer = PlainRenderer(stream=io.StringIO(), input_stream=io.StringIO("\n"))
    assert renderer.prompt("p1", "Continue?", "n") == "n"


def test_plain_prompt_asks_on_its_stream_and_reads_the_input_stream_given():
    out = io.StringIO()
    renderer = PlainRenderer(stream=out, input_stream=io.StringIO("yes\n"))
    assert renderer.prompt("p1", "Continue?", "n") == "yes"
    assert out.getvalue() == "Continue? [n]: "


def test_plain_prompt_returns_default_when_the_input_stream_is_spent():
    renderer = PlainRenderer(stream=io.StringIO(), input_stream=io.StringIO(""))
    assert renderer.prompt("p1", "Continue?", "n") == "n"


def _rich_renderer(out):
    return RichRenderer(Theme(), no_color=True, stream=out, enable_virtual_terminal=lambda: False)


def _json_console(input_text=""):
    out = io.StringIO()
    renderer = JsonRenderer(
        stream=out, error_stream=io.StringIO(), input_stream=io.StringIO(input_text),
    )
    return Console(renderer, Theme(), IconSet()), out


def _events(out):
    return [json.loads(line) for line in out.getvalue().splitlines()]


def test_rich_table_renders_rows():
    out = io.StringIO()
    _rich_renderer(out).table(
        "Modules", ["Module", "State"], [["sushiruntime", "cloned"]], header_style="bold",
    )
    assert "sushiruntime" in out.getvalue() and "cloned" in out.getvalue()


def test_console_table_reaches_the_renderer_with_its_title_columns_and_rows():
    console, out = _json_console()
    console.table(["A"], [["1"]], title="T")
    assert _events(out) == [{"event": "table", "title": "T", "columns": ["A"], "rows": [["1"]]}]


def test_console_table_with_a_grouping_column_reaches_a_json_renderer_as_the_flat_event():
    console, out = _json_console()
    console.table(["A", "B"], [["1", "2"]], title="T", group_by="A")
    assert _events(out) == [
        {"event": "table", "title": "T", "columns": ["A", "B"], "rows": [["1", "2"]]},
    ]


def test_console_table_without_group_by_keeps_the_group_column_in_a_rich_renderer():
    out = io.StringIO()
    Console(_rich_renderer(out), Theme(), IconSet()).table(
        ["Owner", "State"], [["shared", "cloned"]], title="T",
    )
    assert "Owner" in out.getvalue()


def test_console_table_forwards_the_grouping_column_to_a_rich_renderer():
    out = io.StringIO()
    Console(_rich_renderer(out), Theme(), IconSet()).table(
        ["Owner", "State"], [["shared", "cloned"]], title="T", group_by="Owner",
    )
    assert "Owner" not in out.getvalue() and "shared" in out.getvalue()


def test_console_progress_defaults_fraction_to_none():
    console, out = _json_console()
    console.progress("step", 1, 3)
    assert _events(out)[0]["fraction"] is None


def test_console_result_defaults_payload_to_empty_dict():
    console, out = _json_console()
    console.result(True)
    assert _events(out)[0]["payload"] == {}


def test_console_prompt_numbers_prompts_per_instance():
    console, out = _json_console("y\n\n")
    assert console.prompt("Go?", "n") == "y"
    console.prompt("Again?")
    assert [event["id"] for event in _events(out)] == ["prompt-1", "prompt-2"]


@pytest.mark.parametrize(
    ("make_renderer", "expected"),
    [
        (lambda: _rich_renderer(io.StringIO()), False),
        (lambda: JsonRenderer(stream=io.StringIO()), True),
    ],
    ids=["rich", "json"],
)
def test_console_is_machine_is_true_only_for_a_json_renderer(make_renderer, expected):
    console = Console(make_renderer(), Theme(), IconSet())
    assert console.is_machine() is expected
