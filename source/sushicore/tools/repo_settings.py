# repo_settings.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Loads `tools/settings.py` of the repository being checked and gives its names as this module's.

The repository is the one `SUSHICORE_TOOLS_ROOT` names, else the nearest folder at or above the
working directory that holds `tools/settings.py`.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from types import ModuleType

K_ROOT_VARIABLE = "SUSHICORE_TOOLS_ROOT"
K_SETTINGS = Path("tools") / "settings.py"


def settings_path(start: Path, environ: dict[str, str] | os._Environ[str] = os.environ) -> Path:
    """Return the settings file of the repository *environ* names, or the nearest one at or above *start*.

    Raises ImportError when there is none, naming where it looked.
    """
    named = environ.get(K_ROOT_VARIABLE)
    candidates = [Path(named)] if named else [start, *start.parents]
    for folder in candidates:
        if (folder / K_SETTINGS).is_file():
            return folder / K_SETTINGS
    raise ImportError(f"no {K_SETTINGS.as_posix()} at or above {candidates[0]}; run the tools from a repository")


def _load(path: Path) -> ModuleType:
    """Return the module the file at *path* defines."""
    spec = importlib.util.spec_from_file_location("sushicore_repo_settings", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


globals().update({name: value for name, value in vars(_load(settings_path(Path.cwd().resolve()))).items()
                  if not name.startswith("__")})
