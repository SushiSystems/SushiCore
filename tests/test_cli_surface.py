# test_cli_surface.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The surfaces every Sushi CLI takes from sushicore: root options, diagnostics, aliases, entry."""

import io
import json
from datetime import date

import pytest
import typer
from typer.testing import CliRunner

from sushicore.aliases import Alias, AliasTable, UnknownAliasError
from sushicore.describe import K_CONTRACT_VERSION, catalogue
from sushicore.diag_commands import register_diagnostic_commands
from sushicore.entry import run
from sushicore.errors import ConfigError, SushiCoreError
from sushicore.root_options import register_root_options, version_line
from sushicore.workspace import read_toml

K_REMOVED = date(2027, 3, 25)


class _Tty(io.StringIO):
    """A text stream that reports itself as a terminal."""

    def isatty(self) -> bool:
        """Returns True, as a terminal does."""
        return True


class _Diagnostics:
    """Records which diagnostic was asked for."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def config_show(self) -> int:
        """Records the call and reports success."""
        self.calls.append(("config",))
        return 0

    def env_dump(self, show_all: bool = False) -> int:
        """Records the call and reports the failure code 3."""
        self.calls.append(("env", show_all))
        return 3


def _app() -> typer.Typer:
    """Returns an application named `sx` with one command and one hidden command."""
    app = typer.Typer(name="sx", help="Builds things.", no_args_is_help=True, add_completion=False)

    @app.command("build")
    def build(clean: bool = typer.Option(False, "--clean", help="Start over.")) -> None:
        """Configure and build.

        A second paragraph the catalogue leaves out.
        """
        typer.echo(f"built clean={clean}")

    @app.command("old-build", hidden=True)
    def old_build() -> None:
        """The old spelling."""

    return app


def test_version_prints_the_distribution_and_exits_zero():
    """--version prints one line naming the distribution and runs no command."""
    app = _app()
    register_root_options(app, distribution="sushicore")
    result = CliRunner().invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip() == version_line("sushicore")
    assert result.output.startswith("sushicore ")


def test_version_of_an_unknown_distribution_reads_unknown():
    """A distribution that is not installed reports `unknown`, not a traceback."""
    assert version_line("no-such-distribution-xyz") == "no-such-distribution-xyz unknown"


def test_version_lines_can_be_supplied_by_the_cli():
    """A CLI that knows more than its version prints its own lines."""
    app = _app()
    register_root_options(app, distribution="sushicore", version_lines=lambda: ["sx 1", "root /x"])
    assert CliRunner().invoke(app, ["--version"]).output == "sx 1\nroot /x\n"


def test_describe_prints_the_catalogue_without_hidden_commands():
    """--describe prints the catalogue as JSON and leaves hidden spellings out."""
    app = _app()
    register_root_options(app, distribution="sushicore")
    result = CliRunner().invoke(app, ["--describe"])
    assert result.exit_code == 0
    document = json.loads(result.output)
    assert document["program"] == "sx"
    assert document["contract"] == K_CONTRACT_VERSION
    assert [command["name"] for command in document["commands"]] == ["build"]
    assert document["commands"][0]["help"] == "Configure and build."
    assert document["commands"][0]["params"][0]["flags"] == ["--clean"]


def test_root_options_keep_the_help_and_the_commands():
    """Registering the root options changes neither the help text nor a command's behaviour."""
    app = _app()
    register_root_options(app, distribution="sushicore")
    runner = CliRunner()
    assert "Builds things." in runner.invoke(app, ["--help"]).output
    assert runner.invoke(app, ["build", "--clean"]).output == "built clean=True\n"


def test_catalogue_carries_applies_to():
    """The catalogue repeats the presence list a caller gives it on every command."""
    document = catalogue(_app(), distribution="sushicore", applies_to=("cloned",))
    assert document["commands"][0]["applies_to"] == ["cloned"]


def test_diagnostic_commands_delegate_and_return_the_code():
    """config and env call the diagnostics object and exit with what it returns."""
    app = _app()
    diagnostics = _Diagnostics()
    register_diagnostic_commands(app, diagnostics, program="sx", panel="Diagnostics")
    runner = CliRunner()
    assert runner.invoke(app, ["config"]).exit_code == 0
    assert runner.invoke(app, ["env", "--all"]).exit_code == 3
    assert runner.invoke(app, ["env", "-a"]).exit_code == 3
    assert diagnostics.calls == [("config",), ("env", True), ("env", True)]


def test_diagnostic_commands_can_leave_env_to_the_cli():
    """A CLI whose env takes its own flags registers config alone."""
    app = _app()
    register_diagnostic_commands(app, _Diagnostics(), program="sx", panel="Diagnostics", env=False)
    assert CliRunner().invoke(app, ["env"]).exit_code == 2


def _table() -> AliasTable:
    """Returns a table with one dated and one permanent alias."""
    return AliasTable("sx", (Alias("sx doxygen", "sx docs", K_REMOVED), Alias("sx b", "sx build", None)))


def test_alias_notice_names_both_spellings_and_the_date():
    """The notice tells the user the new spelling and the last day of the old one."""
    table = _table()
    assert table.notice(table.alias_for("sx doxygen")) == (
        "sx: `sx doxygen` is now `sx docs`; the old spelling is removed after 2027-03-25.")


def test_alias_announces_once_to_a_terminal_only():
    """The notice is printed once per table, and never to a stream that is not a terminal."""
    table = _table()
    pipe, terminal = io.StringIO(), _Tty()
    table.announce(table.alias_for("sx doxygen"), stream=pipe)
    table.announce(table.alias_for("sx doxygen"), stream=terminal)
    table.announce(table.alias_for("sx doxygen"), stream=terminal)
    assert pipe.getvalue() == ""
    assert terminal.getvalue().count("\n") == 1


def test_alias_stays_silent_when_switched_off_or_permanent(monkeypatch):
    """The environment switch and a permanent alias both print nothing."""
    table = _table()
    terminal = _Tty()
    table.announce(table.alias_for("sx b"), stream=terminal)
    monkeypatch.setenv("SX_NO_DEPRECATION_NOTICE", "1")
    table.announce(table.alias_for("sx doxygen"), stream=terminal)
    assert terminal.getvalue() == ""


def test_alias_command_runs_the_new_command_and_is_hidden():
    """The old word runs the new command's callback and does not appear in the catalogue."""
    app = _app()
    table = AliasTable("sx", (Alias("sx make", "sx build", K_REMOVED),))
    build = next(info.callback for info in app.registered_commands if info.name == "build")
    table.command(app, "make", build, "sx make")
    assert CliRunner().invoke(app, ["make", "--clean"]).output == "built clean=True\n"
    names = [command["name"] for command in catalogue(app, distribution="sushicore")["commands"]]
    assert "make" not in names


def test_alias_table_reports_unknown_and_expired_rows():
    """An unknown spelling raises, and a row past its date is listed as expired."""
    table = _table()
    with pytest.raises(UnknownAliasError):
        table.alias_for("sx nothing")
    assert [alias.old for alias in table.expired(date(2027, 3, 26))] == ["sx doxygen"]
    assert table.expired(K_REMOVED) == []


def test_read_toml_reports_a_malformed_file_as_a_config_error(tmp_path):
    """A file that is not TOML raises a ConfigError that names the file."""
    path = tmp_path / "config.toml"
    path.write_text("[cli\ncolor = ", encoding="utf-8")
    with pytest.raises(ConfigError) as caught:
        read_toml(path)
    assert str(path) in str(caught.value)
    assert isinstance(caught.value, ValueError)


def test_run_turns_a_sushicore_error_into_one_line_and_exit_one():
    """The entry point reports a sushicore failure through the CLI's reporter and exits 1."""
    app = _app()

    @app.command("fail")
    def fail() -> None:
        """Raises the failure a broken configuration raises."""
        raise ConfigError("config.toml: bad value")

    reported: list[str] = []
    with pytest.raises(SystemExit) as caught:
        run(app, reported.append, argv=["fail"])
    assert caught.value.code == 1
    assert reported == ["config.toml: bad value"]


def test_run_falls_back_to_stderr_when_the_reporter_itself_fails(capsys):
    """A reporter that cannot be built still leaves the user one line on stderr."""
    app = _app()

    @app.command("fail")
    def fail() -> None:
        """Raises the failure a broken configuration raises."""
        raise ConfigError("config.toml: bad value")

    def broken(message: str) -> None:
        """Fails the way a console built from the same broken file fails."""
        raise ConfigError("cannot build the console")

    with pytest.raises(SystemExit) as caught:
        run(app, broken, argv=["fail"])
    assert caught.value.code == 1
    assert capsys.readouterr().err == "sx: config.toml: bad value\n"


def test_run_passes_a_normal_exit_and_other_errors_through():
    """A command's own exit code survives, and a bug is not disguised as a user error."""
    app = _app()

    @app.command("bug")
    def bug() -> None:
        """Raises what a programming error raises."""
        raise KeyError("oops")

    with pytest.raises(SystemExit) as caught:
        run(app, lambda message: None, argv=["build"])
    assert caught.value.code == 0
    with pytest.raises(KeyError):
        run(app, lambda message: None, argv=["bug"])
    assert issubclass(ConfigError, SushiCoreError)
