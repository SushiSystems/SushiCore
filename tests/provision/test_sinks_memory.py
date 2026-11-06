# test_sinks_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the in-memory config sink promises beyond the sink contract."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.sinks_memory import InMemoryConfigSink

pytestmark = pytest.mark.small


def test_the_sink_does_not_follow_later_changes_to_the_values_it_was_given():
    values = {"ninja_exe": "n"}
    sink = InMemoryConfigSink()
    sink.write_paths("linux", values)
    values["ninja_exe"] = "changed"
    assert sink.paths == [("linux", {"ninja_exe": "n"})]


def test_the_sink_reports_the_backup_path_it_was_given():
    sink = InMemoryConfigSink(backup_path=Path("a.toml.bak"))
    assert sink.backup() == Path("a.toml.bak")


def test_the_sink_has_nothing_to_back_up_unless_given_a_backup_path():
    assert InMemoryConfigSink().backup() is None


def test_the_sink_lists_its_calls_in_the_order_they_were_made():
    sink = InMemoryConfigSink()
    sink.backup()
    sink.write_tool({"toolchain": "intel-llvm"})
    sink.clear()
    assert sink.calls == ["backup", "write_tool", "clear"]
