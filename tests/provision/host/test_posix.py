# test_posix.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the POSIX host."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.proc_memory import RecordingRunner
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


def _runner() -> RecordingRunner:
    """Return a runner that records commands and starts no process."""
    return RecordingRunner(RecordingConsole())


@pytest.mark.small
def test_a_missing_lspci_is_recorded(caplog):
    """Check that an lspci that cannot start yields no adapters and one warning."""
    with caplog.at_level("WARNING", logger="sushicore.provision"):
        assert PosixHost().display_adapters(_runner().script_missing()) == ""
    warnings = [r.getMessage() for r in caplog.records if r.levelname == "WARNING"]
    assert len(warnings) == 1
    assert "lspci" in warnings[0]


@pytest.mark.small
def test_lspci_display_lines_are_kept_in_lower_case():
    """Check that only the display-controller lines of lspci come back, lower-cased."""
    runner = _runner().script(0, ("00:02.0 VGA compatible controller: Intel", "00:1f.0 ISA bridge"))
    assert PosixHost().display_adapters(runner) == "00:02.0 vga compatible controller: intel"
