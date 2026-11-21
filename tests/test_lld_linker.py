# test_lld_linker.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Which configures link with lld, and what a compiler's answer must be for it to count."""

import pytest

from sushicore.lld_linker import lld_compiler, lld_definitions, lld_is_found


@pytest.mark.small
@pytest.mark.parametrize("compiler", ["/usr/bin/clang++", "/opt/intel/bin/icpx", "clang", "D:/llvm/bin/icx.exe"])
def test_a_clang_driver_on_linux_is_asked_for_lld(compiler):
    assert lld_compiler([], compiler, "linux") == compiler


@pytest.mark.small
@pytest.mark.parametrize("compiler", ["/usr/bin/g++", "/usr/bin/acpp", None, ""])
def test_another_driver_or_none_keeps_the_linker(compiler):
    assert lld_compiler([], compiler, "linux") is None


@pytest.mark.small
@pytest.mark.parametrize("platform", ["win32", "darwin"])
def test_a_platform_other_than_linux_keeps_the_linker(platform):
    assert lld_compiler([], "clang++", platform) is None


@pytest.mark.small
@pytest.mark.parametrize("word", ["-DCMAKE_EXE_LINKER_FLAGS=-fuse-ld=mold", "-DCMAKE_LINKER_TYPE=GOLD"])
def test_a_configure_that_chose_a_linker_keeps_it(word):
    assert lld_compiler([word], "clang++", "linux") is None


@pytest.mark.small
def test_an_answer_naming_an_existing_file_counts(tmp_path):
    lld = tmp_path / "ld.lld"
    lld.write_text("", encoding="utf-8")
    assert lld_is_found(f"{lld}\n")


@pytest.mark.small
@pytest.mark.parametrize("answer", ["ld.lld\n", "", "/no/such/ld.lld\n"])
def test_a_bare_name_or_a_missing_file_does_not_count(answer):
    assert not lld_is_found(answer)


@pytest.mark.small
def test_the_definitions_set_all_three_linker_flag_entries():
    assert lld_definitions() == [
        "-DCMAKE_EXE_LINKER_FLAGS_INIT=-fuse-ld=lld",
        "-DCMAKE_SHARED_LINKER_FLAGS_INIT=-fuse-ld=lld",
        "-DCMAKE_MODULE_LINKER_FLAGS_INIT=-fuse-ld=lld",
    ]
