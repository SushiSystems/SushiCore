# test_main.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the command line of the shared tools."""

import pytest

from sushicore.tools import __main__ as tools_main

pytestmark = pytest.mark.small


def test_an_unknown_or_missing_command_prints_the_usage(capsys):
    assert tools_main.main([]) == tools_main.K_EXIT_USAGE
    assert tools_main.main(["build"]) == tools_main.K_EXIT_USAGE
    assert capsys.readouterr().err.count("usage:") == 2


def test_each_command_hands_its_arguments_to_its_runner(monkeypatch):
    calls = []
    monkeypatch.setattr("sushicore.tools.check_all.main", lambda argv: calls.append(("check", argv)) or 0)
    monkeypatch.setattr("sushicore.tools.hooks.install_hooks.main", lambda argv: calls.append(("hooks", argv)) or 0)
    assert tools_main.main(["check", ".", "--skip-history"]) == 0
    assert tools_main.main(["install-hooks", "."]) == 0
    assert calls == [("check", [".", "--skip-history"]), ("hooks", ["."])]
