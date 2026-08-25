"""The two pieces of toolchain-flag assembly that carry no module policy."""

from pathlib import Path
from types import SimpleNamespace

from sushicore.toolchain_args import c_compiler_for, vcpkg_prefix


def test_a_clangxx_gets_its_sibling_clang(tmp_path):
    """clang++ hardcodes C++ mode, which breaks CMake's C-language probe."""
    (tmp_path / "clang").write_text("")
    cxx = tmp_path / "clang++"
    cxx.write_text("")
    assert c_compiler_for(str(cxx)) == str(tmp_path / "clang")


def test_a_clangxx_without_a_sibling_is_left_alone(tmp_path):
    cxx = tmp_path / "clang++"
    cxx.write_text("")
    assert c_compiler_for(str(cxx)) == str(cxx)


def test_a_non_clangxx_compiler_is_left_alone(tmp_path):
    assert c_compiler_for("/usr/bin/g++") == "/usr/bin/g++"


def test_the_windows_exe_suffix_is_preserved(tmp_path):
    (tmp_path / "clang.exe").write_text("")
    cxx = tmp_path / "clang++.exe"
    cxx.write_text("")
    assert c_compiler_for(str(cxx)) == str(tmp_path / "clang.exe")


def test_vcpkg_prefix_is_empty_without_a_root():
    cfg = SimpleNamespace(vcpkg_triplet="x64-windows",
                          resolved_vcpkg=lambda root: "")
    assert vcpkg_prefix(cfg, Path(".")) == ""


def test_vcpkg_prefix_names_the_triplet():
    cfg = SimpleNamespace(vcpkg_triplet="x64-windows",
                          resolved_vcpkg=lambda root: "C:/vcpkg")
    assert vcpkg_prefix(cfg, Path(".")) == "C:/vcpkg/installed/x64-windows"
