"""The driver's whole contract is the argv it produces."""

from pathlib import Path
from types import SimpleNamespace

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


def test_compile_appends_targets(tmp_path):
    driver, runner = _driver()
    driver.compile(_cfg(), tmp_path, tmp_path, None, config="Debug",
                   targets=("editor",))
    assert runner.calls[0][1] == [
        "cmake", "--build", str(tmp_path), "--config", "Debug",
        "--target", "editor"]


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


# -- root: the stale-source-path check (comparison itself is cmake_cache's) -----
#
# test_cmake_cache.py already pins is_stale's own comparison (case/separator handling,
# an unconfigured tree, etc.). These tests are about needs_configure's wiring of it: that
# passing root turns the check on at all, that it warns when it fires, and that omitting
# root -- what every call site did before this -- leaves an otherwise-fresh tree alone.

def test_root_mismatch_forces_reconfigure_and_warns(tmp_path):
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    (build_dir / "build.ninja").write_text("")
    (build_dir / "CMakeCache.txt").write_text(
        "CMAKE_HOME_DIRECTORY:INTERNAL=/workspace/sushiengine\n")
    console = _Console()
    driver = CMakeDriver(console, _Runner())

    assert driver.needs_configure(build_dir, "Ninja",
                                  root=tmp_path / "sushiengine") is True
    assert any("different source path" in line for line in console.lines)


def test_root_match_does_not_reconfigure_or_warn(tmp_path):
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    (build_dir / "build.ninja").write_text("")
    root = tmp_path / "sushiengine"
    (build_dir / "CMakeCache.txt").write_text(
        f"CMAKE_HOME_DIRECTORY:INTERNAL={root}\n")
    console = _Console()
    driver = CMakeDriver(console, _Runner())

    assert driver.needs_configure(build_dir, "Ninja", root=root) is False
    assert console.lines == []


def test_clean_tree_says_so_when_there_is_nothing_to_clean(tmp_path):
    console = _Console()
    driver = CMakeDriver(console, _Runner())
    driver.clean_tree(tmp_path / "absent")
    assert any("nothing to clean" in line for line in console.lines)


def test_clean_tree_removes_the_directory_it_is_given(tmp_path):
    build = tmp_path / "build"
    (build / "CMakeFiles").mkdir(parents=True)
    (build / "CMakeCache.txt").write_text("")
    driver = CMakeDriver(_Console(), _Runner())
    driver.clean_tree(build)
    assert not build.exists()


def test_clean_tree_removes_only_that_directory(tmp_path):
    """The failure that would matter: removing the parent instead of the tree."""
    sibling = tmp_path / "keep"
    sibling.mkdir()
    build = tmp_path / "build"
    build.mkdir()
    driver = CMakeDriver(_Console(), _Runner())
    driver.clean_tree(build)
    assert not build.exists()
    assert sibling.is_dir()
    assert tmp_path.is_dir()


def _installed_doxygen(tmp_path: Path):
    """A doxygen_exe pointing at a file that exists, so the driver's own
    not-installed check passes and execution reaches the run() call."""
    doxy = tmp_path / "doxygen.exe"
    doxy.write_text("")
    return str(doxy)


def test_doxygen_passes_a_path_relative_to_cwd(tmp_path):
    """The child resolves its argument against cwd; every module hands the driver an
    absolute Doxyfile so its own existence check is robust to being invoked from a
    subdirectory, so the driver must derive the relative form rather than take it."""
    doxyfile = tmp_path / "Doxyfile"
    doxyfile.write_text("")
    doxy = _installed_doxygen(tmp_path)
    driver, runner = _driver()

    driver.doxygen(_cfg(doxygen_exe=doxy), doxyfile, tmp_path, None, install_hint="")

    assert runner.calls == [("run", [doxy, "Doxyfile"], str(tmp_path))]


def test_doxygen_derives_a_nested_relative_path(tmp_path):
    """SushiEngine's Doxyfile lives under .config/doxygen/; the argv must name it the
    same way the module always has, not the absolute path the existence check needs."""
    doxyfile = tmp_path / ".config" / "doxygen" / "Doxyfile"
    doxyfile.parent.mkdir(parents=True)
    doxyfile.write_text("")
    doxy = _installed_doxygen(tmp_path)
    driver, runner = _driver()

    driver.doxygen(_cfg(doxygen_exe=doxy), doxyfile, tmp_path, None, install_hint="")

    assert runner.calls[0][1] == [doxy, ".config/doxygen/Doxyfile"]


def test_doxygen_not_found_names_the_absolute_path():
    """Printed, not spawned, so naming the full path here cannot move the argv."""
    console = _Console()
    driver = CMakeDriver(console, _Runner())
    missing = Path("/project/Doxyfile")

    assert driver.doxygen(_cfg(), missing, Path("/project"), None, install_hint="") == 1
    assert any(str(missing) in line for line in console.lines)


def test_compile_places_parallel_before_targets(tmp_path):
    driver, runner = _driver()
    driver.compile(_cfg(), tmp_path, tmp_path, None, config="Release",
                   targets=["a"], jobs=8)
    assert runner.calls[-1][1] == ["cmake", "--build", str(tmp_path), "--config",
                                   "Release", "--parallel", "8", "--target", "a"]


def test_ctest_run_appends_parallel_and_config_in_order(tmp_path):
    driver, runner = _driver()
    driver.ctest_run(_cfg(), tmp_path, None, filter="S.*", repeat=2, jobs=4,
                     config="Debug")
    assert runner.calls[-1][1] == [
        "ctest", "--test-dir", str(tmp_path), "--output-on-failure", "-R", "S.*",
        "--repeat", "until-fail:2", "--parallel", "4", "-C", "Debug"]


def test_ctest_run_skips_parallel_for_a_single_job(tmp_path):
    driver, runner = _driver()
    driver.ctest_run(_cfg(), tmp_path, None, jobs=1)
    assert "--parallel" not in runner.calls[-1][1]
