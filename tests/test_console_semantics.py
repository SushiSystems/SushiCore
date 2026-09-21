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


class _Spy:
    """A renderer that records every call."""

    def __init__(self):
        self.calls = []
        self.raw = None

    def line(self, *a): self.calls.append(("line", a))
    def command(self, *a): self.calls.append(("command", a))
    def header(self, *a): self.calls.append(("header", a))
    def panel(self, *a): self.calls.append(("panel", a))
    def table(self, *a): self.calls.append(("table", a))
    def progress(self, *a): self.calls.append(("progress", a))
    def result(self, *a): self.calls.append(("result", a))
    def prompt(self, *a):
        self.calls.append(("prompt", a))
        return "y"


def _console(spy):
    from sushicore.console import Console
    from sushicore.icons import IconSet
    return Console(spy, Theme(), IconSet())


def test_console_table_passes_the_theme_header_style():
    spy = _Spy()
    _console(spy).table(["A"], [["1"]], title="T")
    assert spy.calls == [("table", ("T", ["A"], [["1"]], Theme().header))]


class _GroupingSpy(_Spy):
    """A renderer whose table accepts the grouping column the newer Protocol declares."""

    def table(self, *a, group_by=None):
        self.calls.append(("table", a, group_by))


def test_console_leaves_group_by_out_of_the_call_when_it_is_not_asked_for():
    spy = _GroupingSpy()
    _console(spy).table(["A"], [["1"]], title="T")
    assert spy.calls == [("table", ("T", ["A"], [["1"]], Theme().header), None)]


def test_console_forwards_the_grouping_column_when_it_is_given():
    spy = _GroupingSpy()
    _console(spy).table(["A", "B"], [["1", "2"]], title="T", group_by="A")
    assert spy.calls == [("table", ("T", ["A", "B"], [["1", "2"]], Theme().header), "A")]


def test_a_renderer_that_never_heard_of_group_by_still_draws_an_ungrouped_table():
    spy = _Spy()
    _console(spy).table(["A"], [["1"]], title="T")
    assert spy.calls == [("table", ("T", ["A"], [["1"]], Theme().header))]


def test_console_progress_defaults_fraction_to_none():
    spy = _Spy()
    _console(spy).progress("step", 1, 3)
    assert spy.calls == [("progress", ("step", 1, 3, None))]


def test_console_result_defaults_payload_to_empty_dict():
    spy = _Spy()
    _console(spy).result(True)
    assert spy.calls == [("result", (True, {}))]


def test_console_prompt_numbers_prompts_per_instance():
    spy = _Spy()
    c = _console(spy)
    assert c.prompt("Go?", "n") == "y"
    c.prompt("Again?")
    assert [a[0] for k, a in spy.calls] == ["prompt-1", "prompt-2"]
