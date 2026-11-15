# test_main.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests `python -m sushicore.shared_tools`: the exit codes of `sync` and `check`."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.shared_tools.__main__ import main

from .conftest import K_SHARED, K_TAG

pytestmark = pytest.mark.medium


def _sync(target: Path, upstream: Path, *extra: str) -> int:
    """Runs the sync command and returns its exit code."""
    return main(["sync", str(target), "--tag", K_TAG, "--from", str(upstream), *extra])


def test_check_is_clean_after_a_sync(upstream, target):
    """A repository just synced passes the check."""
    _sync(target, upstream)
    assert main(["check", str(target)]) == 0


def test_a_one_byte_edit_makes_check_exit_1_and_name_the_file(upstream, target, capsys):
    """One extra byte in a locked file fails the check and the output names the file."""
    _sync(target, upstream)
    with (target / K_SHARED).open("ab") as handle:
        handle.write(b" ")
    capsys.readouterr()
    assert main(["check", str(target)]) == 1
    assert K_SHARED in capsys.readouterr().out


def test_check_names_a_missing_file(upstream, target, capsys):
    """A locked file that was deleted fails the check."""
    _sync(target, upstream)
    (target / ".github" / "SECURITY.md").unlink()
    capsys.readouterr()
    assert main(["check", str(target)]) == 1
    assert ".github/SECURITY.md" in capsys.readouterr().out


def test_check_exits_2_without_a_lock(target):
    """A repository with no lock cannot be checked."""
    assert main(["check", str(target)]) == 2


def test_an_unknown_tag_exits_2(upstream, target):
    """A tag the checkout lacks is a request that cannot be acted on."""
    assert main(["sync", str(target), "--tag", "v9.9.9", "--from", str(upstream)]) == 2


def test_a_local_edit_exits_1_and_force_brings_the_file_back(upstream, target, capsys):
    """A refused edit exits 1 naming the file on standard error; --force overwrites it."""
    _sync(target, upstream)
    edited = target / K_SHARED
    edited.write_text(edited.read_text(encoding="utf-8") + "# mine\n", encoding="utf-8")
    capsys.readouterr()
    assert _sync(target, upstream) == 1
    assert K_SHARED in capsys.readouterr().err
    assert _sync(target, upstream, "--force") == 0
    assert main(["check", str(target)]) == 0
