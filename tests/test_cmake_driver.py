"""The driver's whole contract is the argv it produces."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from sushicore.cmake_driver import CMakeDriver


class _Console:
    def __init__(self):
        self.lines = []
        self.console = self

    def command(self, text): self.lines.append(text)
    def error(self, text): self.lines.append(text)
    def info(self, text): self.lines.append(text)
    def warn(self, text): self.lines.append(text)
    def success(self, text): self.lines.append(text)
    def print(self, text, **kw): self.lines.append(text)


class _Runner:
    """Captures argv instead of spawning."""

    def __init__(self):
        self.calls = []

    def resolve_exe(self, name, env=None):
        return name

    def run(self, cmd, cwd, env=None):
        self.calls.append(("run", list(cmd), str(cwd)))
        return 0

    def run_drained(self, cmd, cwd, env=None):
        self.calls.append(("drained", list(cmd), str(cwd)))
        return 0


def _cfg(**kw):
    base = dict(cmake_exe="", ctest_exe="", doxygen_exe="", generator="Ninja")
    base.update(kw)
    base["expand"] = lambda s: s
    return SimpleNamespace(**base)


def _driver():
    runner = _Runner()
    return CMakeDriver(_Console(), runner), runner


def test_cmake_defaults_to_the_bare_name():
    driver, _ = _driver()
    assert driver.cmake(_cfg()) == "cmake"
    assert driver.cmake(_cfg(cmake_exe="C:/tools/cmake.exe")) == "C:/tools/cmake.exe"


def test_compile_builds_the_expected_argv(tmp_path):
    driver, runner = _driver()
    driver.compile(_cfg(), tmp_path, tmp_path, None, config="Release")
    assert runner.calls == [
        ("run", ["cmake", "--build", str(tmp_path), "--config", "Release"],
         str(tmp_path))]


def test_compile_appends_targets_and_jobs(tmp_path):
    driver, runner = _driver()
    driver.compile(_cfg(), tmp_path, tmp_path, None, config="Debug",
                   targets=("editor",), jobs=8)
    assert runner.calls[0][1] == [
        "cmake", "--build", str(tmp_path), "--config", "Debug",
        "--target", "editor", "-j", "8"]


def test_ctest_run_is_drained_and_carries_the_knobs(tmp_path):
    driver, runner = _driver()
    driver.ctest_run(_cfg(), tmp_path, None, label_regex="^unit$",
                     filter="Gemm.*", repeat=3)
    kind, argv, cwd = runner.calls[0]
    assert kind == "drained"
    assert argv == ["ctest", "--test-dir", str(tmp_path), "--output-on-failure",
                    "-L", "^unit$", "-R", "Gemm.*", "--repeat", "until-fail:3"]
    assert cwd == str(tmp_path)


def test_ctest_run_omits_absent_knobs(tmp_path):
    driver, runner = _driver()
    driver.ctest_run(_cfg(), tmp_path, None)
    assert runner.calls[0][1] == ["ctest", "--test-dir", str(tmp_path),
                                  "--output-on-failure"]


def test_needs_configure_when_there_is_no_tree(tmp_path):
    driver, _ = _driver()
    assert driver.needs_configure(tmp_path / "absent", "Ninja") is True


def test_needs_configure_when_the_sentinel_is_missing(tmp_path):
    driver, _ = _driver()
    assert driver.needs_configure(tmp_path, "Ninja") is True


def test_no_reconfigure_when_expectations_hold(tmp_path):
    (tmp_path / "build.ninja").write_text("")
    (tmp_path / "CMakeCache.txt").write_text("CMAKE_BUILD_TYPE:STRING=Release\n")
    driver, _ = _driver()
    assert driver.needs_configure(tmp_path, "Ninja",
                                  expect={"CMAKE_BUILD_TYPE": "Release"}) is False


def test_reconfigure_when_an_expectation_is_violated(tmp_path):
    (tmp_path / "build.ninja").write_text("")
    (tmp_path / "CMakeCache.txt").write_text("CMAKE_BUILD_TYPE:STRING=Release\n")
    driver, _ = _driver()
    assert driver.needs_configure(tmp_path, "Ninja",
                                  expect={"CMAKE_BUILD_TYPE": "Debug"}) is True


def test_clean_tree_says_so_when_there_is_nothing_to_clean(tmp_path):
    console = _Console()
    driver = CMakeDriver(console, _Runner())
    driver.clean_tree(tmp_path / "absent")
    assert any("nothing to clean" in line for line in console.lines)
