"""The usage line prints its string literally."""

from sushicore.ui.usage import Usage
from tests.ui.capture import capture


def test_usage_keeps_square_brackets_literal():
    usage = Usage("hub [OPTIONS] COMMAND [ARGS]...")
    assert capture(usage) == "Usage: hub [OPTIONS] COMMAND [ARGS]...\n"
