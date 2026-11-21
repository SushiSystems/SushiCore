# test_example_catalog.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The catalog of the examples a repository registers, however it names its registration call."""

from pathlib import Path

import pytest

from sushicore.example_catalog import Example, ExampleCatalog, K_EXAMPLES_FOLDER


pytestmark = pytest.mark.medium

_TOP = """\
# my_add_example(<name> SOURCES <file>) is the usage line, not an entry.
function(my_add_example name)
    add_executable(${name} ${ARGN})
endfunction()

my_add_example(sr_alpha DEVICE_SOURCES alpha.cpp)
add_executable(beta_demo source/beta_demo.cpp)
# add_executable(commented_out commented_out.cpp)
add_executable(beta_demo source/beta_demo.cpp)
my_add_example(sr_pair
    DEVICE_SOURCES kernels.cpp
    SOURCES pair.cpp)
my_add_example(sr_unwritten DEVICE_SOURCES unwritten.cpp)
add_subdirectory(nested)
"""


def _write(path: Path, text: str) -> None:
    """Create *path* with *text*, and the folders above it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _source(*lines: str) -> str:
    """Return a source file whose `@file` block carries *lines* after its name."""
    body = "\n".join(f" * {line}" for line in lines)
    return f"/**\n * @file x.cpp\n{body}\n * @author Someone\n */\n"


@pytest.fixture
def examples_dir(tmp_path: Path) -> Path:
    """Return a folder that registers its examples in three ways, one of them nested."""
    folder = tmp_path / "examples"
    _write(folder / "CMakeLists.txt", _TOP)
    _write(folder / "alpha.cpp", _source("@brief Runs alpha.", "@see README.md"))
    _write(folder / "source" / "beta_demo.cpp", _source("@brief Runs beta."))
    _write(folder / "kernels.cpp", _source("@brief Declares kernels."))
    _write(folder / "pair.cpp", _source("@brief Runs a pair of tasks", "that share a buffer."))
    _write(folder / "nested" / "CMakeLists.txt", "add_executable(gamma_demo gamma.cpp)\n")
    _write(folder / "nested" / "gamma.cpp", _source("@brief Runs gamma."))
    return folder


def test_entries_lists_the_targets_in_registration_order_shallowest_file_first(examples_dir):
    names = [example.name for example in ExampleCatalog(examples_dir).entries()]

    assert names == ["sr_alpha", "beta_demo", "sr_pair", "sr_unwritten", "gamma_demo"]


def test_entries_skips_comments_the_wrapper_body_and_a_target_named_by_a_variable(examples_dir):
    names = [example.name for example in ExampleCatalog(examples_dir).entries()]

    assert "commented_out" not in names and "${name}" not in names and "name" not in names


def test_entries_takes_the_brief_up_to_the_next_tag(examples_dir):
    first = ExampleCatalog(examples_dir).entries()[0]

    assert first == Example("sr_alpha", "Runs alpha.")


def test_entries_takes_the_brief_of_the_source_in_the_folder_of_its_own_file(examples_dir):
    gamma = ExampleCatalog(examples_dir).entries()[-1]

    assert gamma == Example("gamma_demo", "Runs gamma.")


def test_entries_joins_a_brief_that_runs_over_two_lines(examples_dir):
    pair = ExampleCatalog(examples_dir).entries()[2]

    assert pair.brief == "Runs a pair of tasks that share a buffer."


def test_entries_takes_the_first_source_when_none_is_named_like_the_target(tmp_path):
    folder = tmp_path / "examples"
    _write(folder / "CMakeLists.txt", "add_executable(tool main.cpp)\n")
    _write(folder / "main.cpp", _source("@brief Runs the tool."))

    assert ExampleCatalog(folder).entries() == [Example("tool", "Runs the tool.")]


def test_entries_leaves_the_brief_empty_when_the_source_is_missing(examples_dir):
    unwritten = ExampleCatalog(examples_dir).entries()[3]

    assert unwritten.brief == ""


def test_entries_is_empty_when_the_folder_does_not_exist(tmp_path):
    assert ExampleCatalog(tmp_path / "nowhere").entries() == []


def test_in_project_reads_the_applications_examples_folder(tmp_path):
    _write(tmp_path / K_EXAMPLES_FOLDER / "CMakeLists.txt", "add_executable(solo solo.cpp)\n")

    assert [example.name for example in ExampleCatalog.in_project(tmp_path).entries()] == ["solo"]
