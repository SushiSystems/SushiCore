"""The machine flag picks the renderer before anything prints."""

import json
from pathlib import Path

from sushicore import JsonRenderer, build_console
from sushicore.cli_console import LazyConsole


def test_build_console_machine_uses_the_json_renderer():
    console = build_console([], machine=True)
    assert isinstance(console._renderer, JsonRenderer)


def test_lazy_console_reads_machine_at_first_build(monkeypatch, capsys):
    lazy = LazyConsole(lambda: Path("/nowhere"))
    lazy.machine = True
    lazy.attribute("info")("hello")
    assert json.loads(capsys.readouterr().out.strip()) == {"event": "line", "level": "info", "message": "hello"}


def test_lazy_console_exposes_the_new_names():
    lazy = LazyConsole(lambda: Path("/nowhere"))
    for name in ("table", "progress", "result", "prompt"):
        assert callable(lazy.attribute(name))
