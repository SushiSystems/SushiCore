# test_deps_fragment.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Reading a dependency fragment, and what can be said about one entry.

The format is written by hand in several repositories, so most of what matters
is what the reader refuses and what it declines to guess.
"""

from __future__ import annotations

import sys

import pytest

from sushicore.deps_fragment import (
    Dependency,
    Status,
    install_command,
    pins_at,
    read_present,
    read,
    status,
)


pytestmark = pytest.mark.medium


def _fragment(tmp_path, text: str):
    """Write *text* as a fragment and return its path."""
    path = tmp_path / "sushistack.deps.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_one_table_per_dependency_is_the_shape(tmp_path):
    """Each top-level table becomes a dependency keyed by its name."""
    fragment = read(_fragment(tmp_path, """
[sdl2]
description = "Audio device backend."
required = true
linux_apt = ["libsdl2-dev"]
windows_vcpkg = ["sdl2"]
"""))

    assert [d.name for d in fragment.dependencies] == ["sdl2"]
    assert fragment.dependencies[0].required is True
    assert fragment.dependencies[0].linux_apt == ["libsdl2-dev"]
    assert fragment.depends_on == []


def test_the_module_table_is_metadata_rather_than_a_dependency(tmp_path):
    """[module] carries depends_on and never becomes a Dependency of its own."""
    fragment = read(_fragment(tmp_path, """
[module]
depends_on = ["sushiruntime"]

[sushisystems.sushiruntime]
version = "v1.0.0"
commit = "0123456789abcdef0123456789abcdef01234567"

[hwloc]
description = "Topology."
"""))

    assert [d.name for d in fragment.dependencies] == ["hwloc"]
    assert fragment.depends_on == ["sushiruntime"]


def test_an_array_of_tables_is_refused_rather_than_skipped(tmp_path):
    """The shape that used to lose a whole fragment now names itself."""
    path = _fragment(tmp_path, '[[dependency]]\nname = "sdl2"\nrequired = true\n')

    with pytest.raises(ValueError) as caught:
        read(path)

    assert "dependency" in str(caught.value)
    assert str(path) in str(caught.value)


def test_a_scalar_at_the_top_level_is_refused_too(tmp_path):
    """Any non-table top-level key is a shape the reader does not understand."""
    with pytest.raises(ValueError):
        read(_fragment(tmp_path, 'version = "1"\n\n[sdl2]\ndescription = "x"\n'))


def test_the_platform_decides_which_column_is_read():
    """Windows reads the vcpkg ports and every other platform reads apt."""
    dep = Dependency(name="sdl2", linux_apt=["libsdl2-dev"], windows_vcpkg=["sdl2[vulkan]"])

    assert dep.packages_for("windows") == ["sdl2[vulkan]"]
    assert dep.packages_for("linux") == ["libsdl2-dev"]


def test_a_dependency_with_no_package_here_is_not_applicable():
    """An entry that installs nothing on this platform is neither missing nor met."""
    dep = Dependency(name="intel-llvm", required=False)

    assert status(dep, "linux") is Status.NOT_APPLICABLE
    assert install_command(dep, "linux") is None


def test_a_package_nobody_can_check_is_unknown():
    """Whether a package is installed is a package manager's answer, not this one's."""
    dep = Dependency(name="sdl2", linux_apt=["libsdl2-dev"])

    assert status(dep, "linux") is Status.UNKNOWN


def test_a_check_command_that_passes_settles_it():
    """A declared check is the one thing this module can decide by itself."""
    dep = Dependency(name="python", check_cmd=[sys.executable, "--version"],
                     linux_apt=["python3"])

    assert status(dep, "linux") is Status.SATISFIED


def test_a_check_command_that_fails_leaves_it_unknown():
    """A failed check says the check failed, not that the package is absent."""
    dep = Dependency(name="nope", check_cmd=[sys.executable, "-c", "raise SystemExit(3)"],
                     linux_apt=["nope"])

    assert status(dep, "linux") is Status.UNKNOWN


def test_a_check_command_that_cannot_run_leaves_it_unknown():
    """A missing checker is not evidence about the dependency."""
    dep = Dependency(name="nope", check_cmd=["definitely-not-a-program-3f1c"],
                     linux_apt=["nope"])

    assert status(dep, "linux") is Status.UNKNOWN


def test_the_install_command_names_apt_off_windows():
    """The caller runs it or prints it; either way it is the whole command."""
    dep = Dependency(name="sdl2", linux_apt=["libsdl2-dev"])

    assert install_command(dep, "linux") == ["sudo", "apt-get", "install", "-y", "libsdl2-dev"]


def test_the_install_command_names_vcpkg_on_windows():
    """The caller passes its own vcpkg, because this library knows no tree."""
    dep = Dependency(name="sdl2", windows_vcpkg=["sdl2[vulkan]"])

    assert install_command(dep, "windows", vcpkg="C:/vcpkg/vcpkg.exe",
                           triplet="x64-windows") == [
        "C:/vcpkg/vcpkg.exe", "install", "sdl2[vulkan]:x64-windows"]


def test_the_triplet_is_left_off_when_the_caller_pins_none():
    """A caller with no triplet gets the ports as the fragment wrote them."""
    dep = Dependency(name="sdl2", windows_vcpkg=["sdl2"])

    assert install_command(dep, "windows") == ["vcpkg", "install", "sdl2"]


K_DIGEST = "3f" * 32


def test_an_entry_without_sha256_pins_nothing(tmp_path):
    """The field is optional, so every fragment written before it still reads."""
    (dep,) = read(_fragment(tmp_path, """
[cmake]
description = "Build system."
""")).dependencies

    assert dep.sha256 == {}
    assert dep.digest_for("windows") == ""


def test_sha256_pins_one_digest_per_platform(tmp_path):
    """The table is keyed by platform, because each platform downloads its own file."""
    (dep,) = read(_fragment(tmp_path, f"""
[intel-llvm]
sha256 = {{ windows = "{K_DIGEST}", linux = "{K_DIGEST.upper()}" }}
""")).dependencies

    assert dep.digest_for("windows") == K_DIGEST
    assert dep.digest_for("linux") == K_DIGEST
    assert dep.sha256 == {"windows": K_DIGEST, "linux": K_DIGEST}


def test_a_platform_the_table_leaves_out_has_no_digest(tmp_path):
    """A digest for one platform says nothing about the file another one downloads."""
    (dep,) = read(_fragment(tmp_path, f"""
[cmake]
sha256 = {{ windows = "{K_DIGEST}" }}
""")).dependencies

    assert dep.digest_for("linux") == ""


@pytest.mark.parametrize("value", [
    f'"{K_DIGEST}"',
    '{ windows = "abc123" }',
    f'{{ windows = "{"zz" * 32}" }}',
    '{ windows = 7 }',
    f'{{ macos = "{K_DIGEST}" }}',
])
def test_a_sha256_that_cannot_pin_a_file_is_refused(tmp_path, value):
    """A digest the reader cannot use is named, because dropping it leaves a download unchecked."""
    path = _fragment(tmp_path, f"""
[cmake]
sha256 = {value}
""")

    with pytest.raises(ValueError) as refused:
        read(path)

    assert "cmake" in str(refused.value) and "sha256" in str(refused.value)


def test_a_sushi_pin_is_read_with_its_tag_and_commit(tmp_path):
    """[sushisystems.<name>] carries a release tag and the full commit, in lower case."""
    fragment = read(_fragment(tmp_path, """
[module]
depends_on = ["sushilog"]

[sushisystems.sushilog]
version = "v1.0.0"
commit = "0123456789ABCDEF0123456789ABCDEF01234567"
"""))

    assert [(p.name, p.version, p.commit) for p in fragment.pins] == [
        ("sushilog", "v1.0.0", "0123456789abcdef0123456789abcdef01234567")]
    assert fragment.dependencies == []


def test_the_deprecated_sushi_table_reads_with_a_warning(tmp_path):
    """[sushi.<name>] reads the same pins and warns that the table is now [sushisystems.<name>]."""
    path = _fragment(tmp_path, f"""
[module]
depends_on = ["sushilog"]

[sushi.sushilog]
version = "v1.0.0"
commit = "{"0" * 40}"
""")

    with pytest.warns(DeprecationWarning, match=r"\[sushisystems\.<name>\]"):
        fragment = read(path)

    assert [(p.name, p.version) for p in fragment.pins] == [("sushilog", "v1.0.0")]


def test_pins_under_both_table_names_are_refused(tmp_path):
    """A file keeps its pins under one table name."""
    text = f"""
[module]
depends_on = ["sushilog"]

[sushisystems.sushilog]
version = "v1.0.0"
commit = "{"0" * 40}"

[sushi.sushilog]
version = "v1.0.0"
commit = "{"0" * 40}"
"""

    with pytest.raises(ValueError, match="both"):
        read(_fragment(tmp_path, text))


def test_a_module_in_depends_on_may_go_unpinned(tmp_path):
    """A module depends_on names without a pin reads, with no pin."""
    fragment = read(_fragment(tmp_path, '[module]\ndepends_on = ["sushilog"]\n'))
    assert fragment.depends_on == ["sushilog"] and fragment.pins == []


def test_a_pin_not_in_depends_on_is_refused(tmp_path):
    """A pin names a module depends_on lists."""
    text = f'[sushisystems.sushilog]\nversion = "v1.0.0"\ncommit = "0123456789abcdef0123456789abcdef01234567"\n'
    with pytest.raises(ValueError, match="which depends_on does not name"):
        read(_fragment(tmp_path, text))


@pytest.mark.parametrize("table, expected", [
    ('commit = "0123456789abcdef0123456789abcdef01234567"', "no version"),
    ('version = "v1.0.0"\ncommit = "abc"', "full 40-hex hash"),
])
def test_a_malformed_pin_is_refused(tmp_path, table, expected):
    """A pin without a tag or with a short commit names what is wrong."""
    text = f'[module]\ndepends_on = ["sushilog"]\n[sushisystems.sushilog]\n{table}\n'
    with pytest.raises(ValueError, match=expected):
        read(_fragment(tmp_path, text))


def test_an_absent_fragment_reads_as_none_with_no_pins(tmp_path):
    """A checkout with no fragment has no fragment and no pins."""
    assert read_present(tmp_path / "absent.toml") is None
    assert pins_at(tmp_path / "absent.toml") == []


def test_the_module_table_names_the_cli_and_the_package_exclusions(tmp_path):
    """The cli command and the package exclusions of a library read from [module]."""
    text = '[module]\ncli = "sr"\npackage_exclude = ["bench/", "*.txt"]\n'
    fragment = read(_fragment(tmp_path, text))
    assert (fragment.cli, fragment.package_exclude) == ("sr", ["bench/", "*.txt"])


def test_a_module_table_without_the_keys_reads_them_empty(tmp_path):
    """A fragment that names no cli and no exclusions reads empty values."""
    fragment = read(_fragment(tmp_path, '[module]\ndepends_on = []\n'))
    assert (fragment.cli, fragment.package_exclude) == ("", [])


@pytest.mark.parametrize("line, expected", [
    ("cli = 3", "cli is a int"),
    ('package_exclude = "docs"', "package_exclude"),
    ("package_exclude = [1]", "package_exclude"),
])
def test_a_malformed_cli_or_exclusion_is_refused(tmp_path, line, expected):
    """A cli that is not a string and an exclusion that is not a list of strings raise."""
    with pytest.raises(ValueError, match=expected):
        read(_fragment(tmp_path, f"[module]\n{line}\n"))
