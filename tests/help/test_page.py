"""HelpPage lays a HelpModel out from components."""

from sushicore.help.model import HelpModel, HelpSection
from sushicore.help.page import HelpPage
from sushicore.ui.logo import Logo
from tests.ui.capture import capture

K_BLOCKS = "▀▄█"
K_LOGO_WIDTH = Logo().width


def _leaf() -> HelpModel:
    """Return the model of a leaf help screen."""
    return HelpModel(
        name="hub add", description="Bring a module in.", usage="hub add [OPTIONS] MODULE",
        is_root=False, commands=(),
        arguments=(("MODULE", "The module."),),
        options=(("--dry-run", "Show the plan only."),),
        examples=(("hub add sr", "Bring sushiruntime in"),),
    )


def _root() -> HelpModel:
    """Return the model of a root help screen."""
    return HelpModel(
        name="hub", description="Manage the stack.", usage="hub [OPTIONS] COMMAND [ARGS]...",
        is_root=True,
        commands=(
            HelpSection("Modules", (("add", "Bring a module in."),)),
            HelpSection("Account", (("login", "Sign in."),)),
        ),
        arguments=(), options=(("--help", "Show this message and exit."),), examples=(),
    )


def test_a_leaf_page_lists_its_sections_in_order():
    assert capture(HelpPage(_leaf())) == (
        "hub add\n"
        "Bring a module in.\n"
        "\n"
        "Usage: hub add [OPTIONS] MODULE\n"
        "\n"
        "Arguments\n"
        "  MODULE  The module.\n"
        "\n"
        "Options\n"
        "  --dry-run  Show the plan only.\n"
        "\n"
        "Examples\n"
        "  hub add sr  Bring sushiruntime in\n"
    )


def test_a_root_page_lists_each_command_group_before_the_options():
    text = capture(HelpPage(_root()))
    assert text.index("Modules") < text.index("Account") < text.index("Options")
    assert "  add  Bring a module in." in text


def test_empty_sections_are_left_out():
    text = capture(HelpPage(_root()))
    assert "Arguments" not in text and "Examples" not in text


def test_a_root_page_draws_the_logo_it_is_given():
    text = capture(HelpPage(_root(), logo=Logo()), width=K_LOGO_WIDTH)
    assert any(ch in text for ch in K_BLOCKS)


def test_the_logo_comes_before_the_title():
    text = capture(HelpPage(_root(), logo=Logo()), width=K_LOGO_WIDTH)
    block = min(text.index(ch) for ch in K_BLOCKS if ch in text)
    assert block < text.index("Manage the stack.")


def test_a_page_without_a_logo_draws_none():
    assert not any(ch in capture(HelpPage(_root()), width=K_LOGO_WIDTH) for ch in K_BLOCKS)


def test_the_logo_never_shows_on_a_sub_command_page():
    text = capture(HelpPage(_leaf(), logo=Logo()), width=K_LOGO_WIDTH)
    assert not any(ch in text for ch in K_BLOCKS)
