"""Each renderer speaks the four new calls in its own idiom."""

import io

from sushicore.renderer import PlainRenderer, RichRenderer
from sushicore.theme import Theme


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


def test_plain_prompt_returns_default_on_empty_line(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda *_a, **_k: "")
    assert PlainRenderer(stream=io.StringIO()).prompt("p1", "Continue?", "n") == "n"


def test_plain_prompt_returns_default_on_eof(monkeypatch):
    def _eof(*_a, **_k):
        raise EOFError
    monkeypatch.setattr("builtins.input", _eof)
    assert PlainRenderer(stream=io.StringIO()).prompt("p1", "Continue?", "n") == "n"


def test_rich_table_renders_rows(capsys):
    r = RichRenderer(Theme(), no_color=True)
    r.table("Modules", ["Module", "State"], [["sushiruntime", "cloned"]], header_style="bold")
    captured = capsys.readouterr().out
    assert "sushiruntime" in captured and "cloned" in captured
