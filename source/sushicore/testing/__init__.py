# __init__.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The shared ``test`` command of a module CLI and the pieces it is built from."""

from .commands import register_test_command
from .labels import LabelSelection, TestLabel, select_labels
from .module_tests import ModuleTests, SanitizedTests
from .options import all_option, filter_option, jobs_option, label_option, repeat_option, seed_option, shuffle_option
from .session import run_tests

__all__ = ["LabelSelection", "ModuleTests", "SanitizedTests", "TestLabel", "all_option", "filter_option",
           "jobs_option", "label_option", "register_test_command", "repeat_option", "run_tests", "seed_option", "select_labels", "shuffle_option"]
