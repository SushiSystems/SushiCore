# release_train.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Releases a chain of libraries in dependency order: pin what moved below, bump, wait, tag, wait."""

from __future__ import annotations

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import final

from ..files import Files
from .changelog_section import close_changelog
from .errors import ReleaseTrainError
from .library_graph import K_PINS_FILE, LibraryGraph
from .pin_text import pin_in_deps, pin_in_workflow
from .ports import IForge, IGit, IPackageIndex
from .version import Version
from .version_text import bump_text

K_CHANGELOG = Path("docs/reference/CHANGELOG.md")
K_PROJECT = Path("cli/pyproject.toml")
K_WORKFLOWS = Path(".github/workflows")


@final
@dataclass(frozen=True, slots=True)
class Released:
    """One library the train released: its version and the commit its tag names."""

    name: str
    version: Version
    commit: str


@final
class ReleaseTrain:
    """Walks the train of a workspace one library at a time and stops at the first failure.

    Args:
        workspace: The folder that holds each library as a sibling.
        files: Reads and writes the files of the libraries.
        git: The git operations.
        forge: Waits for the CI and release workflows.
        index: Waits for a CLI on the package index.
        report: Receives one line per step.
        date: The date the changelog sections carry, YYYY-MM-DD.
    """

    def __init__(self, workspace: Path, files: Files, git: IGit, forge: IForge, index: IPackageIndex,
                 report: Callable[[str], None], date: str) -> None:
        self._workspace = workspace
        self._files = files
        self._git = git
        self._forge = forge
        self._index = index
        self._report = report
        self._date = date

    def plan(self, changed: list[str]) -> list[str]:
        """Return the libraries a release of *changed* takes, in the order the train walks them."""
        return LibraryGraph.read(self._workspace, self._files).train(changed)

    def run(self, changed: list[str], part: str) -> list[Released]:
        """Release *changed*, raising *part* of their version, and a patch of every library above them."""
        graph = LibraryGraph.read(self._workspace, self._files)
        released: dict[str, Released] = {}
        for name in graph.train(changed):
            moved = [released[below] for below in sorted(graph.pins[name]) if below in released]
            released[name] = self._release(name, part if name in changed else "patch", moved)
        return list(released.values())

    def _release(self, name: str, part: str, moved: list[Released]) -> Released:
        repo = self._workspace / name
        if not self._git.is_clean(repo):
            raise ReleaseTrainError(f"{name}: the working tree has changes; commit or remove them first")
        if moved:
            self._pin(repo, moved)
            self._git.commit_all(repo, "build(deps): pin " + ", ".join(f"{m.name} {m.version.tag}" for m in moved)
                                 + "\n\nBacklog: none (release train)\n")
        old = self._git.latest_release(repo)
        new = old.next(part)
        self._report(f"{name}: {old.tag} -> {new.tag}")
        for path in self._git.last_release_files(repo):
            target = repo / path
            if path != K_CHANGELOG and self._files.is_file(target):
                self._files.write_text(target, bump_text(self._files.read_text(target), old, new))
        note = ("deps: Pinned " + ", ".join(f"{m.name} {m.version}" for m in moved)
                + f" (`{K_PINS_FILE.as_posix()}`).") if moved else None
        changelog = repo / K_CHANGELOG
        self._files.write_text(changelog, close_changelog(self._files.read_text(changelog), new, self._date,
                                                          (note,) if note else ()))
        self._git.commit_all(repo, f"chore(release): {new.tag}\n\nBacklog: none (release)\n")
        commit = self._git.head(repo)
        self._git.push(repo)
        self._wait(name, "CI", self._forge.ci_passed(repo, commit))
        self._git.tag(repo, new.tag, commit)
        self._git.push(repo, new.tag)
        self._wait(name, "the release workflow", self._forge.release_passed(repo, commit))
        self._wait(name, "the package index", self._index.wait_for(self._package(repo), new))
        self._report(f"{name}: {new.tag} released at {commit[:12]}")
        return Released(name, new, commit)

    def _pin(self, repo: Path, moved: list[Released]) -> None:
        """Point the pins file and the workflows of *repo* at the new tags of *moved*."""
        workflows = repo / K_WORKFLOWS
        targets = [repo / K_PINS_FILE]
        if self._files.is_dir(workflows):
            targets.extend(path for path in self._files.children(workflows) if path.suffix == ".yml")
        for path in targets:
            text = self._files.read_text(path)
            for below in moved:
                text = (pin_in_deps(text, below.name, below.version, below.commit) if path.name.endswith(".toml")
                        else pin_in_workflow(text, below.name, below.version))
            self._files.write_text(path, text)

    def _package(self, repo: Path) -> str:
        """Return the name the CLI of *repo* is published under."""
        return str(tomllib.loads(self._files.read_text(repo / K_PROJECT))["project"]["name"])

    def _wait(self, name: str, what: str, passed: bool) -> None:
        if not passed:
            raise ReleaseTrainError(f"{name}: {what} did not pass; the train stops here")
