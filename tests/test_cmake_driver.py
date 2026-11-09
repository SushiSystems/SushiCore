# test_cmake_driver.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The driver's whole contract is the argv it produces."""

import os
from pathlib import Path

import pytest

from sushicore.cmake_driver import CMakeDriver
from sushicore.config_base import ToolConfig
from sushicore.console_memory import RecordingConsole
from sushicore.proc_memory import RecordingRunner

K_TREE = Path("tree")


def _calls(runner):
    """Return the commands *runner* recorded as ``(kind, argv, cwd)``, kind being run or drained."""
    return [("drained" if command.drained else "run", list(command.argv), str(command.cwd))
            for command in runner.commands]


def _lines(console):
    """Return the text of every call the console recorded, in order."""
    return [call.text for call in console.calls]


def _cfg(**kw):
    """Return a tool config with the settings *kw* names and the defaults for the rest."""
    return ToolConfig(**kw)


def _runner():
    """Return a runner that records its commands and prints to a console of its own."""
    return RecordingRunner(RecordingConsole())


def _driver():
    runner = _runner()
    return CMakeDriver(RecordingConsole(), runner), runner


@pytest.mark.small
def test_cmake_defaults_to_the_bare_name():
    driver, _ = _driver()
    assert driver.cmake(_cfg()) == "cmake"


@pytest.mark.small
def test_cmake_takes_the_configured_path():
    driver, _ = _driver()
    assert driver.cmake(_cfg(cmake_exe="C:/tools/cmake.exe")) == "C:/tools/cmake.exe"


@pytest.mark.medium
def test_compile_builds_the_expected_argv(tmp_path):
    driver, runner = _driver()
    driver.compile(_cfg(), tmp_path, tmp_path, None, config="Release")
    assert _calls(runner) == [
        ("run", ["cmake", "--build", str(tmp_path), "--config", "Release"],
         str(tmp_path))]


@pytest.mark.medium
def test_compile_appends_targets(tmp_path):
    driver, runner = _driver()
    driver.compile(_cfg(), tmp_path, tmp_path, None, config="Debug",
                   targets=("editor",))
    assert _calls(runner)[0][1] == [
        "cmake", "--build", str(tmp_path), "--config", "Debug",
        "--target", "editor"]


@pytest.mark.small
def test_ctest_run_is_drained_and_carries_the_knobs():
    driver, runner = _driver()
    driver.ctest_run(_cfg(), K_TREE, None, label_regex="^unit$",
                     filter="Gemm.*", repeat=3)
    kind, argv, cwd = _calls(runner)[0]
    assert kind == "drained"
    assert argv == ["ctest", "--test-dir", str(K_TREE), "--output-on-failure",
                    "-L", "^unit$", "-R", "Gemm.*", "--repeat", "until-fail:3"]
    assert cwd == str(K_TREE)


@pytest.mark.small
def test_ctest_run_leaves_out_the_excluded_labels():
    driver, runner = _driver()
    driver.ctest_run(_cfg(), K_TREE, None, label_regex="^(small|medium)$",
                     exclude_label_regex="^quarantined$")
    assert _calls(runner)[0][1][-4:] == ["-L", "^(small|medium)$", "-LE", "^quarantined$"]


@pytest.mark.small
def test_ctest_run_writes_a_junit_file_when_asked():
    driver, runner = _driver()
    report = K_TREE / "junit.xml"
    driver.ctest_run(_cfg(), K_TREE, None, label_regex="^small$", output_junit=report)
    assert _calls(runner)[0][1][-2:] == ["--output-junit", str(report)]


@pytest.mark.small
def test_ctest_run_omits_absent_knobs():
    driver, runner = _driver()
    driver.ctest_run(_cfg(), K_TREE, None)
    assert _calls(runner)[0][1] == ["ctest", "--test-dir", str(K_TREE),
                                    "--output-on-failure"]


@pytest.mark.medium
def test_needs_configure_when_there_is_no_tree(tmp_path):
    driver, _ = _driver()
    assert driver.needs_configure(tmp_path / "absent", "Ninja") is True


@pytest.mark.medium
def test_needs_configure_when_the_sentinel_is_missing(tmp_path):
    driver, _ = _driver()
    assert driver.needs_configure(tmp_path, "Ninja") is True


@pytest.mark.medium
def test_no_reconfigure_when_expectations_hold(tmp_path):
    (tmp_path / "build.ninja").write_text("")
    (tmp_path / "CMakeCache.txt").write_text("CMAKE_BUILD_TYPE:STRING=Release\n")
    driver, _ = _driver()
    assert driver.needs_configure(tmp_path, "Ninja",
                                  expect={"CMAKE_BUILD_TYPE": "Release"}) is False


@pytest.mark.medium
def test_reconfigure_when_an_expectation_is_violated(tmp_path):
    (tmp_path / "build.ninja").write_text("")
    (tmp_path / "CMakeCache.txt").write_text("CMAKE_BUILD_TYPE:STRING=Release\n")
    driver, _ = _driver()
    assert driver.needs_configure(tmp_path, "Ninja",
                                  expect={"CMAKE_BUILD_TYPE": "Debug"}) is True


# is_stale's comparison is pinned in test_cmake_cache.py; see docs/architecture/OVERVIEW.md.

@pytest.mark.medium
def test_root_mismatch_forces_reconfigure_and_warns(tmp_path):
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    (build_dir / "build.ninja").write_text("")
    (build_dir / "CMakeCache.txt").write_text(
        "CMAKE_HOME_DIRECTORY:INTERNAL=/workspace/sushiengine\n")
    console = RecordingConsole()
    driver = CMakeDriver(console, _runner())

    assert driver.needs_configure(build_dir, "Ninja",
                                  root=tmp_path / "sushiengine") is True
    assert any("different source path" in line for line in _lines(console))


@pytest.mark.medium
def test_root_match_does_not_reconfigure_or_warn(tmp_path):
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    (build_dir / "build.ninja").write_text("")
    root = tmp_path / "sushiengine"
    (build_dir / "CMakeCache.txt").write_text(
        f"CMAKE_HOME_DIRECTORY:INTERNAL={root}\n")
    console = RecordingConsole()
    driver = CMakeDriver(console, _runner())

    assert driver.needs_configure(build_dir, "Ninja", root=root) is False
    assert _lines(console) == []


@pytest.mark.medium
def test_clean_tree_says_so_when_there_is_nothing_to_clean(tmp_path):
    console = RecordingConsole()
    driver = CMakeDriver(console, _runner())
    driver.clean_tree(tmp_path / "absent")
    assert any("nothing to clean" in line for line in _lines(console))


@pytest.mark.medium
def test_clean_tree_removes_the_directory_it_is_given(tmp_path):
    build = tmp_path / "build"
    (build / "CMakeFiles").mkdir(parents=True)
    (build / "CMakeCache.txt").write_text("")
    driver = CMakeDriver(RecordingConsole(), _runner())
    driver.clean_tree(build)
    assert not build.exists()


@pytest.mark.medium
def test_clean_tree_removes_only_that_directory(tmp_path):
    """The failure that would matter: removing the parent instead of the tree."""
    sibling = tmp_path / "keep"
    sibling.mkdir()
    build = tmp_path / "build"
    build.mkdir()
    driver = CMakeDriver(RecordingConsole(), _runner())
    driver.clean_tree(build)
    assert sibling.is_dir()


@pytest.mark.medium
def test_clean_tree_reports_a_tree_that_is_still_there(tmp_path, monkeypatch):
    """A tree a program holds open survives the removal and must not be reported as removed."""
    build = tmp_path / "build"
    build.mkdir()
    monkeypatch.setattr("sushicore.cmake_driver.shutil.rmtree", lambda *arguments, **keywords: None)
    console = RecordingConsole()
    assert CMakeDriver(console, _runner()).clean_tree(build) is False
    assert any("could not be removed completely" in line for line in _lines(console))
    assert not any(line.endswith("removed.") for line in _lines(console))


@pytest.mark.medium
def test_clean_tree_returns_true_for_a_removed_tree(tmp_path):
    build = tmp_path / "build"
    build.mkdir()
    assert CMakeDriver(RecordingConsole(), _runner()).clean_tree(build) is True


@pytest.mark.medium
def test_clean_tree_returns_true_for_an_absent_tree(tmp_path):
    assert CMakeDriver(RecordingConsole(), _runner()).clean_tree(tmp_path / "absent") is True


def _installed_doxygen(tmp_path: Path):
    """A doxygen_exe pointing at a file that exists, so the driver's own
    not-installed check passes and execution reaches the run() call."""
    doxy = tmp_path / "doxygen.exe"
    doxy.write_text("")
    return str(doxy)


@pytest.mark.medium
def test_doxygen_passes_a_path_relative_to_cwd(tmp_path):
    """The child resolves its argument against cwd; every module hands the driver an
    absolute Doxyfile so its own existence check is robust to being invoked from a
    subdirectory, so the driver must derive the relative form rather than take it."""
    doxyfile = tmp_path / "Doxyfile"
    doxyfile.write_text("")
    doxy = _installed_doxygen(tmp_path)
    driver, runner = _driver()

    driver.doxygen(_cfg(doxygen_exe=doxy), doxyfile, tmp_path, None, install_hint="")

    assert _calls(runner) == [("run", [doxy, "Doxyfile"], str(tmp_path))]


@pytest.mark.medium
def test_doxygen_derives_a_nested_relative_path(tmp_path):
    """SushiEngine's Doxyfile lives under .config/doxygen/; the argv must name it the
    same way the module always has, not the absolute path the existence check needs."""
    doxyfile = tmp_path / ".config" / "doxygen" / "Doxyfile"
    doxyfile.parent.mkdir(parents=True)
    doxyfile.write_text("")
    doxy = _installed_doxygen(tmp_path)
    driver, runner = _driver()

    driver.doxygen(_cfg(doxygen_exe=doxy), doxyfile, tmp_path, None, install_hint="")

    assert _calls(runner)[0][1] == [doxy, ".config/doxygen/Doxyfile"]


@pytest.mark.medium
def test_doxygen_not_found_names_the_absolute_path():
    """Printed, not spawned, so naming the full path here cannot move the argv."""
    console = RecordingConsole()
    driver = CMakeDriver(console, _runner())
    missing = Path("/project/Doxyfile")

    assert driver.doxygen(_cfg(), missing, Path("/project"), None, install_hint="") == 1
    assert any(str(missing) in line for line in _lines(console))


@pytest.mark.medium
def test_doxygen_prints_the_install_hint_and_returns_1_when_doxygen_is_not_on_path(tmp_path):
    doxyfile = tmp_path / "Doxyfile"
    doxyfile.write_text("")
    console = RecordingConsole()
    driver = CMakeDriver(console, _runner())

    code = driver.doxygen(_cfg(doxygen_exe="no-such-doxygen-executable"), doxyfile, tmp_path, None,
                          install_hint="  - install it by hand")

    assert code == 1
    assert console.texts("error") == [
        "Doxygen is not installed or not on PATH.\n  - install it by hand"]


@pytest.mark.medium
def test_compile_places_parallel_before_targets(tmp_path):
    driver, runner = _driver()
    driver.compile(_cfg(), tmp_path, tmp_path, None, config="Release",
                   targets=["a"], jobs=8)
    assert _calls(runner)[-1][1] == ["cmake", "--build", str(tmp_path), "--config",
                                     "Release", "--parallel", "8", "--target", "a"]


@pytest.mark.small
def test_ctest_run_appends_parallel_and_config_in_order():
    driver, runner = _driver()
    driver.ctest_run(_cfg(), K_TREE, None, filter="S.*", repeat=2, jobs=4,
                     config="Debug")
    assert _calls(runner)[-1][1] == [
        "ctest", "--test-dir", str(K_TREE), "--output-on-failure", "-R", "S.*",
        "--repeat", "until-fail:2", "--parallel", "4", "-C", "Debug"]


@pytest.mark.small
def test_ctest_run_passes_parallel_for_a_single_job():
    driver, runner = _driver()
    driver.ctest_run(_cfg(), K_TREE, None, jobs=1)
    command = _calls(runner)[-1][1]
    assert command[command.index("--parallel") + 1] == "1"


def _configured_tree(tmp_path, compiler):
    build = tmp_path / "build"
    build.mkdir()
    (build / "CMakeCache.txt").write_text(
        f"CMAKE_CXX_COMPILER:STRING={compiler}\nSUSHI_OPTION:BOOL=ON\n", encoding="utf-8")
    return build


@pytest.mark.medium
def test_configure_drops_the_cache_when_the_compiler_path_changed(tmp_path):
    build = _configured_tree(tmp_path, "D:/old/bin/clang++.exe")
    driver, runner = _driver()
    args = ["cmake", "-S", str(tmp_path), "-B", str(build),
            "-DCMAKE_CXX_COMPILER=D:/new/bin/clang++.exe", "-DSUSHI_OPTION=ON"]
    assert driver.configure(args, tmp_path) == 0
    assert not (build / "CMakeCache.txt").exists()
    assert _calls(runner) == [("run", args, str(tmp_path))]


@pytest.mark.medium
@pytest.mark.parametrize("spelled", [
    "D:/Tools/bin/./clang++.exe",
    pytest.param(r"D:\Tools\bin\clang++.exe",
                 marks=pytest.mark.skipif(os.name != "nt", reason="only Windows reads a backslash as a separator")),
])
def test_configure_keeps_the_cache_when_only_the_spelling_of_the_path_differs(tmp_path, spelled):
    build = _configured_tree(tmp_path, "D:/Tools/bin/clang++.exe")
    driver, _ = _driver()
    driver.configure(["cmake", "-B", str(build), f"-DCMAKE_CXX_COMPILER={spelled}"], tmp_path)
    assert (build / "CMakeCache.txt").exists()


@pytest.mark.medium
def test_configure_keeps_the_cache_when_no_compiler_is_named(tmp_path):
    build = _configured_tree(tmp_path, "D:/old/bin/clang++.exe")
    driver, _ = _driver()
    driver.configure(["cmake", "-B", str(build), "-DSUSHI_OPTION=ON"], tmp_path)
    assert (build / "CMakeCache.txt").exists()


@pytest.mark.medium
def test_compile_hands_the_compilers_a_scratch_folder_in_the_tree(tmp_path):
    driver, runner = _driver()
    driver.compile(_cfg(), tmp_path, tmp_path, {"TMP": "C:/Temp", "PATH": "x"}, config="Release")
    env = runner.commands[-1].env
    scratch = str(tmp_path / "compiler_tmp")
    assert (env["TMP"], env["TEMP"]) == (scratch, scratch)


@pytest.mark.medium
def test_compile_empties_the_scratch_folder_when_the_build_ends(tmp_path):
    scratch = tmp_path / "compiler_tmp"
    scratch.mkdir()
    (scratch / "main-sm_86-65cff7.s").write_text("leftover")
    driver, _ = _driver()
    driver.compile(_cfg(), tmp_path, tmp_path, None, config="Release")
    assert not scratch.exists()


@pytest.mark.medium
def test_compile_empties_the_scratch_folder_when_the_build_fails(tmp_path):
    scratch = tmp_path / "compiler_tmp"
    scratch.mkdir()
    (scratch / "main-sm_86-65cff7.s").write_text("leftover")
    driver, runner = _driver()
    runner.script(exit_code=1)
    assert driver.compile(_cfg(), tmp_path, tmp_path, None, config="Release") == 1
    assert not scratch.exists()


@pytest.mark.small
def test_ctest_run_hands_the_shuffle_seed_to_the_tests_through_the_environment():
    driver, runner = _driver()
    driver.ctest_run(_cfg(), K_TREE, {"A": "1"}, shuffle_seed=77)
    assert runner.commands[-1].env == {"A": "1", "GTEST_SHUFFLE": "1", "GTEST_RANDOM_SEED": "77"}


@pytest.mark.small
def test_ctest_run_leaves_the_environment_alone_without_a_shuffle_seed():
    driver, runner = _driver()
    driver.ctest_run(_cfg(), K_TREE, {"A": "1"})
    assert runner.commands[-1].env == {"A": "1"}


@pytest.mark.small
def test_ctest_run_hands_the_gtest_filter_to_the_tests_through_the_environment():
    driver, runner = _driver()
    driver.ctest_run(_cfg(), K_TREE, {"A": "1"}, gtest_filter="Small_A.*")
    assert runner.commands[-1].env == {"A": "1", "GTEST_FILTER": "Small_A.*"}
    assert "-R" not in runner.commands[-1].argv
