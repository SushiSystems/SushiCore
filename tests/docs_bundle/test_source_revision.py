# test_source_revision.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests how a bundle reads the commit it is built from."""

import subprocess

import pytest

from sushicore.docs_bundle.errors import ReleaseError
from sushicore.docs_bundle.source_revision import read_head_commit

pytestmark = pytest.mark.small


def _answer(returncode, stdout="", stderr=""):
    def run(*args, **kwargs):
        return subprocess.CompletedProcess(args, returncode, stdout, stderr)
    return run


def test_returns_the_head_commit(monkeypatch, tmp_path):
    monkeypatch.setattr(subprocess, "run", _answer(0, "abc123\n"))
    assert read_head_commit(tmp_path) == "abc123"


def test_a_folder_that_is_not_a_checkout_is_a_release_error(monkeypatch, tmp_path):
    monkeypatch.setattr(subprocess, "run", _answer(128, stderr="not a git repository\n"))
    with pytest.raises(ReleaseError, match="not a git checkout: not a git repository"):
        read_head_commit(tmp_path)


def test_a_missing_git_is_a_release_error(monkeypatch, tmp_path):
    def missing(*args, **kwargs):
        raise OSError("no git")
    monkeypatch.setattr(subprocess, "run", missing)
    with pytest.raises(ReleaseError, match="git could not be run"):
        read_head_commit(tmp_path)
