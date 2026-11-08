# test_github_release.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that every installer request names itself the same way."""

from __future__ import annotations

import urllib.request
from pathlib import Path

import pytest

import sushicore.provision as provision
from sushicore.provision.packages import direct_download, github_release


_ROOT = Path(provision.__file__).parent


class _Sent(Exception):
    """Stops a request once its headers are recorded."""


@pytest.fixture
def sent_agents(monkeypatch):
    """Record the User-Agent of every request instead of sending it."""
    agents = []

    def urlopen(request, timeout=None):
        """Check that urlopen."""
        agents.append(request.get_header("User-agent"))
        raise _Sent

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    return agents


@pytest.mark.small
@pytest.mark.parametrize("call", [
    lambda tmp: github_release.gh_latest_asset("o/r", "*"),
    lambda tmp: github_release.gh_latest_release_asset("o/r", "*"),
    lambda tmp: github_release.gh_tagged_asset("o/r", "v1", "*"),
    lambda tmp: direct_download.download("https://example.invalid/x", tmp / "x"),
])
def test_every_package_request_sends_the_sushicore_agent(
        call, sent_agents, tmp_path, recording_console):
    """Check that every package request sends the sushicore agent."""
    with pytest.raises(_Sent):
        call(tmp_path)
    assert sent_agents == ["sushicore-installer"]


@pytest.mark.medium
@pytest.mark.parametrize("module", [
    "packages/github_release.py", "packages/direct_download.py", "gpu/cuda_redist.py",
    "gpu/cuda_toolkit_installer.py", "gpu/rocm_tarball_index.py", "gpu/rocm_toolkit_installer.py",
    "gpu/windows_installer.py"])
def test_no_module_spells_its_own_agent(module):
    """Check that a module that sends a request takes its agent from system.USER_AGENT."""
    text = (_ROOT / module).read_text(encoding="utf-8")
    assert '-installer"' not in text
