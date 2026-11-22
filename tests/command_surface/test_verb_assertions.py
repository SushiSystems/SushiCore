# test_verb_assertions.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that a CLI's test can assert its app registers each canonical verb that applies to it."""

import pytest
import typer

from sushicore.command_surface import K_CANONICAL_VERBS, UnknownVerbError, assert_registers_verbs

pytestmark = pytest.mark.small


def _app(verbs) -> typer.Typer:
    app = typer.Typer()

    @app.callback()
    def root() -> None:
        """Root."""

    for verb in verbs:
        app.command(verb)(lambda: None)
    return app


def test_assert_registers_verbs_passes_an_app_with_every_canonical_verb():
    assert_registers_verbs(_app(K_CANONICAL_VERBS))


def test_assert_registers_verbs_names_each_verb_the_app_lacks():
    app = _app([verb for verb in K_CANONICAL_VERBS if verb not in ("bench", "where")])
    with pytest.raises(AssertionError, match="bench, where"):
        assert_registers_verbs(app)


def test_assert_registers_verbs_passes_an_app_that_lacks_only_excluded_verbs():
    app = _app([verb for verb in K_CANONICAL_VERBS if verb != "bench"])
    assert_registers_verbs(app, excluded=["bench"])


def test_assert_registers_verbs_refuses_to_exclude_a_verb_that_is_not_canonical():
    with pytest.raises(UnknownVerbError, match="deploy"):
        assert_registers_verbs(_app(K_CANONICAL_VERBS), excluded=["deploy"])
