# test_steps.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the deprecated ``sushicore.provision.steps`` module."""

from __future__ import annotations

import importlib
import sys

import pytest

from sushicore.provision.configure_step import ConfigureStep
from sushicore.provision.detect_step import DetectStep
from sushicore.provision.gpu_stage import GpuStage
from sushicore.provision.install_deps_step import InstallDepsStep
from sushicore.provision.machine_actions import MachineActions
from sushicore.provision.packages import refresh_windows_path
from sushicore.provision.uninstall_step import UninstallStep

pytestmark = pytest.mark.small

K_MODULE = "sushicore.provision.steps"


@pytest.fixture
def steps():
    """Import the module afresh, so its import warning is raised inside the test."""
    sys.modules.pop(K_MODULE, None)
    with pytest.warns(DeprecationWarning):
        return importlib.import_module(K_MODULE)


def test_importing_the_module_warns_at_the_importer_and_names_what_replaces_it():
    """Check that the import warns, points at this file and names the modules that replace it."""
    sys.modules.pop(K_MODULE, None)
    with pytest.warns(DeprecationWarning, match="DetectStep") as caught:
        __import__(K_MODULE)
    assert caught[0].filename == __file__


def test_the_module_still_exports_each_step_and_helper_consumers_imported(steps):
    """Check that every name the consumers import is the object its own module holds."""
    assert (steps.DetectStep, steps.InstallDepsStep, steps.ConfigureStep, steps.UninstallStep,
            steps.MachineActions, steps.GpuStage, steps.refresh_windows_path) == (
        DetectStep, InstallDepsStep, ConfigureStep, UninstallStep, MachineActions, GpuStage,
        refresh_windows_path)


def test_the_module_lists_exactly_the_names_it_re_exports(steps):
    """Check that the star import brings the same seven names."""
    assert sorted(steps.__all__) == sorted([
        "ConfigureStep", "DetectStep", "GpuStage", "InstallDepsStep", "MachineActions",
        "UninstallStep", "refresh_windows_path"])
