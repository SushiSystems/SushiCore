"""A table has a header row, one rule under it, and no frame."""

import re

import pytest

from sushicore.theme import Theme
from sushicore.ui.table import Table
from tests.ui.capture import capture, capture_ansi

K_ROWS = (("sushiruntime", "cloned"), ("sushiengine", "linked"))

K_INVENTORY_COLUMNS = ("Owner", "Component", "Status", "Detail")
K_INVENTORY_ROWS = (
    ("shared", "python", "OK", r"C:\Users\sushi\AppData\Local\Programs\Python\python.EXE"),
    (
        "shared",
        "build_tools",
        "NOT NEEDED",
        "C++ compiler and core build tools (gcc, g++, make). Any GCC >= 9 suffices for the "
        "intel-llvm -fsycl host pass. (nothing to install on windows)",
    ),
    ("shared", "GPU vendor", "OK", "NVIDIA - installs CUDA toolkit"),
    ("sushiruntime", "adaptivecpp", "MISSING", "AdaptiveCpp (acpp)"),
)


def _inventory(**overrides) -> Table:
    """Return the fixed inventory table, grouped by owner unless overridden."""
    fields = {
        "columns": K_INVENTORY_COLUMNS,
        "rows": K_INVENTORY_ROWS,
        "title": "Environment inventory",
        "group_by": "Owner",
    }
    return Table(**{**fields, **overrides})


def _lines(table: Table) -> list[str]:
    """Return the table's plain lines at 100 columns, without the trailing empty line."""
    return capture(table, width=100).split("\n")[:-1]


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


def test_group_by_must_name_one_of_the_columns():
    with pytest.raises(ValueError) as error:
        _inventory(group_by="Owners")
    assert "Owners" in str(error.value)
    assert all(column in str(error.value) for column in K_INVENTORY_COLUMNS)


def test_the_grouped_table_keeps_its_title_and_a_blank_line_under_it():
    lines = _lines(_inventory())
    assert lines[0] == "Environment inventory"
    assert lines[1] == ""


def test_the_column_headers_are_drawn_once_without_the_group_column():
    lines = _lines(_inventory())
    headers = [line for line in lines if "Component" in line and "Status" in line]
    assert len(headers) == 1
    assert "Owner" not in headers[0]
    assert headers[0].split() == ["Component", "Status", "Detail"]


def test_a_muted_rule_separates_the_headers_from_the_first_group():
    lines = _lines(_inventory())
    rule = lines.index("Environment inventory") + 3
    assert set(lines[rule]) == {"─"}
    assert lines[rule + 1] == "shared"


def test_each_group_value_becomes_a_heading_in_order_of_first_appearance():
    lines = _lines(_inventory())
    assert [line for line in lines if line and line[0] not in " ─"] == [
        "Environment inventory",
        "shared",
        "sushiruntime",
    ]


def test_one_blank_line_separates_the_groups_and_none_follows_the_last():
    lines = _lines(_inventory())
    assert lines[lines.index("sushiruntime") - 1] == ""
    assert lines[-1].lstrip().startswith("adaptivecpp")


def test_the_group_column_is_gone_from_the_rows():
    assert "sushiruntime  " not in "\n".join(_lines(_inventory()))


def test_every_column_but_the_last_lines_up_across_the_groups():
    lines = _lines(_inventory())
    python = next(line for line in lines if "python" in line)
    adaptivecpp = next(line for line in lines if "adaptivecpp" in line)
    assert python.index("OK") == adaptivecpp.index("MISSING")
    assert python.index("C:") == adaptivecpp.index("AdaptiveCpp")


def test_only_the_last_column_wraps():
    lines = _lines(_inventory())
    detail = next(line for line in lines if "python" in line).index("C:")
    first = next(position for position, line in enumerate(lines) if set(line) == {"─"}) + 1
    rows = [line for line in lines[first:] if line.startswith("  ")]
    assert all(len(line) <= 100 for line in rows)
    assert len([line for line in rows if line[:detail].strip()]) == len(K_INVENTORY_ROWS)
    wrapped = [line for line in rows if not line[:detail].strip()]
    assert wrapped and all(line[:detail] == " " * detail for line in wrapped)


def test_a_wrapped_detail_keeps_its_first_word_under_the_first_line():
    lines = _lines(_inventory())
    first = next(line for line in lines if "build_tools" in line)
    detail = first.index("C++")
    following = lines[lines.index(first) + 1]
    assert following[:detail].strip() == ""
    assert following[detail] != " "


def test_an_empty_group_value_is_drawn_as_a_dash():
    rows = (("", "python", "OK", "found"),)
    assert "-" in _lines(_inventory(rows=rows))


def test_a_status_cell_takes_the_theme_style_its_word_maps_to():
    text = capture_ansi(_inventory(), width=100, theme=Theme())
    assert "\x1b[1;32mOK" in text
    assert "\x1b[1;31mMISSING" in text
    assert "\x1b[2mNOT NEEDED" in text


def test_a_status_word_is_recognised_whatever_its_case():
    rows = (("shared", "python", "ok", "found"),)
    assert "\x1b[1;32mok" in capture_ansi(_inventory(rows=rows), width=100)


def test_a_cell_that_is_not_a_status_word_carries_no_style():
    text = capture_ansi(Table(("Module", "State"), (("sushiruntime", "cloned"),)), width=50)
    row = next(line for line in text.split("\n") if "sushiruntime" in line)
    assert re.search(r"\x1b\[[0-9;]*m(?=cloned)", row) is None
