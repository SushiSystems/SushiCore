# test_index_tree.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that the index tree holds what the index holds and links the rest of the working tree."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from sushicore.tools.hooks.index_tree import (  # noqa: E402
    K_OWNER_FILE,
    IndexTree,
    differing_files,
    outermost,
    tree_prefix,
)
from tests.tools.repo_builder import Repo, without_commit_dates  # noqa: E402


class IndexTreeTest(unittest.TestCase):
    """Writes the tree of a repository with one committed file beside the repository."""

    K_TEST_SIZE = "medium"

    def setUp(self) -> None:
        parent = tempfile.TemporaryDirectory()
        self.addCleanup(parent.cleanup)
        self.repo = Repo(Path(parent.name))
        self.addCleanup(self.repo.close)
        self.repo.write("src/a.py", "x = 1\n")
        self.repo.write("src/b.py", "y = 1\n")
        self.repo.commit("first")
        self.environ = without_commit_dates()
        for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX"):
            self.environ.pop(name, None)

    def _write(self, tree: IndexTree) -> Path:
        differing = differing_files(self.repo.root, self.environ) or []
        self.assertIsNone(tree.write(differing))
        assert tree.path is not None
        return tree.path

    def test_a_file_that_differs_holds_the_index_bytes(self) -> None:
        self.repo.write("src/a.py", "x = 2\n")
        with IndexTree(self.repo.root, self.environ) as tree:
            text = (self._write(tree) / "src" / "a.py").read_text(encoding="utf-8")
        self.assertEqual(text, "x = 1\n")

    def test_a_file_that_equals_the_index_is_a_copy_apart_from_the_disk_file(self) -> None:
        self.repo.write("src/a.py", "x = 2" + chr(10))
        with IndexTree(self.repo.root, self.environ) as tree:
            copy = self._write(tree) / "src" / "b.py"
            found = (copy.read_text(encoding="utf-8"),
                     os.path.samefile(copy, self.repo.root / "src" / "b.py"))
        self.assertEqual(found, ("y = 1" + chr(10), False))

    def test_an_ignored_folder_is_reached_through_a_link(self) -> None:
        self.repo.write(".gitignore", "out/" + chr(10))
        self.repo.commit("ignore")
        self.repo.write("out/log.txt", "kept" + chr(10))
        self.repo.write("src/a.py", "x = 2" + chr(10))
        with IndexTree(self.repo.root, self.environ) as tree:
            text = (self._write(tree) / "out" / "log.txt").read_text(encoding="utf-8")
        self.assertEqual((text, (self.repo.root / "out" / "log.txt").is_file()),
                         ("kept" + chr(10), True))

    def test_the_tree_is_gone_after_the_block(self) -> None:
        self.repo.write("src/a.py", "x = 2\n")
        with IndexTree(self.repo.root, self.environ) as tree:
            path = self._write(tree)
        self.assertEqual((path.exists(), tree.problems), (False, []))

    def test_a_folder_that_names_no_owner_is_left_alone(self) -> None:
        other = self.repo.root.parent / f"{tree_prefix(self.repo.root)}x"
        other.mkdir()
        with IndexTree(self.repo.root, self.environ) as tree:
            self._write(tree)
        self.assertTrue(other.is_dir())

    def test_a_tree_of_another_repository_is_left_alone(self) -> None:
        other = self.repo.root.parent / f"{tree_prefix(self.repo.root)}x"
        other.mkdir()
        (other / K_OWNER_FILE).write_text(f"{self.repo.root.parent / 'other'}\n", encoding="utf-8")
        with IndexTree(self.repo.root, self.environ) as tree:
            self._write(tree)
        self.assertTrue(other.is_dir())

    def test_a_tree_an_earlier_commit_left_is_removed(self) -> None:
        stale = self.repo.root.parent / f"{tree_prefix(self.repo.root)}stale"
        (stale / "src").mkdir(parents=True)
        (stale / "src" / "a.py").write_text("old\n", encoding="utf-8")
        (stale / K_OWNER_FILE).write_text(f"{self.repo.root.resolve()}\n", encoding="utf-8")
        with IndexTree(self.repo.root, self.environ) as tree:
            self._write(tree)
        self.assertFalse(stale.exists())

    def test_the_removed_tree_leaves_the_working_tree_whole(self) -> None:
        self.repo.write("src/a.py", "x = 2\n")
        with IndexTree(self.repo.root, self.environ) as tree:
            self._write(tree)
        self.assertEqual((self.repo.root / "src" / "b.py").read_text(encoding="utf-8"), "y = 1\n")



class OutermostTest(unittest.TestCase):
    """Reads the ignored paths git lists."""

    K_TEST_SIZE = "small"

    def test_the_files_and_folders_inside_an_ignored_folder_are_dropped(self) -> None:
        listed = [".cache/", ".cache/.gitignore", ".cache/v/", "notes.log", "out/"]
        self.assertEqual(outermost(listed), [".cache/", "notes.log", "out/"])

if __name__ == "__main__":
    unittest.main()
