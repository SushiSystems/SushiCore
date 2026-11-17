# deps_fragment.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Reads a `sushistack.deps.toml` fragment and reports what a repository needs.

The reasoning is in docs/architecture/OVERVIEW.md, section `deps_fragment`.
"""

from __future__ import annotations

import re
import warnings
from pathlib import Path

from .fragment_types import (  # noqa: F401  re-exported: callers import these from here
    WINDOWS,
    Dependency,
    Download,
    Fragment,
    Status,
    SushiPin,
)
from .proc import CommandRunner
from .quiet_runner import quiet_runner

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib


#: Reserved table name carrying module metadata rather than a dependency.
MODULE_TABLE = "module"

#: Reserved table holding one ``[sushisystems.<name>]`` pin per Sushi library the module links.
SUSHI_TABLE = "sushisystems"

#: The table's deprecated name, read as :data:`SUSHI_TABLE` with a ``DeprecationWarning``.
K_DEPRECATED_SUSHI_TABLE = "sushi"

#: The shape of a full git commit hash.
K_COMMIT_HEX = re.compile(r"[0-9a-f]{40}")

#: The platforms a ``sha256`` table may pin a download for.
K_DIGEST_PLATFORMS = (WINDOWS, "linux")

#: The shape of a SHA-256 written as hex.
K_SHA256_HEX = re.compile(r"[0-9a-f]{64}")


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
            Or an entry's ``sha256`` is not a table of platform to hex digest, its ``url`` is
            not a table of platform to address, or its ``version`` is not a string. Or an entry
            declares one of ``version``, ``url`` and ``sha256`` without the other two, or its
            ``url`` and ``sha256`` name different platforms.
            Or a ``[sushisystems.<name>]`` pin is malformed or names a module
            ``depends_on`` does not, or the file holds the pins under both table names. Or ``[module] cli`` is not a
            string, or ``[module] package_exclude`` is not a list of strings. A module in ``depends_on`` may go unpinned; it is then never
            fetched.
    """
    with path.open("rb") as handle:
        document = tomllib.load(handle)

    depends_on: list[str] = []
    cli = ""
    package_exclude: list[str] = []
    pins: list[SushiPin] = []
    dependencies: list[Dependency] = []
    if SUSHI_TABLE in document and K_DEPRECATED_SUSHI_TABLE in document:
        raise ValueError(
            f"{path}: the pins sit under both [{SUSHI_TABLE}.<name>] and "
            f"[{K_DEPRECATED_SUSHI_TABLE}.<name>]; keep [{SUSHI_TABLE}.<name>] alone.")
    for name, table in document.items():
        if not isinstance(table, dict):
            raise ValueError(
                f"{path}: '{name}' is a {type(table).__name__}, and a fragment declares one "
                f"table per dependency. An array of [[{name}]] tables reads as a list here, "
                f"and a reader that skips it loses everything the file declared.")
        if name == MODULE_TABLE:
            depends_on = [str(module) for module in table.get("depends_on", [])]
            cli = _read_text(path, "cli", table.get("cli", ""))
            package_exclude = _read_texts(path, "package_exclude", table.get("package_exclude", []))
            continue
        if name in (SUSHI_TABLE, K_DEPRECATED_SUSHI_TABLE):
            if name == K_DEPRECATED_SUSHI_TABLE:
                warnings.warn(
                    f"{path}: [{K_DEPRECATED_SUSHI_TABLE}.<name>] is deprecated; rename the pin "
                    f"tables [{SUSHI_TABLE}.<name>].", DeprecationWarning, stacklevel=2)
            pins = [_read_pin(path, pin_name, pin) for pin_name, pin in table.items()]
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
            sha256=_read_digests(path, name, table.get("sha256", {})),
            version=_read_version(path, name, table.get("version", "")),
            url=_read_urls(path, name, table.get("url", {})),
        ))
        _require_whole_download(path, dependencies[-1], table)
    _match_pins(path, depends_on, pins)
    return Fragment(dependencies, depends_on, pins, cli, package_exclude)


def read_present(path: Path) -> Fragment | None:
    """Read the fragment at *path*, or return None when there is no file there.

    Raises:
        ValueError: As :func:`read`.
    """
    return read(path) if path.is_file() else None


def pins_at(path: Path) -> list[SushiPin]:
    """Return the pins of the fragment at *path*, none when there is no file there.

    Raises:
        ValueError: As :func:`read`.
    """
    fragment = read_present(path)
    return fragment.pins if fragment is not None else []


def _read_pin(path: Path, name: str, value: object) -> SushiPin:
    """Return the pin ``[sushisystems.<name>]`` declares.

    Raises:
        ValueError: *value* is not a table, ``version`` is empty, or ``commit`` is
            not 40 hex digits.
    """
    if not isinstance(value, dict):
        raise ValueError(
            f"{path}: {SUSHI_TABLE}.{name} is a {type(value).__name__}, and it is a table such as "
            f"{{ version = \"v1.0.0\", commit = \"<40 hex digits>\" }}.")
    version = value.get("version", "")
    commit = value.get("commit", "")
    if not isinstance(version, str) or not version:
        raise ValueError(
            f"{path}: {SUSHI_TABLE}.{name} has no version; it is the release tag to fetch.")
    if not isinstance(commit, str) or not K_COMMIT_HEX.fullmatch(commit.lower()):
        raise ValueError(
            f"{path}: commit of {SUSHI_TABLE}.{name} is {commit!r}, and a commit is the full "
            f"40-hex hash the tag {version} points at.")
    return SushiPin(name, version, commit.lower())


def _read_text(path: Path, key: str, value: object) -> str:
    """Return the string a ``[module]`` key holds.

    Raises:
        ValueError: *value* is not a string.
    """
    if not isinstance(value, str):
        raise ValueError(
            f"{path}: [{MODULE_TABLE}] {key} is a {type(value).__name__}, and it is a string.")
    return value


def _read_texts(path: Path, key: str, value: object) -> list[str]:
    """Return the list of strings a ``[module]`` key holds.

    Raises:
        ValueError: *value* is not a list of strings.
    """
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(
            f"{path}: [{MODULE_TABLE}] {key} is {value!r}, and it is a list of strings.")
    return list(value)


def _match_pins(path: Path, depends_on: list[str], pins: list[SushiPin]) -> None:
    """Check that every pin names a module in *depends_on*.

    Raises:
        ValueError: A pin names a module *depends_on* does not; the message names it.
    """
    unlisted = sorted({pin.name for pin in pins} - set(depends_on))
    if unlisted:
        raise ValueError(
            f"{path}: [{SUSHI_TABLE}.<name>] pins {', '.join(unlisted)}, which depends_on does not "
            f"name; add it to depends_on or remove the pin.")


def _read_digests(path: Path, name: str, value: object) -> dict[str, str]:
    """Return the ``sha256`` table of the entry *name* with each digest in lower case.

    Raises:
        ValueError: *value* is not a table, names a platform outside
            :data:`K_DIGEST_PLATFORMS`, or holds something other than 64 hex digits.
    """
    if not isinstance(value, dict):
        raise ValueError(
            f"{path}: sha256 of '{name}' is a {type(value).__name__}, and it is a table "
            f"of platform to digest, such as {{ windows = \"<64 hex digits>\" }}.")
    digests: dict[str, str] = {}
    for platform, digest in value.items():
        if platform not in K_DIGEST_PLATFORMS:
            raise ValueError(
                f"{path}: sha256 of '{name}' names the platform '{platform}'; "
                f"the platforms are {', '.join(K_DIGEST_PLATFORMS)}.")
        if not isinstance(digest, str) or not K_SHA256_HEX.fullmatch(digest.lower()):
            raise ValueError(
                f"{path}: sha256 of '{name}' for {platform} is {digest!r}, "
                f"and a SHA-256 is 64 hex digits.")
        digests[platform] = digest.lower()
    return digests


def _read_version(path: Path, name: str, value: object) -> str:
    """Return the ``version`` of the entry *name*.

    Raises:
        ValueError: *value* is not a string.
    """
    if not isinstance(value, str):
        raise ValueError(
            f"{path}: version of '{name}' is a {type(value).__name__}, and it is a string.")
    return value


def _read_urls(path: Path, name: str, value: object) -> dict[str, str]:
    """Return the ``url`` table of the entry *name*.

    Raises:
        ValueError: *value* is not a table, names a platform outside
            :data:`K_DIGEST_PLATFORMS`, or holds something other than a non-empty string.
    """
    if not isinstance(value, dict):
        raise ValueError(
            f"{path}: url of '{name}' is a {type(value).__name__}, and it is a table "
            f"of platform to address, such as {{ windows = \"https://...\" }}.")
    for platform, address in value.items():
        if platform not in K_DIGEST_PLATFORMS:
            raise ValueError(
                f"{path}: url of '{name}' names the platform '{platform}'; "
                f"the platforms are {', '.join(K_DIGEST_PLATFORMS)}.")
        if not isinstance(address, str) or not address.startswith("https://"):
            raise ValueError(
                f"{path}: url of '{name}' for {platform} is {address!r}, "
                f"and it is an https address.")
    return dict(value)


def _require_whole_download(path: Path, dep: Dependency, table: dict) -> None:
    """Check that an entry declaring part of a download declares all of it.

    Raises:
        ValueError: *dep* declares some of ``version``, ``url`` and ``sha256`` and not the
            rest, or its ``url`` and ``sha256`` name different platforms.
    """
    declared = [key for key in ("version", "url", "sha256") if key in table]
    if not declared:
        return
    missing = [key for key in ("version", "url", "sha256") if key not in table]
    if missing or not dep.version or not dep.url or not dep.sha256:
        absent = missing or [key for key in declared if not getattr(dep, key)]
        raise ValueError(
            f"{path}: download '{dep.name}' lacks {' and '.join(absent)}; a download "
            f"declares version, url and sha256 together.")
    if set(dep.url) != set(dep.sha256):
        raise ValueError(
            f"{path}: download '{dep.name}' has url for {', '.join(sorted(dep.url))} but "
            f"sha256 for {', '.join(sorted(dep.sha256))}; each platform needs both.")


def status(dep: Dependency, platform: str, runner: CommandRunner | None = None) -> Status:
    """Report what is known about *dep* on this machine.

    A ``check_cmd`` that exits 0 settles it. Without one, an entry naming no
    package for *platform* has nothing to install and the rest is unknown here,
    because answering it means asking a package manager.

    Args:
        dep: The dependency to ask about.
        platform: ``"windows"`` or anything else, which means the apt column.
        runner: Runs the check command; the real one when None.
    """
    if dep.check_cmd:
        try:
            code, _, _ = (runner if runner is not None else quiet_runner()).capture(dep.check_cmd)
        except OSError:
            return Status.UNKNOWN
        return Status.SATISFIED if code == 0 else Status.UNKNOWN
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
