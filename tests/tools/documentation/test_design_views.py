# test_design_views.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the generated views of the design topics, rendered from the texts of a tree."""

from __future__ import annotations

import unittest


from sushicore.tools.documentation.design_views import (  # noqa: E402
    expected_blocks,
    insert_block,
    modules_with_designs,
    read_block,
    render_module_designs,
    render_topic_map,
    render_topic_work,
    state_of,
    write_block,
)
from tests.tools.documentation.view_files import K_FILES, K_TOPIC, tree_of  # noqa: E402


class RenderTest(unittest.TestCase):
    """Covers the text of each view, rendered from the texts of a tree."""
    K_TEST_SIZE = "small"

    def test_renders_the_topic_map(self) -> None:
        """Lists each topic with its link, state and About line."""
        self.assertEqual(
            render_topic_map(tree_of(K_FILES), "docs", "docs/design/README.md").split("\n")[2],
            "| [AUDIO](AUDIO.md) | Open | The sound the engine makes. |",
        )

    def test_marks_a_topic_under_revision(self) -> None:
        """Lists a topic in the revision folder with its link there and the state Revision."""
        tree = tree_of({**K_FILES, "docs/design/_REVISION/VIDEO/README.md": K_TOPIC})
        self.assertIn(
            "| [VIDEO](_REVISION/VIDEO/README.md) | Revision | The sound the engine makes. |",
            render_topic_map(tree, "docs", "docs/design/README.md").split("\n"),
        )

    def test_says_when_a_topic_has_no_about_line(self) -> None:
        """Writes a fixed word for a topic that has not described itself."""
        tree = tree_of({"docs/design/AUDIO.md": K_TOPIC.replace("**About:** The sound the engine makes.\n", "")})
        self.assertIn("No description.", render_topic_map(tree, "docs", "docs/design/README.md"))

    def test_lists_the_topics_of_a_module(self) -> None:
        """Lists the topics whose Modules line names the module, as links from its README."""
        body = render_module_designs(tree_of(K_FILES), "docs", "modules/domain/audio", "modules/domain/audio/README.md")
        self.assertEqual(body, "- [AUDIO](../../../docs/design/AUDIO.md): The sound the engine makes.")

    def test_lists_only_open_work_that_names_the_topic(self) -> None:
        """Lists an open folder with its phases and leaves a closed one out."""
        body = render_topic_work(tree_of(K_FILES), "docs", "AUDIO", "docs/design/AUDIO.md")
        self.assertEqual(body, "- [2026_10_20_SPATIALIZER](../agent/2026_10_20_SPATIALIZER/SPEC.md): A1")

    def test_says_when_no_work_is_open(self) -> None:
        """Writes a fixed sentence when no open folder names the topic."""
        tree = tree_of({key: value for key, value in K_FILES.items() if "SPATIALIZER" not in key})
        self.assertEqual(render_topic_work(tree, "docs", "AUDIO", "docs/design/AUDIO.md"), "No open work.")

    def test_names_the_topic_map_the_module_and_the_work_blocks(self) -> None:
        """Names the topic map, the module block and the work block of a tree."""
        names = sorted(block for _, block, _ in expected_blocks(tree_of(K_FILES)))
        self.assertEqual(names, ["designs", "topics", "work"])

    def test_state_of_names_the_state_word_of_a_status_line(self) -> None:
        """Reads Shipped, Superseded and Withdrawn from the status word of a topic."""
        rows = (
            ("Open — phase A1 is building", "Open"),
            ("Shipped — 2026-10-01", "Shipped"),
            ("Superseded — 2026-10-01 by VIDEO", "Superseded"),
            ("Withdrawn — 2026-10-01, no longer wanted", "Withdrawn"),
        )
        for line, state in rows:
            with self.subTest(line=line):
                self.assertEqual(state_of("docs/design/AUDIO.md", f"# Audio\n\n**Status:** {line}\n"), state)

    def test_modules_with_designs_lists_each_module_once_in_order(self) -> None:
        """Lists a module that two topics name once, and the modules sorted."""
        video = K_TOPIC.replace("modules/domain/audio", "modules/domain/video, modules/domain/audio/")
        tree = tree_of({**K_FILES, "docs/design/VIDEO.md": video})
        self.assertEqual(modules_with_designs(tree), ["modules/domain/audio", "modules/domain/video"])


class BlockTest(unittest.TestCase):
    """Covers reading and writing between markers, on the text of a file."""
    K_TEST_SIZE = "small"

    def test_returns_none_without_markers(self) -> None:
        """Reads no block from a text that has no markers."""
        self.assertIsNone(read_block("# Design\n", "topics"))

    def test_write_block_replaces_only_what_is_between_the_markers(self) -> None:
        """Replaces what is between the markers and nothing else."""
        text = "head\n<!-- topics:begin -->\nold\n<!-- topics:end -->\ntail\n"
        self.assertEqual(write_block(text, "topics", "new one\nnew two"),
                         "head\n<!-- topics:begin -->\nnew one\nnew two\n<!-- topics:end -->\ntail\n")

    def test_write_block_changes_nothing_on_the_same_body(self) -> None:
        """Returns the text itself when its block already holds the body."""
        text = "head\n<!-- topics:begin -->\nnew\n<!-- topics:end -->\ntail\n"
        self.assertEqual(write_block(text, "topics", "new"), text)

    def test_leaves_a_text_without_markers_as_it_was(self) -> None:
        """Returns the text itself when the text carries no such block."""
        self.assertEqual(write_block("plain\n", "topics", "new"), "plain\n")

    def test_insert_block_adds_a_block_under_its_heading_once(self) -> None:
        """Adds a block under a heading, and adds nothing the second time."""
        added = insert_block(K_FILES["docs/design/README.md"], "topics", "## Topics")
        self.assertIsNotNone(added)
        self.assertIsNone(insert_block(added, "topics", "## Topics"))

    def test_insert_block_puts_the_work_block_at_the_end_of_the_phases_section(self) -> None:
        """Adds the Work block after the phase table and before the next section."""
        topic = insert_block(K_TOPIC, "work", None)
        self.assertIsNotNone(topic)
        self.assertLess(topic.index("| A1 |"), topic.index("### Work"))
        self.assertLess(topic.index("### Work"), topic.index("## Open questions"))


if __name__ == "__main__":
    unittest.main()
