# test_adaptivecpp_compat.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the deprecated private helpers of the AdaptiveCpp installer."""

from __future__ import annotations

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.provision.default_console import DEFAULT_CONSOLE
from sushicore.provision.llvm_plans.windows import find_windows_llvm
from sushicore.provision.toolchains import adaptivecpp

pytestmark = pytest.mark.small


@pytest.fixture
def console():
    """Bind a recording console as the default one, and unbind it afterwards."""
    recording = RecordingConsole()
    DEFAULT_CONSOLE.bind(lambda: recording)
    yield recording
    DEFAULT_CONSOLE.bind(None)


def test_the_old_lookup_answers_what_the_current_one_does_and_warns(tmp_path):
    """Check that the deprecated lookup forwards, for an LLVM present and for none."""
    present = tmp_path / "lib" / "cmake" / "llvm"
    present.mkdir(parents=True)
    with pytest.warns(DeprecationWarning, match="find_windows_llvm"):
        found = adaptivecpp._find_windows_llvm([tmp_path])
    assert found == find_windows_llvm([tmp_path]) == (str(present), str(tmp_path))


def test_the_old_lookup_finds_nothing_in_an_empty_root(tmp_path):
    """Check that no LLVM under the given roots answers None."""
    with pytest.warns(DeprecationWarning):
        assert adaptivecpp._find_windows_llvm([tmp_path]) is None


def test_the_old_lookup_warns_at_its_caller(tmp_path):
    """Check that the warning points at this file."""
    with pytest.warns(DeprecationWarning) as caught:
        adaptivecpp._find_windows_llvm([tmp_path])
    assert caught[0].filename == __file__


@pytest.mark.parametrize("answer, expected", [("y", True), ("EVET", True), ("n", False), ("", False)])
def test_the_old_question_returns_whether_the_answer_means_yes(console, answer, expected):
    """Check that the yes words, in both languages, are the only yes."""
    with pytest.warns(DeprecationWarning, match="licence consent"):
        assert adaptivecpp._confirm_timeout("Install?", 5, reader=lambda: answer) is expected


def test_the_old_question_returns_its_default_when_nothing_answers(console):
    """Check that an end of input keeps the default."""
    def closed() -> str:
        raise EOFError
    with pytest.warns(DeprecationWarning):
        assert adaptivecpp._confirm_timeout("Install?", 5, True, reader=closed) is True


def test_the_old_question_in_machine_mode_asks_the_console_for_the_answer():
    """Check that a machine console is prompted with the markup removed."""
    machine = RecordingConsole(machine=True, answer="y")
    DEFAULT_CONSOLE.bind(lambda: machine)
    try:
        with pytest.warns(DeprecationWarning):
            assert adaptivecpp._confirm_timeout("[warn]Install?[/warn]", 5) is True
    finally:
        DEFAULT_CONSOLE.bind(None)
    assert machine.texts("prompt") == ["Install?"]
