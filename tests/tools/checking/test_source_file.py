# test_source_file.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the file values checker rules read: the line of an offset and reading files from disk."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


from sushicore.tools.checking.source_file import SourceFile, line_of, read_files  # noqa: E402


class TestLineOf(unittest.TestCase):
    """Covers the line number of a character offset."""
    K_TEST_SIZE = "small"

    def test_the_first_character_is_on_line_one(self) -> None:
        self.assertEqual(line_of("ab\ncd\n", 0), 1)

    def test_a_character_after_a_newline_is_on_the_next_line(self) -> None:
        self.assertEqual(line_of("ab\ncd\n", 3), 2)

    def test_the_newline_itself_belongs_to_the_line_it_ends(self) -> None:
        self.assertEqual(line_of("ab\ncd\n", 2), 1)

    def test_an_offset_past_two_newlines_is_on_line_three(self) -> None:
        self.assertEqual(line_of("a\n\nb", 3), 3)


class TestReadFiles(unittest.TestCase):
    """Covers reading the wanted paths of a folder as UTF-8."""
    K_TEST_SIZE = "medium"

    def setUp(self) -> None:
        self._folder = tempfile.TemporaryDirectory()
        self.root = Path(self._folder.name)

    def tearDown(self) -> None:
        self._folder.cleanup()

    def test_each_accepted_path_is_read_with_its_text(self) -> None:
        path = self.root / "a.md"
        path.write_text("hello\n", encoding="utf-8")
        self.assertEqual(read_files([path], lambda _: True), (SourceFile(path, "hello\n"),))

    def test_a_path_the_predicate_refuses_is_not_read(self) -> None:
        keep, skip = self.root / "keep.md", self.root / "skip.txt"
        keep.write_text("k", encoding="utf-8")
        skip.write_text("s", encoding="utf-8")
        found = read_files([skip, keep], lambda path: path.suffix == ".md")
        self.assertEqual([source.path for source in found], [keep])

    def test_a_refused_path_that_does_not_exist_is_never_opened(self) -> None:
        self.assertEqual(read_files([self.root / "missing.txt"], lambda _: False), ())

    def test_bytes_that_do_not_decode_become_the_replacement_character(self) -> None:
        path = self.root / "bad.md"
        path.write_bytes(b"a\xffb")
        self.assertEqual(read_files([path], lambda _: True)[0].text, "a�b")

    def test_the_order_of_the_paths_is_kept(self) -> None:
        paths = [self.root / name for name in ("b.md", "a.md")]
        for path in paths:
            path.write_text("x", encoding="utf-8")
        self.assertEqual([source.path for source in read_files(paths, lambda _: True)], paths)


if __name__ == "__main__":
    unittest.main()
