"""A table has a header row, one rule under it, and no frame."""

from sushicore.ui.table import Table
from tests.ui.capture import capture

K_ROWS = (("sushiruntime", "cloned"), ("sushiengine", "linked"))


def test_table_draws_title_header_rule_and_rows():
    text = capture(Table(("Module", "State"), K_ROWS, title="Modules"), width=50)
    assert text == (
        "Modules\n"
        "Module         State\n"
        "─────────────────────\n"
        "sushiruntime   cloned\n"
        "sushiengine    linked\n"
    )


def test_table_without_a_title_starts_at_the_header_row():
    assert capture(Table(("Module", "State"), K_ROWS), width=50).startswith("Module ")


def test_table_has_no_outer_frame():
    text = capture(Table(("Module", "State"), K_ROWS, title="Modules"), width=50)
    assert not set(text) & set("│┃┌┐└┘╭╮╰╯|+")
