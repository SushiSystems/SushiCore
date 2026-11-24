# test_release_train.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for walking a release train over fakes of git, the forge and the index."""

from pathlib import Path

import pytest

from sushicore.files_memory import MemoryFiles
from sushicore.release_train.errors import ReleaseTrainError
from sushicore.release_train.release_train import ReleaseTrain
from sushicore.release_train.version import Version

pytestmark = pytest.mark.small

K_ROOT = Path("/w")


class _Git:
    def __init__(self):
        self.log = []
        self.dirty = set()

    def is_clean(self, repo):
        return repo.name not in self.dirty

    def head(self, repo):
        return f"{repo.name}-{sum(1 for entry in self.log if entry[0] == repo.name)}"

    def latest_release(self, repo):
        return Version(0, 5, 1)

    def last_release_files(self, repo):
        return [Path("cli/pyproject.toml"), Path("docs/reference/CHANGELOG.md")]

    def commit_all(self, repo, message):
        self.log.append((repo.name, "commit", message.split("\n", 1)[0]))

    def push(self, repo, *refs):
        self.log.append((repo.name, "push", refs))

    def tag(self, repo, name, commit):
        self.log.append((repo.name, "tag", name, commit))


class _Forge:
    def __init__(self, failing=()):
        self.failing = failing

    def ci_passed(self, repo, commit):
        return repo.name not in self.failing

    def release_passed(self, repo, commit):
        return True


class _Index:
    def wait_for(self, package, version):
        return True


def _library(name, pins=()):
    deps = "".join(f'[sushisystems.{below}]\nversion = "v0.5.1"\ncommit  = "old"\n\n' for below in pins)
    refs = "".join(f"  {below.upper()}_REF: v0.5.1\n" for below in pins)
    return {K_ROOT / name / "cli/sushistack.deps.toml": deps,
            K_ROOT / name / "cli/pyproject.toml": f'[project]\nname = "{name}-cli"\nversion = "0.5.1"\n',
            K_ROOT / name / "docs/reference/CHANGELOG.md": "# Changelog\n\n## Unreleased\n\n- 2026-11-24 — x\n",
            K_ROOT / name / ".github/workflows/ci.yml": "env:\n" + refs}


def _train(failing=()):
    files = MemoryFiles({**_library("log"), **_library("runtime", ["log"])})
    git = _Git()
    train = ReleaseTrain(K_ROOT, files, git, _Forge(failing), _Index(), lambda _line: None, "2026-11-24")
    return train, files, git


def test_a_library_and_the_one_above_it_are_released_in_turn_with_the_pin_moved():
    train, files, git = _train()
    released = train.run(["log"], "patch")
    assert [(entry.name, str(entry.version)) for entry in released] == [("log", "0.5.2"), ("runtime", "0.5.2")]
    deps = files.read_text(K_ROOT / "runtime/cli/sushistack.deps.toml")
    assert 'version = "v0.5.2"' in deps and f'commit  = "{released[0].commit}"' in deps
    assert "LOG_REF: v0.5.2" in files.read_text(K_ROOT / "runtime/.github/workflows/ci.yml")
    assert 'version = "0.5.2"' in files.read_text(K_ROOT / "runtime/cli/pyproject.toml")
    assert [entry[2] for entry in git.log if entry[1] == "commit"] == [
        "chore(release): v0.5.2", "build(deps): pin log v0.5.2", "chore(release): v0.5.2"]
    assert ("log", "tag", "v0.5.2", released[0].commit) in git.log


def test_a_red_ci_stops_the_train_before_the_tag():
    train, _files, git = _train(failing=("log",))
    with pytest.raises(ReleaseTrainError, match="log: CI"):
        train.run(["log"], "patch")
    assert not any(entry[1] == "tag" for entry in git.log)


def test_a_dirty_library_stops_the_train_before_it_changes_anything():
    train, _files, git = _train()
    git.dirty.add("log")
    with pytest.raises(ReleaseTrainError, match="working tree"):
        train.run(["log"], "patch")
    assert git.log == []


def test_the_plan_names_the_train_in_order():
    assert _train()[0].plan(["log"]) == ["log", "runtime"]
