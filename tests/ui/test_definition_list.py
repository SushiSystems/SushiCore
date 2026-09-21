"""A definition list is a heading over a term column and a text column."""

from sushicore.ui.definition_list import DefinitionList
from tests.ui.capture import capture, capture_raw


def test_entries_align_and_the_text_wraps_inside_its_column():
    entries = (
        ("add", "Bring one or more stack modules into the workspace, with what they need."),
        ("install-cli", "Install a [cyan]module[/cyan]'s CLI."),
    )
    assert capture(DefinitionList("Modules", entries), width=50) == (
        "Modules\n"
        "  add          Bring one or more stack modules\n"
        "               into the workspace, with what they\n"
        "               need.\n"
        "  install-cli  Install a module's CLI.\n"
    )


def test_a_term_with_brackets_is_printed_literally():
    text = capture(DefinitionList("Options", (("--type [debug|release]", "The build type."),)))
    assert "--type [debug|release]" in text


def test_an_entry_without_text_prints_its_term_alone():
    assert capture(DefinitionList("Examples", (("hub doctor", ""),))) == "Examples\n  hub doctor\n"


def test_a_row_is_not_padded_to_the_console_width():
    entries = (("add", "Bring a module in."), ("install-cli", "Install a module's CLI."))
    lines = capture_raw(DefinitionList("Modules", entries), width=200).splitlines()
    assert max(len(line) for line in lines) <= 60
