# check_sushicore_pin.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Checks that a repository requires sushicore with a lower bound only.

An upper bound makes every SushiCore release force a release of the repository, and two CLIs
installed side by side fail when their bounds do not meet.

Usage: python -m sushicore.tools.checking.check_sushicore_pin [repository root] [--report] [--rule NAME]
"""

from __future__ import annotations

import re
import sys
try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path


from sushicore.tools.checking.checker import Checker, Issue, run  # noqa: E402

K_PROJECT_FILES = (Path("cli/pyproject.toml"), Path("pyproject.toml"))
K_REQUIREMENT = re.compile(r"^\s*sushicore(?![A-Za-z0-9_.-])\s*(?:\[[^\]]*\])?\s*(?P<spec>[^;]*)")
K_UPPER = re.compile(r"(<|<=|==|~=|===)\s*[0-9]")


@dataclass(frozen=True, slots=True)
class ProjectFile:
    """Holds one pyproject.toml and the dependency strings it declares."""

    path: Path
    dependencies: tuple[str, ...]


def _read(path: Path) -> ProjectFile | None:
    """Returns the project file at *path* with its dependencies, or None when it is not one."""
    if not path.is_file():
        return None
    try:
        project = tomllib.loads(path.read_text(encoding="utf-8")).get("project", {})
    except tomllib.TOMLDecodeError:
        return None
    dependencies = project.get("dependencies", [])
    return ProjectFile(path, tuple(item for item in dependencies if isinstance(item, str)))


def collect(paths: list[Path]) -> Iterable[ProjectFile]:
    """Returns the project files of each repository root given."""
    roots = [path if path.is_dir() else path.parent for path in paths]
    return [found for root in roots for name in K_PROJECT_FILES if (found := _read(root / name)) is not None]


def rule_no_upper_bound(project: ProjectFile) -> Iterator[Issue]:
    """Yields an issue when the sushicore requirement caps or fixes the version."""
    for dependency in project.dependencies:
        match = K_REQUIREMENT.match(dependency)
        if match is not None and K_UPPER.search(match.group("spec")):
            yield Issue(project.path, 1, f"'{dependency}' bounds sushicore from above; keep the lower bound only")


K_CHECKER = Checker(
    description="Checks that sushicore is required with a lower bound only.",
    collect=collect,
    rules={"rule_no_upper_bound": rule_no_upper_bound},
)

if __name__ == "__main__":
    sys.exit(run(K_CHECKER))
