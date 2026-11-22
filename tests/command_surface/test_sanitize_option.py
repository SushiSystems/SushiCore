# test_sanitize_option.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that ``--sanitize`` takes the sanitizers sushi_sanitizers builds as one set per tree."""

import pytest
import typer
from typer.testing import CliRunner

from sushicore.command_surface import (SanitizerConflictError, UnknownSanitizerError, parse_sanitizers,
                                       sanitize_option)

pytestmark = pytest.mark.small


@pytest.mark.parametrize(("text", "kinds"), [
    (None, ()),
    ("", ()),
    ("thread", ("thread",)),
    ("address,undefined", ("address", "undefined")),
    ("undefined, address,undefined", ("address", "undefined")),
])
def test_parse_sanitizers_returns_each_kind_once_in_the_canonical_order(text, kinds):
    assert parse_sanitizers(text) == kinds


def test_parse_sanitizers_refuses_a_kind_sushi_sanitizers_does_not_build():
    with pytest.raises(UnknownSanitizerError, match="memory"):
        parse_sanitizers("address,memory")


def test_parse_sanitizers_refuses_a_kind_the_command_does_not_allow():
    with pytest.raises(UnknownSanitizerError, match="thread"):
        parse_sanitizers("thread", allowed=("address", "undefined"))


def test_parse_sanitizers_refuses_address_with_thread_in_one_build():
    with pytest.raises(SanitizerConflictError, match="address and thread"):
        parse_sanitizers("thread,address")


def test_sanitize_option_refuses_an_allowed_kind_sushi_sanitizers_does_not_build():
    with pytest.raises(UnknownSanitizerError, match="leak"):
        sanitize_option(("address", "leak"))


def _app(seen: list) -> typer.Typer:
    parameter = sanitize_option()
    app = typer.Typer()

    @app.command()
    def build(sanitize: parameter.annotation = parameter.default) -> None:
        """Build."""
        seen.append(sanitize)

    return app


def test_sanitize_option_turns_a_refused_value_into_a_usage_error():
    seen = []
    result = CliRunner().invoke(_app(seen), ["--sanitize", "address,thread"])
    assert (result.exit_code, seen) == (2, [])


def test_sanitize_option_passes_an_accepted_value_through_unchanged():
    seen = []
    CliRunner().invoke(_app(seen), ["--sanitize", "undefined,address"])
    assert seen == ["undefined,address"]
