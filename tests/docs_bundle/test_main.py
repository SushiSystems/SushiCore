# test_main.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests `python -m sushicore.docs_bundle`, the entry of a repository with no CLI."""

from __future__ import annotations

from sushicore.docs_bundle.__main__ import main


def test_main_writes_the_archive_and_prints_it(checkout, tmp_path, capsys):
    """Writes the bundle of the repository `--root` names and prints path and digest."""
    out = tmp_path / "out"
    code = main(["--release", "1.2.3", "--root", str(checkout), "--out", str(out)])
    assert code == 0
    printed = capsys.readouterr().out.splitlines()
    assert printed[0] == str(out / "docs-bundle-1.2.3.tar.gz")
    assert printed[1].startswith("sha256 ")


def test_main_reports_a_failure_as_one_line_and_exit_one(repository, capsys):
    """Prints one line on stderr and returns 1 when the release cannot be used."""
    assert main(["--release", "v1", "--root", str(repository)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.count("\n") == 1
