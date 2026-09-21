"""Reading a `sushistack.deps.toml` fragment: what a repository says it needs.

A fragment is one table per dependency, keyed by its name, plus a reserved
``[module]`` table carrying metadata rather than a dependency. Several CLIs read
the format, so it is read here once: two readers of one file is how a required
dependency goes missing without a word, which is what happened to sushidsp's
fragment until 2026-09-22.

This module reads and reports. It runs no package manager: whether a package is
installed is a question only a package manager answers, and which one to ask is
the caller's world, not this library's. What it answers is what the file says,
which command would satisfy an entry on a given platform, and -- when an entry
declares a ``check_cmd`` -- whether that check passes.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib


#: Reserved table name carrying module metadata rather than a dependency.
MODULE_TABLE = "module"

#: The platform string that selects the vcpkg column; anything else selects apt.
WINDOWS = "windows"


class Status(str, Enum):
    """What is known about one dependency on this machine."""

    #: Its ``check_cmd`` ran and exited 0.
    SATISFIED = "satisfied"
    #: It names no package for this platform, so there is nothing to install.
    NOT_APPLICABLE = "not applicable"
    #: It names a package and nothing here can say whether it is installed.
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Dependency:
    """One entry of a fragment, as the file declares it."""

    name: str
    description: str = ""
    required: bool = True
    gpu_only: bool = False
    linux_apt: list[str] = field(default_factory=list)
    windows_vcpkg: list[str] = field(default_factory=list)
    check_cmd: list[str] = field(default_factory=list)
    provides: str = ""

    def packages_for(self, platform: str) -> list[str]:
        """Package names for *platform*: the vcpkg ports on Windows, apt elsewhere."""
        return self.windows_vcpkg if platform == WINDOWS else self.linux_apt


@dataclass(frozen=True)
class Fragment:
    """What one fragment file declares."""

    dependencies: list[Dependency]
    depends_on: list[str]


def read(path: Path) -> Fragment:
    """Read the fragment at *path*.

    Args:
        path: A ``sushistack.deps.toml`` file.

    Returns:
        Its dependencies in file order, and the modules its ``[module]`` table
        says it builds on.

    Raises:
        ValueError: A top-level key holds something other than a table. An array
            of ``[[dependency]]`` tables reads as a list here, and skipping it is
            how a fragment goes unread; the shape is named rather than ignored.
    """
    with path.open("rb") as handle:
        document = tomllib.load(handle)

    depends_on: list[str] = []
    dependencies: list[Dependency] = []
    for name, table in document.items():
        if not isinstance(table, dict):
            raise ValueError(
                f"{path}: '{name}' is a {type(table).__name__}, and a fragment declares one "
                f"table per dependency. An array of [[{name}]] tables reads as a list here, "
                f"and a reader that skips it loses everything the file declared.")
        if name == MODULE_TABLE:
            depends_on = [str(module) for module in table.get("depends_on", [])]
            continue
        dependencies.append(Dependency(
            name=name,
            description=str(table.get("description", "")),
            required=bool(table.get("required", True)),
            gpu_only=bool(table.get("gpu_only", False)),
            linux_apt=[str(p) for p in table.get("linux_apt", [])],
            windows_vcpkg=[str(p) for p in table.get("windows_vcpkg", [])],
            check_cmd=[str(part) for part in table.get("check_cmd", [])],
            provides=str(table.get("provides", "")),
        ))
    return Fragment(dependencies, depends_on)


def status(dep: Dependency, platform: str) -> Status:
    """Report what is known about *dep* on this machine.

    A ``check_cmd`` that exits 0 settles it. Without one, an entry naming no
    package for *platform* has nothing to install and the rest is unknown here,
    because answering it means asking a package manager.

    Args:
        dep: The dependency to ask about.
        platform: ``"windows"`` or anything else, which means the apt column.
    """
    if dep.check_cmd:
        try:
            probe = subprocess.run(dep.check_cmd, capture_output=True)
        except OSError:
            return Status.UNKNOWN
        return Status.SATISFIED if probe.returncode == 0 else Status.UNKNOWN
    if not dep.packages_for(platform):
        return Status.NOT_APPLICABLE
    return Status.UNKNOWN


def install_command(dep: Dependency, platform: str, *, vcpkg: str = "vcpkg",
                    triplet: str = "") -> list[str] | None:
    """The command that installs *dep*, or None when it names no package.

    The caller runs it, or prints it and stops. Nothing here runs anything.

    Args:
        dep: The dependency to install.
        platform: ``"windows"`` or anything else, which means apt.
        vcpkg: The vcpkg executable to name on Windows; the caller knows where
            its own tree is, and this library does not.
        triplet: The vcpkg triplet to append to each port, when the caller pins
            one.
    """
    packages = dep.packages_for(platform)
    if not packages:
        return None
    if platform == WINDOWS:
        ports = [f"{p}:{triplet}" if triplet else p for p in packages]
        return [vcpkg, "install", *ports]
    return ["sudo", "apt-get", "install", "-y", *packages]
