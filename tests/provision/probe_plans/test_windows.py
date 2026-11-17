# test_windows.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the Windows probe plan records in the local config."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.config import ProvisionSettings
from sushicore.provision.probe_plans.windows import WindowsProbePlan


@pytest.mark.small
@pytest.mark.parametrize(("glob_hit", "found", "expected"), [
    ("C:/VS/2022/x.bat", None, "C:/VS/2022/x.bat"),
    ("", Path("/machine/vcvars64.bat"), str(Path("/machine/vcvars64.bat"))),
], ids=["the 2022 glob comes first", "find_vcvars is the fallback"])
def test_the_visual_studio_script_is_looked_for_in_the_glob_then_the_finder(glob_hit, found, expected):
    """Check the order in which the Visual Studio script is looked for."""
    plan = WindowsProbePlan(first_glob=lambda patterns: glob_hit, vcvars_finder=lambda: found)

    values = plan.resolve_local_config(ProvisionSettings(platform="windows"))

    assert values["vs_vcvars"] == expected


@pytest.mark.medium
def test_a_configured_visual_studio_script_that_exists_is_kept(tmp_path):
    """Check that a script the config names, and that exists, is recorded without any search."""
    script = tmp_path / "vcvars64.bat"
    script.write_text("", encoding="utf-8")
    plan = WindowsProbePlan(first_glob=lambda patterns: "from glob", vcvars_finder=lambda: None)

    values = plan.resolve_local_config(ProvisionSettings(platform="windows", vs_vcvars=str(script)))

    assert values["vs_vcvars"] == str(script)
