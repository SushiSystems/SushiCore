# test_check_sushicore_pin.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the sushicore pin checker on repositories written to a temporary folder."""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from checking.check_sushicore_pin import K_CHECKER  # noqa: E402
from checking.checker import run  # noqa: E402


class SushicorePinTest(unittest.TestCase):
    """Runs the checker's command line over a repository built for each case."""

    K_TEST_SIZE = "small"

    def setUp(self) -> None:
        """Makes an empty repository folder that the test deletes afterwards."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)

    def _check(self, requirement: str) -> tuple[int, str]:
        """Writes cli/pyproject.toml requiring *requirement*, runs the checker, returns code and output."""
        target = self.root / "cli" / "pyproject.toml"
        target.parent.mkdir(parents=True)
        target.write_text(f'[project]\nname = "x"\ndependencies = ["typer>=0.9", "{requirement}"]\n', encoding="utf-8")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = run(K_CHECKER, [str(self.root)])
        return code, output.getvalue()

    def test_a_lower_bound_alone_passes(self) -> None:
        self.assertEqual(self._check("sushicore>=0.17.1"), (0, ""))

    def test_an_upper_bound_fails(self) -> None:
        code, output = self._check("sushicore>=0.16.2,<0.17")
        self.assertEqual(code, 1)
        self.assertIn("rule_no_upper_bound", output)

    def test_a_compatible_release_or_exact_pin_fails(self) -> None:
        self.assertEqual(self._check("sushicore~=0.17")[0], 1)

    def test_another_package_with_an_upper_bound_is_not_judged(self) -> None:
        self.assertEqual(self._check("sushicorex<2")[0], 0)


if __name__ == "__main__":
    unittest.main()
