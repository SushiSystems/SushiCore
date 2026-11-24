# test_generate_design_views.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the command that writes the generated views of the design topics to disk."""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path


from sushicore.tools.documentation.design_views import read_block  # noqa: E402
from sushicore.tools.documentation.generate_design_views import main  # noqa: E402
from tests.tools.documentation.view_files import K_FILES, write_files  # noqa: E402


class GeneratorTest(unittest.TestCase):
    """Covers the command that writes the views to the files on disk."""
    K_TEST_SIZE = "medium"

    def test_initialises_then_fills_every_block(self) -> None:
        """Adds the markers and writes the three views."""
        with tempfile.TemporaryDirectory() as folder:
            root = write_files(folder, K_FILES)
            self.assertEqual(main([str(root), "--init"]), 0)
            self.assertIn("[AUDIO](AUDIO.md)", read_block((root / "docs/design/README.md").read_text(encoding="utf-8"), "topics") or "")
            self.assertIn("[AUDIO]", read_block((root / "modules/domain/audio/README.md").read_text(encoding="utf-8"), "designs") or "")
            self.assertIn("SPATIALIZER", read_block((root / "docs/design/AUDIO.md").read_text(encoding="utf-8"), "work") or "")

    @staticmethod
    def make_stale(folder: str) -> Path:
        """Initialises the views under a root, makes the topic map stale and returns the root."""
        root = write_files(folder, K_FILES)
        main([str(root), "--init"])
        path = root / "docs/design/README.md"
        path.write_text(path.read_text(encoding="utf-8").replace("The sound the engine makes.", "stale text"), encoding="utf-8")
        return root

    def test_check_exits_one_and_names_a_stale_block(self) -> None:
        """Exits 1 and names the stale block."""
        with tempfile.TemporaryDirectory() as folder:
            root = self.make_stale(folder)
            with contextlib.redirect_stdout(io.StringIO()) as printed:
                code = main([str(root), "--check"])
        self.assertEqual((code, "the block 'topics' is stale" in printed.getvalue()), (1, True))

    def test_check_leaves_a_stale_file_as_it_was(self) -> None:
        """Writes nothing when only checking."""
        with tempfile.TemporaryDirectory() as folder:
            root = self.make_stale(folder)
            with contextlib.redirect_stdout(io.StringIO()):
                main([str(root), "--check"])
            self.assertIn("stale text", (root / "docs/design/README.md").read_text(encoding="utf-8"))

    def test_the_write_repairs_a_stale_block(self) -> None:
        """Writes the view again, so a later check exits 0."""
        with tempfile.TemporaryDirectory() as folder:
            root = self.make_stale(folder)
            main([str(root)])
            self.assertEqual(main([str(root), "--check"]), 0)

    def test_leaves_a_file_without_markers_alone(self) -> None:
        """Does not write into a README that has no markers unless asked to initialise."""
        with tempfile.TemporaryDirectory() as folder:
            root = write_files(folder, K_FILES)
            before = (root / "docs/design/README.md").read_text(encoding="utf-8")
            main([str(root)])
            self.assertEqual((root / "docs/design/README.md").read_text(encoding="utf-8"), before)


if __name__ == "__main__":
    unittest.main()
