# test_pre_commit.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that the pre-commit hook checks the index and not the disk, on a real repository with a stub for check_all."""

from __future__ import annotations

import contextlib
import io
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from hooks import pre_commit  # noqa: E402
from repo_builder import Repo, without_commit_dates  # noqa: E402

K_STUB = """import os
import sys
from pathlib import Path

root = Path(sys.argv[1])
with open(os.environ["PRE_COMMIT_TEST_LOG"], "a", encoding="utf-8") as log:
    log.write(str(root) + "\\n")
sys.exit(1 if (root / "bad.txt").exists() else 0)
"""


class PreCommitTest(unittest.TestCase):
    """Runs the hook with a check_all that fails when `bad.txt` exists in the folder it is given."""

    K_TEST_SIZE = "medium"

    def setUp(self) -> None:
        self.repo = Repo()
        self.addCleanup(self.repo.close)
        self.log = self.repo.root.parent / f"{self.repo.root.name}_checked.log"
        self.addCleanup(lambda: self.log.unlink(missing_ok=True))
        self.repo.write("tools/check_all.py", K_STUB)
        self.repo.write("src/a.py", "x = 1\n")
        self.repo.commit("first")

    def _run(self) -> int:
        environment = {**without_commit_dates(), "PRE_COMMIT_TEST_LOG": str(self.log)}
        for name in pre_commit_git_variables():
            environment.pop(name, None)
        with contextlib.redirect_stderr(io.StringIO()):
            return pre_commit.run(self.repo.root, environment)

    def _checked_folders(self) -> list[Path]:
        return [Path(line) for line in self.log.read_text(encoding="utf-8").splitlines()]

    def test_a_red_file_on_disk_that_is_not_staged_does_not_refuse_the_commit(self) -> None:
        self.repo.write("src/a.py", "x = 2\n")
        self.repo.git("add", "src/a.py")
        self.repo.write("bad.txt", "unfinished work of another session\n")
        self.assertEqual(self._run(), 0)

    def test_a_red_file_the_commit_holds_refuses_it_even_when_the_disk_copy_is_fixed(self) -> None:
        self.repo.write("bad.txt", "staged\n")
        self.repo.git("add", "bad.txt")
        self.repo.remove("bad.txt")
        self.assertEqual(self._run(), 1)

    def test_a_red_file_taken_out_of_the_index_but_left_on_disk_does_not_refuse_the_commit(self) -> None:
        self.repo.write("bad.txt", "tracked\n")
        self.repo.commit("add it")
        self.repo.git("rm", "--cached", "bad.txt")
        self.assertEqual(self._run(), 0)

    def test_the_checks_run_in_a_folder_that_is_gone_afterwards_and_is_not_the_repository(self) -> None:
        self.repo.write("src/a.py", "x = 2\n")
        self.repo.git("add", "src/a.py")
        self._run()
        [folder] = self._checked_folders()
        self.assertNotEqual((folder.exists(), folder == self.repo.root), (True, True))
        self.assertFalse(folder.exists())

    def test_a_folder_that_is_no_repository_is_refused(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()) as errors:
            code = pre_commit.run(self.repo.root.parent / "no_such_repository", {"PATH": os.environ["PATH"]})
        self.assertEqual((code, "not a git repository" in errors.getvalue()), (1, True))

    def test_the_index_git_hands_the_hook_is_the_one_checked(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=False):
            git_dir = Path(self.repo.git("rev-parse", "--absolute-git-dir").strip())
        self.assertEqual(pre_commit.index_file(git_dir, {}), git_dir / "index")
        self.assertEqual(pre_commit.index_file(git_dir, {"GIT_INDEX_FILE": str(git_dir / "next-index")}),
                         git_dir / "next-index")


def pre_commit_git_variables() -> tuple[str, ...]:
    """Returns the variables that would point git at the repository that runs the tests."""
    return ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX")


if __name__ == "__main__":
    unittest.main()
