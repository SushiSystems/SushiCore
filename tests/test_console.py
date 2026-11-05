# test_console.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests how the console turns semantic calls into renderer calls."""

import io
from collections.abc import Callable
from dataclasses import dataclass

import pytest

from sushicore.console import Console
from sushicore.console_memory import RecordingConsole
from sushicore.icons import IconSet
from sushicore.renderer import PlainRenderer
from sushicore.theme import Theme



class _Renderer:
    """Records every call a console makes."""

    def __init__(self):
        self.calls = []
        self.raw = object()

    def __getattr__(self, name):
        def record(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            return "answer" if name == "prompt" else None
        return record


def _console():
    renderer = _Renderer()
    return Console(renderer, Theme(), IconSet(), dark_background=True), renderer


@pytest.mark.small
def test_each_level_uses_its_style_and_icon():
    console, renderer = _console()
    theme, icons = Theme(), IconSet()
    console.info("a")
    console.warn("b")
    console.error("c")
    console.success("d")
    assert renderer.calls == [
        ("line", (theme.info, icons.info, "a"), {}),
        ("line", (theme.warn, icons.warn, "b"), {}),
        ("line", (theme.error, icons.error, "c"), {}),
        ("line", (theme.success, icons.success, "d"), {}),
    ]


@pytest.mark.small
def test_a_flat_table_does_not_pass_group_by():
    console, renderer = _console()
    console.table(["A"], [["1"]])
    console.table(["A"], [["1"]], group_by="A")
    assert renderer.calls[0][2] == {}
    assert renderer.calls[1][2] == {"group_by": "A"}


@pytest.mark.small
def test_prompts_are_numbered_per_console():
    console, renderer = _console()
    assert console.prompt("Name?") == "answer"
    console.prompt("Again?", default="x")
    assert [call[1][0] for call in renderer.calls] == ["prompt-1", "prompt-2"]


@pytest.mark.small
def test_result_sends_an_empty_payload_by_default():
    console, renderer = _console()
    console.result(True)
    assert renderer.calls == [("result", (True, {}), {})]


@pytest.mark.small
def test_properties_expose_the_bound_parts():
    console, renderer = _console()
    assert console.console is renderer.raw
    assert console.accent == Theme().header
    assert console.dark_background
    assert not console.is_machine()



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


@pytest.mark.small
class TestRecordingConsoleKeepsTheConsoleContract(ConsoleContract):
    """The recording console, which prints nothing."""

    @pytest.fixture
    def world(self):
        console = RecordingConsole()
        return ConsoleWorld(console, lambda: "\n".join(call.text for call in console.calls))


@pytest.mark.small
class TestConsoleKeepsTheConsoleContract(ConsoleContract):
    """The real console, rendering into a string in place of a terminal."""

    @pytest.fixture
    def world(self):
        stream = io.StringIO()
        return ConsoleWorld(Console(PlainRenderer(stream), Theme(), IconSet()), stream.getvalue)
