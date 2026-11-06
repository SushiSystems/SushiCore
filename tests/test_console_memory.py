# test_console_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the recording console promises beyond the console contract in test_console.py."""

from __future__ import annotations

import pytest

from sushicore.console_memory import ConsoleCall, RecordingConsole

pytestmark = pytest.mark.small


def test_every_call_is_recorded_with_its_kind_and_text_in_call_order():
    console = RecordingConsole()
    console.info("one")
    console.warn("two")
    console.command("three")
    assert console.calls == [
        ConsoleCall("info", ("one",)), ConsoleCall("warn", ("two",)),
        ConsoleCall("command", ("three",))]


def test_texts_lists_only_the_calls_of_one_kind():
    console = RecordingConsole()
    console.info("a")
    console.warn("b")
    console.info("c")
    assert console.texts("info") == ["a", "c"]


def test_a_call_without_arguments_has_empty_text():
    assert ConsoleCall("status", ()).text == ""


def test_has_call_tells_whether_a_kind_was_recorded():
    console = RecordingConsole()
    console.error("x")
    assert (console.has_call("error"), console.has_call("warn")) == (True, False)


def test_a_rich_print_is_recorded_with_its_options_and_among_the_calls():
    console = RecordingConsole()
    console.console.print("line", markup=False)
    assert (console.console.printed[0].options, console.calls) == (
        {"markup": False}, [ConsoleCall("console.print", ("line",))])


def test_a_rich_status_is_recorded_and_runs_its_block():
    console = RecordingConsole()
    with console.console.status("working"):
        console.info("inside")
    assert console.calls == [
        ConsoleCall("console.status", ("working",)), ConsoleCall("info", ("inside",))]


def test_a_prompt_returns_its_default_when_no_answer_is_set():
    assert RecordingConsole().prompt("go?", "y") == "y"


def test_a_prompt_returns_the_fixed_answer_when_one_is_set():
    assert RecordingConsole(answer="n").prompt("go?", "y") == "n"


def test_the_machine_flag_is_the_one_the_console_was_built_with():
    assert RecordingConsole(machine=True).is_machine() is True
