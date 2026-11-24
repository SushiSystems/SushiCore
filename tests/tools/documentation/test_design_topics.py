# test_design_topics.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests how a design document is read: its topic name, metadata, phase ids and the work that names it."""

from __future__ import annotations

import unittest


from sushicore.tools.documentation.design_topics import (  # noqa: E402
    loose_documents,
    metadata,
    phase_ids,
    split_reference,
    split_values,
    topic_name,
    topics,
    work_documents,
)
from tests.tools.documentation.view_files import K_FILES, K_TOPIC, tree_of  # noqa: E402


class TestTopics(unittest.TestCase):
    """Covers which topics a tree holds and what each is called."""
    K_TEST_SIZE = "small"

    def test_a_loose_document_is_named_by_its_stem(self) -> None:
        self.assertEqual(topic_name("docs/design/AUDIO.md"), "AUDIO")

    def test_a_split_topic_is_named_by_its_folder(self) -> None:
        self.assertEqual(topic_name("docs/design/AUDIO/README.md"), "AUDIO")

    def test_each_topic_maps_to_its_document_and_the_indexes_are_left_out(self) -> None:
        self.assertEqual(topics(tree_of(K_FILES)), {"AUDIO": "docs/design/AUDIO.md"})

    def test_a_split_topic_maps_to_its_readme(self) -> None:
        tree = tree_of({"docs/design/VIDEO/README.md": K_TOPIC})
        self.assertEqual(topics(tree), {"VIDEO": "docs/design/VIDEO/README.md"})

    def test_loose_documents_are_the_markdown_files_directly_in_design_that_are_no_index(self) -> None:
        tree = tree_of({
            "docs/design/README.md": "# Design\n",
            "docs/design/REMAINING_WORK.md": "# Left\n",
            "docs/design/AUDIO.md": K_TOPIC,
            "docs/design/notes.txt": "x",
            "docs/design/VIDEO/README.md": K_TOPIC,
        })
        self.assertEqual(loose_documents(tree), ["docs/design/AUDIO.md"])


class TestMetadata(unittest.TestCase):
    """Covers the `**Field:** value` lines that follow the status line."""
    K_TEST_SIZE = "small"

    def test_each_field_carries_its_line_number_and_value(self) -> None:
        self.assertEqual(metadata(K_TOPIC), {
            "About": (4, "The sound the engine makes."),
            "Modules": (5, "modules/domain/audio"),
        })

    def test_the_status_line_is_not_a_field(self) -> None:
        self.assertNotIn("Status", metadata(K_TOPIC))

    def test_reading_stops_at_the_first_line_that_is_no_field(self) -> None:
        text = "# T\n\n**Status:** Open — x\n**About:** a\n\nProse.\n**Modules:** late\n"
        self.assertEqual(metadata(text), {"About": (4, "a")})

    def test_a_document_without_fields_has_none(self) -> None:
        self.assertEqual(metadata("# T\n\n**Status:** Open — x\n\n## Problem\n"), {})

    def test_values_split_on_commas_without_code_marks(self) -> None:
        self.assertEqual(split_values("`modules/a`, b ,`c`"), ["modules/a", "b", "c"])

    def test_the_word_none_stands_for_no_value(self) -> None:
        self.assertEqual(split_values("None"), [])
        self.assertEqual(split_values("a, none"), ["a"])


class TestPhases(unittest.TestCase):
    """Covers the phase ids of a document and the references that name them."""
    K_TEST_SIZE = "small"

    def test_each_row_of_the_phase_table_gives_its_id(self) -> None:
        self.assertEqual(phase_ids(K_TOPIC), {"A0", "A1"})

    def test_the_header_row_and_the_rule_row_give_no_id(self) -> None:
        ids = phase_ids(K_TOPIC)
        self.assertNotIn("Id", ids)
        self.assertNotIn("---", ids)

    def test_an_id_loses_its_code_and_bold_marks(self) -> None:
        text = "# T\n\n## Phases\n\n| Id | Phase |\n| --- | --- |\n| **`B1`** | x |\n"
        self.assertEqual(phase_ids(text), {"B1"})

    def test_a_document_without_phases_has_no_ids(self) -> None:
        self.assertEqual(phase_ids("# T\n\n## Problem\n\nNone.\n"), set())

    def test_a_reference_splits_into_its_topic_and_phase(self) -> None:
        self.assertEqual(split_reference("AUDIO#A1"), ("AUDIO", "A1"))

    def test_a_reference_without_a_phase_has_an_empty_one(self) -> None:
        self.assertEqual(split_reference(" AUDIO "), ("AUDIO", ""))


class TestWorkDocuments(unittest.TestCase):
    """Covers which file of each work folder carries its status and metadata."""
    K_TEST_SIZE = "small"

    def test_the_spec_comes_before_the_plan_and_the_report(self) -> None:
        tree = tree_of({
            "docs/agent/2026_01_01_A/PLAN.md": "p",
            "docs/agent/2026_01_01_A/SPEC.md": "s",
            "docs/agent/2026_01_01_A/REPORT.md": "r",
        })
        self.assertEqual(work_documents(tree), ["docs/agent/2026_01_01_A/SPEC.md"])

    def test_a_folder_without_a_spec_falls_back_to_the_next_file(self) -> None:
        tree = tree_of({"docs/agent/2026_01_01_B/REPORT.md": "r", "docs/agent/2026_01_01_B/PLAN.md": "p"})
        self.assertEqual(work_documents(tree), ["docs/agent/2026_01_01_B/PLAN.md"])

    def test_a_folder_with_none_of_the_three_files_is_skipped(self) -> None:
        tree = tree_of({"docs/agent/2026_01_01_C/NOTES.md": "n", "docs/agent/2026_01_02_D/SPEC.md": "s"})
        self.assertEqual(work_documents(tree), ["docs/agent/2026_01_02_D/SPEC.md"])


if __name__ == "__main__":
    unittest.main()
