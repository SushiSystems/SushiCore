# test_json_renderer.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""One event per call, on stdout alone."""

import io
import json
import logging

import pytest

from sushicore.renderer import JsonRenderer, force_utf8


pytestmark = pytest.mark.small


def _renderer(stdin_text=""):
    out, err = io.StringIO(), io.StringIO()
    r = JsonRenderer(stream=out, error_stream=err, input_stream=io.StringIO(stdin_text))
    return r, out, err


def _events(out):
    return [json.loads(l) for l in out.getvalue().splitlines()]


def test_line_event_carries_level_and_message():
    r, out, _ = _renderer()
    r.line("bold blue", "[INFO]", "hello")
    assert _events(out) == [{"event": "line", "level": "info", "message": "hello"}]


@pytest.mark.parametrize(
    ("prefix", "level"),
    [("[WARN]", "warn"), ("", "info")],
    ids=["named-prefix", "no-prefix"],
)
def test_level_comes_from_the_prefix_not_the_style_and_is_info_without_one(prefix, level):
    r, out, _ = _renderer()
    r.line("bold red", prefix, "x")
    assert _events(out)[0]["level"] == level


def test_each_call_is_exactly_one_line():
    r, out, _ = _renderer()
    r.header("H", "bold"); r.command("c", "i", "[INFO]", "cmake"); r.panel("t", "a\nb", "red")
    r.table("T", ["A"], [["1"]], "bold"); r.progress("s", 1, 2, None); r.result(True, {})
    assert len(out.getvalue().splitlines()) == 6
    assert [e["event"] for e in _events(out)] == ["header", "command", "panel", "table", "progress", "result"]


def test_events_carry_the_contract_keys():
    r, out, _ = _renderer()
    r.header("H", "bold"); r.command("c", "i", "[INFO]", "cmake"); r.panel("t", "b", "red")
    r.table("T", ["A"], [["1"]], "bold"); r.progress("s", 1, 2, 0.5); r.result(True, {"k": 1})
    assert _events(out) == [
        {"event": "header", "title": "H"},
        {"event": "command", "command": "cmake"},
        {"event": "panel", "title": "t", "body": "b"},
        {"event": "table", "title": "T", "columns": ["A"], "rows": [["1"]]},
        {"event": "progress", "label": "s", "index": 1, "count": 2, "fraction": 0.5},
        {"event": "result", "ok": True, "payload": {"k": 1}},
    ]


def test_the_table_event_is_byte_identical_with_and_without_a_grouping_column():
    flat, flat_out, _ = _renderer()
    grouped, grouped_out, _ = _renderer()
    flat.table("T", ["Owner", "State"], [["shared", "cloned"]], "bold")
    grouped.table("T", ["Owner", "State"], [["shared", "cloned"]], "bold", group_by="Owner")
    assert grouped_out.getvalue() == flat_out.getvalue()


def test_raw_writes_to_the_error_stream_not_stdout():
    r, out, err = _renderer()
    r.raw.print("stray")
    assert out.getvalue() == "" and "stray" in err.getvalue()


def test_prompt_emits_the_event_and_reads_one_line():
    r, out, _ = _renderer("yes\n")
    assert r.prompt("prompt-1", "Go?", "n") == "yes"
    assert _events(out) == [{"event": "prompt", "id": "prompt-1", "message": "Go?", "default": "n"}]


def test_prompt_returns_default_on_eof():
    r, _, _ = _renderer("")
    assert r.prompt("prompt-1", "Go?", "n") == "n"


def test_force_utf8_switches_a_cp1252_stream_to_utf8():
    """A redirected stdout on Windows defaults to cp1252; the contract says UTF-8."""
    stream = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    force_utf8((stream,))
    assert stream.encoding.lower().replace("-", "") == "utf8"


class _StubbornStream:
    """Stands in for a stream whose encoding cannot be changed."""

    def reconfigure(self, **_kwargs) -> None:
        """Refuse the new encoding the way a detached stream does."""
        raise ValueError("underlying buffer has been detached")


class _ListHandler(logging.Handler):
    """Collects the records a logger emits, in memory."""

    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        """Keep the record."""
        self.records.append(record)


def test_a_stream_that_refuses_utf8_is_recorded_once_per_stream():
    """Check that a stream left on its old encoding is logged once per stream."""
    sink = logging.Logger("test.force_utf8")
    handler = _ListHandler()
    sink.addHandler(handler)
    force_utf8((_StubbornStream(), _StubbornStream()), log=sink)
    assert [r.levelname for r in handler.records] == ["WARNING", "WARNING"]
    assert "detached" in handler.records[0].getMessage()


@pytest.mark.parametrize(
    ("title", "column", "cell", "expected"),
    [
        ("[bold]Doctor[/bold]", "[dim]Result[/dim]", "[success]ok[/success]",
         ("Doctor", "Result", "ok")),
        ("T", "Detail", "found [1, 2] in path", ("T", "Detail", "found [1, 2] in path")),
    ],
    ids=["markup-removed", "bracket-that-is-no-markup-kept"],
)
def test_the_table_event_carries_plain_text_and_keeps_brackets_that_are_no_markup(
    title, column, cell, expected,
):
    """A cell the human table colours with markup reaches a program as the bare word."""
    r, out, _ = _renderer()
    r.table(title, [column], [[cell]], "bold")
    event = _events(out)[0]
    assert (event["title"], event["columns"][0], event["rows"][0][0]) == expected
