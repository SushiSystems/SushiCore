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
    read,
    status,
)


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
