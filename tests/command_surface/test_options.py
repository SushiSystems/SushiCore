# test_options.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the flags and the defaults of the options build, run, bench and check share."""

import pytest
import typer

from sushicore.command_surface import (BuildTypes, define_option, jobs_option, no_build_option,
                                       no_test_option, report_option, rule_option, target_argument,
                                       type_option)

pytestmark = pytest.mark.small


@pytest.mark.parametrize(("parameter", "flags", "default"), [
    (type_option(BuildTypes(("debug", "release"), "release")), ["--type", "-t"], "release"),
    (define_option(), ["--define", "-D"], None),
    (jobs_option(), ["--jobs", "-j"], None),
    (no_test_option(), ["--no-test"], False),
    (no_build_option(), ["--no-build"], False),
    (report_option(), ["--report", "-r"], False),
    (rule_option(), ["--rule"], None),
])
def test_each_shared_option_has_its_canonical_flags_and_default(parameter, flags, default):
    assert (list(parameter.default.param_decls), parameter.default.default) == (flags, default)


def test_type_option_names_every_type_and_the_default_in_its_help():
    help = type_option(BuildTypes(("debug", "relwithdebinfo"), "debug"), "Tree to run from").default.help
    assert help.startswith("Tree to run from: debug | relwithdebinfo.") and "Default: debug." in help


def test_report_option_takes_the_help_of_the_command_that_declares_it():
    default = report_option().default.help
    given = report_option("Print the edges of the build.").default.help
    assert ("finding count" in default, given) == (True, "Print the edges of the build.")


def test_target_argument_is_an_optional_argument():
    parameter = target_argument()
    assert isinstance(parameter.default, typer.models.ArgumentInfo) and parameter.default.default is None
