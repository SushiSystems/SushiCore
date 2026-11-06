# test_main.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests `python -m sushicore.docs_bundle`, the entry of a repository with no CLI."""

from __future__ import annotations

import hashlib

import pytest

from sushicore.docs_bundle.__main__ import main


K_ARCHIVE = "docs-bundle-1.2.3.tar.gz"


@pytest.mark.medium
def test_main_writes_the_archive_of_the_root_at_out(checkout, tmp_path):
    """Writes the bundle of the repository `--root` names into the folder `--out` names."""
    out = tmp_path / "out"
    code = main(["--release", "1.2.3", "--root", str(checkout), "--out", str(out)])
    assert (code, (out / K_ARCHIVE).is_file()) == (0, True)


@pytest.mark.medium
def test_main_prints_the_archive_path_and_the_digest(checkout, tmp_path, capsys):
    """Prints the archive path, then the SHA-256 line."""
    out = tmp_path / "out"
    main(["--release", "1.2.3", "--root", str(checkout), "--out", str(out)])
    printed = capsys.readouterr().out.splitlines()
    assert printed[0] == str(out / K_ARCHIVE)
    assert printed[1] == f"sha256 {hashlib.sha256((out / K_ARCHIVE).read_bytes()).hexdigest()}"


@pytest.mark.small
def test_main_reports_a_failure_as_one_line_and_exit_one(capsys):
    """Prints one line on stderr and returns 1 when the release cannot be used."""
    assert main(["--release", "v1", "--root", "repo"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.count("\n") == 1
