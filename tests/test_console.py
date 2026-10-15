# test_console.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests how the console turns semantic calls into renderer calls."""

import pytest

from sushicore.console import Console
from sushicore.icons import IconSet
from sushicore.theme import Theme

pytestmark = pytest.mark.small


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


def test_a_flat_table_does_not_pass_group_by():
    console, renderer = _console()
    console.table(["A"], [["1"]])
    console.table(["A"], [["1"]], group_by="A")
    assert renderer.calls[0][2] == {}
    assert renderer.calls[1][2] == {"group_by": "A"}


def test_prompts_are_numbered_per_console():
    console, renderer = _console()
    assert console.prompt("Name?") == "answer"
    console.prompt("Again?", default="x")
    assert [call[1][0] for call in renderer.calls] == ["prompt-1", "prompt-2"]


def test_result_sends_an_empty_payload_by_default():
    console, renderer = _console()
    console.result(True)
    assert renderer.calls == [("result", (True, {}), {})]


def test_properties_expose_the_bound_parts():
    console, renderer = _console()
    assert console.console is renderer.raw
    assert console.accent == Theme().header
    assert console.dark_background
    assert not console.is_machine()
