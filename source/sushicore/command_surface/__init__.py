# __init__.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The canonical command surface: the shared build, run, bench and check commands, panels and verbs."""

from .bench_command import register_bench_command
from .bench_service import BenchRequest, BenchService
from .build_command import register_build_command
from .build_service import BuildRequest, BuildService
from .build_types import BuildTypes
from .check_command import register_check_command
from .check_service import CheckRequest, CheckService
from .command_parameter import CommandParameter
from .errors import (BuildTypeError, CommandSurfaceError, DomainPanelError, ParameterNameError,
                     SanitizerConflictError, UnknownSanitizerError, UnknownVerbError)
from .options import (define_option, jobs_option, no_build_option, no_test_option, report_option,
                      rule_option, target_argument, type_option)
from .panels import (K_BUILD_PANEL, K_ENVIRONMENT_PANEL, K_PANELS, K_RECORDS_PANEL, K_RUN_PANEL,
                     K_VERB_PANELS, CommandPanels, panel_of)
from .run_command import register_run_command
from .run_service import RunRequest, RunService
from .sanitize_option import K_SANITIZER_KINDS, parse_sanitizers, sanitize_option
from .verb_assertions import assert_registers_verbs
from .verbs import K_CANONICAL_VERBS

__all__ = [
    "BenchRequest", "BenchService", "BuildRequest", "BuildService", "BuildTypeError", "BuildTypes",
    "CheckRequest", "CheckService", "CommandPanels", "CommandParameter", "CommandSurfaceError",
    "DomainPanelError", "K_BUILD_PANEL", "K_CANONICAL_VERBS", "K_ENVIRONMENT_PANEL", "K_PANELS",
    "K_RECORDS_PANEL", "K_RUN_PANEL", "K_SANITIZER_KINDS", "K_VERB_PANELS", "ParameterNameError",
    "RunRequest", "RunService", "SanitizerConflictError", "UnknownSanitizerError", "UnknownVerbError",
    "assert_registers_verbs", "define_option", "jobs_option", "no_build_option", "no_test_option",
    "panel_of", "parse_sanitizers", "register_bench_command", "register_build_command",
    "register_check_command", "register_run_command", "report_option", "rule_option",
    "sanitize_option", "target_argument", "type_option",
]
