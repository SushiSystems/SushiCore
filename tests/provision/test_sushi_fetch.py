# test_sushi_fetch.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the step that fetches pinned Sushi libraries, in a layout holding only a consumer."""

from __future__ import annotations

import pytest

from sushicore.deps_fragment import read
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.pipeline import InstallContext, StepResult
from sushicore.provision.sushi_fetch import FetchSushiSourcesStep
from sushicore.provision.sushi_sources import SourceKind, resolve

from .sushi_fakes import K_OTHER, K_PINNED, FakeGit, write_fragment

pytestmark = pytest.mark.medium


@pytest.fixture
def consumer(tmp_path, provision_home, monkeypatch):
    """Return a scratch layout holding only a consumer whose fragment pins sushilog v1.0.0."""
    monkeypatch.delenv("SUSHILOG_DIR", raising=False)
    root = tmp_path / "layout" / "sushiruntime"
    write_fragment(root, {"sushilog": "v1.0.0"})
    return root


def _step(root, git):
    """Return the fetch step over *root*'s own pins."""
    pins = read(root / "cli" / "sushistack.deps.toml").pins
    return FetchSushiSourcesStep(root, pins, git)


def _ctx():
    """Return a context for a real run."""
    return InstallContext(cfg=ProvisionSettings(platform="linux"))


def test_a_missing_library_is_fetched_and_then_resolves_as_fetched(consumer, recording_console):
    """Check that the step clones the pinned tag and resolution then reports fetched."""
    git = FakeGit()

    assert _step(consumer, git).run(_ctx()) is StepResult.OK

    url, tag, destination = git.calls[0]
    assert (url, tag) == ("https://github.com/sushisystems/sushilog.git", "v1.0.0")
    found = resolve(consumer, "sushilog", "v1.0.0")
    assert found.kind is SourceKind.FETCHED and found.path == destination


def test_a_sibling_wins_and_the_step_is_skipped(consumer, recording_console):
    """Check that a sibling checkout is used and nothing is cloned."""
    (consumer.parent / "sushilog").mkdir()
    git = FakeGit()

    assert _step(consumer, git).run(_ctx()) is StepResult.SKIPPED

    assert git.calls == []
    assert resolve(consumer, "sushilog", "v1.0.0").kind is SourceKind.SIBLING


def test_the_directory_variable_wins(consumer, recording_console, monkeypatch, tmp_path):
    """Check that SUSHILOG_DIR is used before a sibling and nothing is cloned."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (consumer.parent / "sushilog").mkdir()
    monkeypatch.setenv("SUSHILOG_DIR", str(elsewhere))
    git = FakeGit()

    assert _step(consumer, git).run(_ctx()) is StepResult.SKIPPED

    found = resolve(consumer, "sushilog", "v1.0.0")
    assert found.kind is SourceKind.DIRECTORY and found.path == elsewhere.resolve()
    assert git.calls == []


def test_a_commit_off_the_pin_fails_and_leaves_no_folder(consumer, recording_console):
    """Check that a clone whose HEAD is not the pin is removed and the step fails."""
    git = FakeGit(commit=K_OTHER)

    assert _step(consumer, git).run(_ctx()) is StepResult.FAILED

    destination = git.calls[0][2]
    assert not destination.exists()
    assert resolve(consumer, "sushilog", "v1.0.0") is None
    errors = [args[0] for name, args in recording_console.calls if name == "error"]
    assert any(K_OTHER in e and K_PINNED in e for e in errors)


def test_a_failed_clone_names_the_url_the_tag_and_the_directory_variable(
        consumer, recording_console):
    """Check that an offline clone fails with one message saying how to hand over a checkout."""
    git = FakeGit(clones=False)

    assert _step(consumer, git).run(_ctx()) is StepResult.FAILED

    errors = [args[0] for name, args in recording_console.calls if name == "error"]
    assert len(errors) == 1
    message = errors[0]
    for part in ("sushilog", "v1.0.0", "https://github.com/sushisystems/sushilog.git",
                 "SUSHILOG_DIR"):
        assert part in message
    assert not git.calls[0][2].exists()


def test_a_fetched_copy_at_the_pin_is_not_cloned_again(consumer, recording_console):
    """Check that the step is skipped when the folder already holds the pinned commit."""
    git = FakeGit()
    _step(consumer, git).run(_ctx())

    assert _step(consumer, git).run(_ctx()) is StepResult.SKIPPED
    assert len(git.calls) == 1
