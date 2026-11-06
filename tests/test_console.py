# test_console.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests how the console turns semantic calls into renderer calls."""

import io
import json
from collections.abc import Callable
from dataclasses import dataclass

import pytest

from sushicore.console import Console
from sushicore.console_memory import RecordingConsole
from sushicore.icons import IconSet
from sushicore.renderer import JsonRenderer, PlainRenderer
from sushicore.theme import Theme

pytestmark = pytest.mark.small

K_ICONS = IconSet(info="i", success="s", warn="w", error="e")


def _plain_console(theme: Theme | None = None, *,
                   dark_background: bool = False) -> tuple[Console, io.StringIO]:
    """Return a console over the plain renderer and the stream it writes to."""
    stream = io.StringIO()
    return Console(PlainRenderer(stream), theme or Theme(), K_ICONS, dark_background), stream


def _json_console(answers: str = "") -> tuple[Console, io.StringIO]:
    """Return a console over the JSON renderer, reading *answers*, and the stream of its events."""
    events = io.StringIO()
    renderer = JsonRenderer(events, io.StringIO(), io.StringIO(answers))
    return Console(renderer, Theme(), K_ICONS), events


def _events(stream: io.StringIO) -> list[dict]:
    """Return the JSON events written to *stream*, in order."""
    return [json.loads(line) for line in stream.getvalue().splitlines()]


@pytest.mark.parametrize("method, line", [
    ("info", "i a\n"),
    ("success", "s a\n"),
    ("warn", "w a\n"),
    ("error", "e a\n"),
])
def test_each_level_prints_its_own_icon_before_the_message(method, line):
    console, stream = _plain_console()
    getattr(console, method)("a")
    assert stream.getvalue() == line


def test_a_flat_table_prints_its_title_header_and_rows():
    console, stream = _plain_console()
    console.table(["A", "B"], [["1", "2"]], "Things")
    assert stream.getvalue() == "Things\nA  B\n1  2\n"


def test_a_table_grouped_by_a_column_prints_its_rows():
    console, stream = _plain_console()
    console.table(["A", "B"], [["1", "2"]], "Things", group_by="A")
    assert stream.getvalue() == "Things\nA  B\n1  2\n"


def test_prompts_are_numbered_from_one_in_the_order_they_are_asked():
    console, events = _json_console("Ann\nBo\n")
    console.prompt("Name?")
    console.prompt("Again?", default="x")
    assert [event["id"] for event in _events(events)] == ["prompt-1", "prompt-2"]


def test_a_prompt_returns_the_answer_the_renderer_read():
    console, _ = _json_console("Ann\n")
    assert console.prompt("Name?") == "Ann"


def test_result_sends_an_empty_payload_by_default():
    console, events = _json_console()
    console.result(True)
    assert _events(events) == [{"event": "result", "ok": True, "payload": {}}]


def test_the_rich_console_property_prints_to_the_stream_of_the_renderer():
    console, stream = _plain_console()
    console.console.print("shown")
    assert stream.getvalue() == "shown\n"


def test_accent_is_the_header_style_of_the_theme():
    console, _ = _plain_console(Theme(header="underline"))
    assert console.accent == "underline"


def test_dark_background_reports_what_the_console_was_built_with():
    console, _ = _plain_console(dark_background=True)
    assert console.dark_background is True


def test_a_console_over_the_json_renderer_is_in_machine_mode():
    console, _ = _json_console()
    assert console.is_machine() is True


@dataclass
class ConsoleWorld:
    """A console under test and a reader of everything it showed, in call order."""

    console: Console | RecordingConsole
    shown: Callable[[], str]


class ConsoleContract:
    """The promises every console keeps; a subclass supplies the world."""

    @pytest.mark.parametrize("method", ["info", "success", "warn", "error", "command", "header"])
    def test_a_message_is_shown(self, world, method):
        getattr(world.console, method)("the message")
        assert "the message" in world.shown()

    def test_messages_are_shown_in_the_order_of_the_calls(self, world):
        world.console.info("first")
        world.console.warn("second")
        world.console.error("third")
        shown = world.shown()
        assert shown.index("first") < shown.index("second") < shown.index("third")

    def test_a_console_is_not_in_machine_mode_unless_built_to_be(self, world):
        assert world.console.is_machine() is False


class TestRecordingConsoleKeepsTheConsoleContract(ConsoleContract):
    """The recording console, which prints nothing."""

    @pytest.fixture
    def world(self):
        console = RecordingConsole()
        return ConsoleWorld(console, lambda: "\n".join(call.text for call in console.calls))


class TestConsoleKeepsTheConsoleContract(ConsoleContract):
    """The real console, rendering into a string in place of a terminal."""

    @pytest.fixture
    def world(self):
        stream = io.StringIO()
        return ConsoleWorld(Console(PlainRenderer(stream), Theme(), IconSet()), stream.getvalue)
