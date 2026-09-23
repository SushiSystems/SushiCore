# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the seams the shared steps gained."""

from __future__ import annotations

from sushicore.provision import probe, steps
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.pipeline import InstallContext, StepResult


class _Sink:
    def __init__(self):
        self.paths, self.tool = [], []

    def write_paths(self, platform, values):
        self.paths.append((platform, values))

    def write_tool(self, updates):
        self.tool.append(updates)


def test_configure_writes_through_the_sink(monkeypatch, recording_console):
    monkeypatch.setattr(probe, "resolve_local_config", lambda cfg, gpu=False: {"ninja_exe": "n"})
    sink = _Sink()
    ctx = InstallContext(cfg=ProvisionSettings(platform="linux"), active_toolchain="intel-llvm")
    assert steps.ConfigureStep(sink).run(ctx) is StepResult.OK
    assert sink.paths == [("linux", {"ninja_exe": "n"})]
    assert sink.tool == [{"toolchain": "intel-llvm"}]
