# test_posix.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the POSIX host."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.host import PosixHost


@pytest.mark.small
def test_the_posix_host_states_its_conventions():
    """Check the compiler name, prefix search, Visual Studio and registry answers."""
    host = PosixHost()

    assert host.nvcc_name == "nvcc"
    assert host.cuda_platform_key in ("linux-x86_64", "linux-sbsa")
    assert (host.searches_system_prefixes, host.hosts_visual_studio,
            host.keeps_environment_in_registry) == (True, False, False)


@pytest.mark.small
def test_the_posix_host_keeps_a_path_unchanged_and_reads_no_registry():
    """Check that a POSIX path needs no long form and no registry value exists."""
    assert PosixHost().long_path(Path("a/b")) == Path("a/b")
    assert PosixHost().registry_paths() is None


@pytest.mark.medium
def test_the_posix_host_replaces_a_link_in_place(tmp_path):
    """Check that a second replace_dir_link repoints the link at the new folder."""
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    second.mkdir()
    link = tmp_path / "link"
    try:
        PosixHost().replace_dir_link(link, first)
    except OSError:
        pytest.skip("symlinks are not permitted on this machine")

    PosixHost().replace_dir_link(link, second)

    assert link.resolve() == second.resolve()
