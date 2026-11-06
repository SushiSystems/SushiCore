# test_diag.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the config and env diagnostics a CLI offers."""

from dataclasses import dataclass, fields
from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.diag import ConfigModule, Diagnostics
from sushicore.diag_memory import InMemoryConfigModule
from sushicore.files_memory import MemoryFiles
from sushicore.profile import ModuleProfile

pytestmark = pytest.mark.small

K_ROOT = Path("module")
K_CONFIG = K_ROOT / "cli" / "config.toml"
K_LOCAL = K_ROOT / "cli" / "config.local.toml"
K_WORKSPACE = Path("ws") / "workspace.toml"


@dataclass
class _Settings:
    cxx: str = ""
    generator: str = "Ninja"
    vcpkg_root: str = ""

    def blas_dir(self, root: Path) -> Path:
        """Return where the sibling checkout sits under *root*."""
        return root / "extern" / "blas"


def _profile(**fields_given) -> ModuleProfile:
    """Return the profile of the module `st`."""
    return ModuleProfile(name="SushiTest", program="st", env_prefix="ST", **fields_given)


def _config_module() -> InMemoryConfigModule:
    """Return a config module over the root, naming the three layers a linked module reads."""
    return InMemoryConfigModule(
        K_ROOT, _Settings, {"cxx": "clang", "generator": "Ninja", "vcpkg_root": "/v"},
        env_overrides={"vcpkg_root": "ST_TEST_VCPKG"},
        sources=[K_CONFIG, K_WORKSPACE, K_LOCAL])


def _diagnostics(files: dict[Path, str] | None = None, *, profile: ModuleProfile | None = None,
                 build_env=None) -> tuple[Diagnostics, RecordingConsole]:
    """Return diagnostics over the in-memory config module and files, and their console."""
    console = RecordingConsole()
    diagnostics = Diagnostics(profile=profile or _profile(), console=console,
                              config=_config_module(), files=MemoryFiles(files),
                              build_env=build_env)
    return diagnostics, console


def _cells(console: RecordingConsole, column: int) -> list[str]:
    """Return the body cells of one column of the first table the console printed."""
    table = console.console.printed[0].objects[0]
    return list(table.columns[column].cells)


def test_env_without_a_build_environment_fails_with_one_line():
    diagnostics, console = _diagnostics()
    assert diagnostics.env_dump() == 1
    assert console.texts("error") == ["st has no build environment to dump."]


def test_env_shows_only_build_relevant_variables_unless_asked():
    diagnostics, console = _diagnostics(build_env=lambda cfg, build_dir: {
        "PATH": "/bin", "UNRELATED_THING": "x"})
    assert diagnostics.env_dump() == 0
    assert console.texts("info") == [
        "1 of 2 variables shown (build-relevant; use --all for everything)"]
    assert _cells(console, 0) == ["PATH"]


def test_env_shows_every_variable_when_asked():
    diagnostics, console = _diagnostics(build_env=lambda cfg, build_dir: {
        "PATH": "/bin", "UNRELATED_THING": "x"})
    assert diagnostics.env_dump(show_all=True) == 0
    assert console.texts("info") == ["2 of 2 variables shown"]
    assert _cells(console, 0) == ["PATH", "UNRELATED_THING"]


def test_env_hands_the_build_environment_the_build_directory_under_the_root():
    diagnostics, console = _diagnostics(build_env=lambda cfg, build_dir: {
        "CMAKE_BINARY_DIR": str(build_dir)})
    diagnostics.env_dump()
    assert _cells(console, 1) == [str(K_ROOT / "build")]


def _source_of(files: dict[Path, str], setting: str, monkeypatch) -> str:
    """Return what the Source column says about *setting* for config files holding *files*."""
    monkeypatch.delenv("ST_TEST_VCPKG", raising=False)
    diagnostics, console = _diagnostics(files)
    diagnostics.config_show()
    return dict(zip(_cells(console, 0), _cells(console, 2)))[setting]


def test_a_value_set_in_the_local_file_names_the_local_file(monkeypatch):
    files = {K_CONFIG: '[tool]\ncxx = "gcc"\n', K_LOCAL: '[tool]\ncxx = "clang"\n'}
    assert _source_of(files, "cxx", monkeypatch) == "config.local.toml"


def test_a_value_from_the_linked_workspace_names_the_workspace(monkeypatch):
    files = {K_CONFIG: '[tool]\ngenerator = "Ninja"\n',
             K_WORKSPACE: '[tool]\ngenerator = "Make"\n'}
    assert _source_of(files, "generator", monkeypatch) == "workspace"


def test_a_value_set_nowhere_is_the_default(monkeypatch):
    files = {K_CONFIG: '[tool]\ncxx = "gcc"\n'}
    assert _source_of(files, "generator", monkeypatch) == "default"


def test_a_value_set_in_the_environment_names_the_variable(monkeypatch):
    monkeypatch.setenv("ST_TEST_VCPKG", "/elsewhere")
    diagnostics, console = _diagnostics({K_CONFIG: '[tool]\nvcpkg_root = "/v"\n'})
    diagnostics.config_show()
    assert dict(zip(_cells(console, 0), _cells(console, 2)))["vcpkg_root"] == "env:ST_TEST_VCPKG"


def test_config_show_lists_the_project_root_and_each_sibling_directory():
    diagnostics, console = _diagnostics(profile=_profile(siblings=("sushiblas",)))
    diagnostics.config_show()
    assert console.texts("info")[:2] == [
        f"Project root  : {K_ROOT}",
        f"sushiblas dir : {K_ROOT / 'extern' / 'blas'}",
    ]


@dataclass
class ConfigWorld:
    """A config module under test and the project root it was built over."""

    module: ConfigModule
    root: Path


class ConfigModuleContract:
    """The promises every :class:`ConfigModule` keeps; a subclass supplies the world.

    No config module of this package implements the port: each CLI writes its own, so the
    contract runs here over the in-memory one and is the model for those.
    """

    @pytest.mark.parametrize("start", [None, Path("somewhere/below")])
    def test_the_project_root_is_found_from_any_start(self, world, start):
        assert world.module.find_project_root(start) == world.root

    def test_the_config_directory_lies_inside_the_project_root(self, world):
        assert world.module.config_dir(world.root).is_relative_to(world.root)

    def test_the_loaded_config_is_an_instance_of_the_config_class(self, world):
        assert isinstance(world.module.load_config(), world.module.Config)

    def test_every_environment_override_names_a_field_of_the_config_class(self, world):
        names = {field.name for field in fields(world.module.Config)}
        assert set(world.module._ENV_OVERRIDES) <= names


class TestInMemoryConfigModuleKeepsTheConfigModuleContract(ConfigModuleContract):
    """The in-memory config module."""

    @pytest.fixture
    def world(self):
        root = Path("project")
        module = InMemoryConfigModule(root, _Settings, {"cxx": "clang"},
                                      env_overrides={"vcpkg_root": "ST_VCPKG"})
        return ConfigWorld(module, root)
