# test_toolchain_licence.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The toolchain licence installer copies a valid text into its component folder and refuses any other."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.toolchains.toolchain_licence import (
    LicenceTextError, bundled_licence, install_licence, licence_path, llvm_licence_url)

pytestmark = pytest.mark.small

_TEXT = "Apache License 2.0\n--- LLVM Exceptions to the Apache 2.0 License ----\n"


def test_a_valid_text_is_installed_under_its_component(tmp_path: Path):
    """Check that the text lands at share/licenses/llvm-sycl/<component>/LICENSE.TXT unchanged."""
    source = tmp_path / "in.txt"
    source.write_text(_TEXT, encoding="utf-8")

    placed = install_licence(tmp_path / "root", "llvm", source)

    assert placed == licence_path(tmp_path / "root", "llvm")
    assert placed.relative_to(tmp_path / "root").as_posix() == "share/licenses/llvm-sycl/llvm/LICENSE.TXT"
    assert placed.read_text(encoding="utf-8") == _TEXT


@pytest.mark.parametrize("text", ["", "  \n", "Apache License 2.0 only\n"])
def test_an_empty_or_exception_free_text_is_refused_and_nothing_is_written(tmp_path: Path, text: str):
    """Check that a text without the LLVM exception clause raises and leaves no file."""
    source = tmp_path / "in.txt"
    source.write_text(text, encoding="utf-8")

    with pytest.raises(LicenceTextError):
        install_licence(tmp_path / "root", "llvm", source)

    assert not licence_path(tmp_path / "root", "llvm").exists()


def test_a_missing_source_is_refused(tmp_path: Path):
    """Check that an unreadable source raises the licence error that names the component."""
    with pytest.raises(LicenceTextError, match="unified-runtime"):
        install_licence(tmp_path, "unified-runtime", tmp_path / "absent.txt")


def test_the_bundle_licence_is_found_at_the_root_only(tmp_path: Path):
    """Check that a LICENSE.TXT at the bundle root is found and a nested one is not."""
    (tmp_path / "doc").mkdir()
    (tmp_path / "doc" / "LICENSE.TXT").write_text(_TEXT, encoding="utf-8")
    assert bundled_licence(tmp_path) is None
    (tmp_path / "LICENSE.TXT").write_text(_TEXT, encoding="utf-8")
    assert bundled_licence(tmp_path) == tmp_path / "LICENSE.TXT"


def test_the_llvm_url_is_built_from_the_pinned_ref():
    """Check that the raw GitHub URL names the ref and LLVM's licence path."""
    assert llvm_licence_url("nightly-2026-11-17") == (
        "https://raw.githubusercontent.com/intel/llvm/nightly-2026-11-17/llvm/LICENSE.TXT")
