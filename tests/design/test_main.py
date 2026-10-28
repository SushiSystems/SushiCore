# test_main.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests `python -m sushicore.design`, the group for a repository with no CLI of its own."""

from __future__ import annotations

import pytest

from sushicore.design.__main__ import main

pytestmark = pytest.mark.medium


def test_main_opens_a_topic_and_checks_it(store, capsys):
    """The group runs on --root and returns each command's code."""
    root = str(store.root)
    assert main(["--root", root, "new", "ATMOSPHERE", "--modules", "modules/atmosphere", "--about", "The air."]) == 0
    assert main(["--root", root, "check"]) == 0
    assert capsys.readouterr().out.splitlines()[-1] == "clean"


def test_main_prints_a_design_error_as_one_line(store, capsys):
    """An unknown topic exits 1 with one line on standard error."""
    assert main(["--root", str(store.root), "show", "RAIN"]) == 1
    assert capsys.readouterr().err.strip() == "python -m sushicore.design: 'RAIN' is not a design topic"
