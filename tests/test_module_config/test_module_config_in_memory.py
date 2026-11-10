# test_module_config_in_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Module config loads from an in-memory environment and files, with no disk."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.config_base import ToolConfig
from sushicore.environment_memory import MemoryEnvironment
from sushicore.errors import ConfigError
from sushicore.files_memory import MemoryFiles
from sushicore.module_config import ModuleConfig
from sushicore.profile import ModuleProfile
from sushicore.workspace import WORKSPACE_MARKER, workspace_file

pytestmark = pytest.mark.small

K_ROOT = Path("mem") / "module"
K_CONFIG = K_ROOT / "cli" / "config.toml"
K_PROFILE = ModuleProfile(name="SushiEngine", program="se", env_prefix="SE")


def test_module_config_loads_every_layer_from_memory():
    home = Path("mem") / "ws"
    files = MemoryFiles({
        K_CONFIG: '[tool]\ncxx = "repo"\ngenerator = "repo"\n',
        workspace_file(home): '[tool]\ngenerator = "shared"\n',
        home / WORKSPACE_MARKER / "keep": "",
    })
    environment = MemoryEnvironment({"SUSHISTACK_HOME": str(home), "SE_NINJA": "from-environment"})
    loaded = ModuleConfig(K_PROFILE).load(ToolConfig, root=K_ROOT, environment=environment,
                                          files=files)
    assert (loaded.cxx, loaded.generator, loaded.ninja_exe) == ("repo", "shared", "from-environment")


def test_a_malformed_module_config_in_memory_raises_a_config_error():
    files = MemoryFiles({K_CONFIG: "[tool\n"})
    with pytest.raises(ConfigError, match="config.toml"):
        ModuleConfig(K_PROFILE, use_workspace_config=False).load(
            ToolConfig, root=K_ROOT, environment=MemoryEnvironment(), files=files)


def test_the_root_is_found_by_walking_up_through_the_files_given():
    files = MemoryFiles({K_ROOT / "CMakeLists.txt": ""})
    found = ModuleConfig(K_PROFILE).find_project_root(K_ROOT / "src" / "deep", files=files)
    assert found == K_ROOT
