"""One event per call, on stdout alone."""

import io
import json

from sushicore.renderer import JsonRenderer


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


def test_level_is_derived_from_the_prefix_not_the_style():
    r, out, _ = _renderer()
    r.line("bold red", "[WARN]", "x")
    assert _events(out)[0]["level"] == "warn"


def test_unnamed_prefix_yields_info():
    r, out, _ = _renderer()
    r.line("bold red", "", "x")
    assert _events(out)[0]["level"] == "info"


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


def test_default_streams_are_forced_to_utf8(monkeypatch):
    """A redirected stdout on Windows defaults to cp1252; the contract says UTF-8."""
    import io
    import sys

    raw = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    monkeypatch.setattr(sys, "stdout", raw)
    JsonRenderer()
    assert sys.stdout.encoding.lower().replace("-", "") == "utf8"
