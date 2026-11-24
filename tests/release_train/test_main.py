# test_main.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the command line of the release train."""

import pytest

from sushicore.release_train.__main__ import K_EXIT_FAILURE, main
from sushicore.release_train.library_graph import K_PINS_FILE

pytestmark = pytest.mark.medium


def _library(workspace, name, pins=()):
    path = workspace / name / K_PINS_FILE
    path.parent.mkdir(parents=True)
    path.write_text("".join(f'[sushisystems.{below}]\nversion = "v1.0.0"\n' for below in pins), encoding="utf-8")


def test_plan_prints_the_train_in_order(tmp_path, capsys):
    _library(tmp_path, "log")
    _library(tmp_path, "runtime", ["log"])
    assert main(["plan", str(tmp_path), "log"]) == 0
    assert capsys.readouterr().out == "log\nruntime\n"


def test_an_unknown_library_fails_with_the_reason(tmp_path, capsys):
    _library(tmp_path, "log")
    assert main(["plan", str(tmp_path), "nothing"]) == K_EXIT_FAILURE
    assert "no library nothing" in capsys.readouterr().err
