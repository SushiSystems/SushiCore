"""build_model reads a Click command tree into a HelpModel."""

import click
import typer

from sushicore.help.from_click import build_model


class _RegistrationOrderGroup(click.Group):
    """Lists its commands in registration order, as a Typer group does."""

    def list_commands(self, ctx: click.Context) -> list[str]:
        """Return the command names in the order they were registered."""
        return list(self.commands)


def _tree(group_class: type[click.Group] = _RegistrationOrderGroup) -> click.Group:
    """Return a plain Click tree of five commands, registered out of alphabetical order."""

    @click.group(
        cls=group_class,
        name="hub",
        help="Manage the\nstack.\n\nSecond paragraph.\f hidden",
        epilog="hub add sr  # bring sushiruntime in\n\nhub doctor",
    )
    def hub():
        pass

    @hub.command(name="init", help="Mark a workspace.")
    def init():
        pass

    @hub.command(name="doctor", help="Check tools.")
    def doctor():
        pass

    @hub.command(name="add", help="Bring a module in.")
    @click.argument("module")
    @click.option("--dry-run", is_flag=True, help="Show the plan only.")
    def add(module, dry_run):
        pass

    @hub.command(name="link", help="Register a checkout.")
    def link():
        pass

    @hub.command(name="secret", help="Hidden.", hidden=True)
    def secret():
        pass

    add.rich_help_panel = "Modules"
    link.rich_help_panel = "Modules"
    init.rich_help_panel = "Workspace"
    return hub


def _root(group_class: type[click.Group] = _RegistrationOrderGroup):
    """Return the tree and a context for it."""
    group = _tree(group_class)
    return group, click.Context(group, info_name="hub")


def _typer_root():
    """Return a default-mode Typer app as a Click command, and a context for it."""
    app = typer.Typer(name="tool", help="Tend a garden.")

    @app.command(name="grow", help="Grow a module.", rich_help_panel="Garden")
    def grow(
        module: str = typer.Argument(..., help="The module."),
        kind: str = typer.Option("a", "--kind", help="Kind [x]."),
    ):
        pass

    @app.command(name="rest", help="Rest a while.")
    def rest():
        pass

    command = typer.main.get_command(app)
    return command, click.Context(command, info_name="tool")


def _leaf_model(command: click.Command, parent: click.Context):
    """Return the help model of ``command`` as a child of ``parent``."""
    return build_model(command, click.Context(command, info_name=command.name, parent=parent))


def test_commands_are_grouped_by_panel_in_order_of_first_appearance():
    group, ctx = _root()
    sections = build_model(group, ctx).commands
    assert [s.heading for s in sections] == ["Workspace", "Commands", "Modules"]
    assert [term for term, _ in sections[2].entries] == ["add", "link"]


def test_a_plain_click_group_lists_commands_alphabetically_so_panels_follow_that_order():
    group, ctx = _root(click.Group)
    headings = [s.heading for s in build_model(group, ctx).commands]
    assert headings == ["Modules", "Commands", "Workspace"]


def test_a_command_with_no_panel_falls_into_commands():
    group, ctx = _root()
    sections = {s.heading: s.entries for s in build_model(group, ctx).commands}
    assert sections["Commands"] == (("doctor", "Check tools."),)


def test_a_placeholder_panel_is_not_a_heading():
    group, ctx = _root()
    group.commands["add"].rich_help_panel = object()
    sections = {s.heading: s.entries for s in build_model(group, ctx).commands}
    assert list(sections) == ["Workspace", "Commands", "Modules"]
    assert [term for term, _ in sections["Commands"]] == ["doctor", "add"]


def test_hidden_commands_are_left_out():
    group, ctx = _root()
    names = [t for s in build_model(group, ctx).commands for t, _ in s.entries]
    assert "secret" not in names


def test_options_come_from_the_help_records():
    group, ctx = _root()
    add = group.commands["add"]
    model = build_model(add, click.Context(add, info_name="add", parent=ctx))
    assert ("--dry-run", "Show the plan only.") in model.options
    assert ("--help", "Show this message and exit.") in model.options


def test_an_argument_without_a_record_falls_back_to_its_metavar():
    group, ctx = _root()
    add = group.commands["add"]
    model = build_model(add, click.Context(add, info_name="add", parent=ctx))
    assert model.arguments == (("MODULE", ""),)


def test_usage_and_name_use_the_command_path():
    group, ctx = _root()
    add = group.commands["add"]
    model = build_model(add, click.Context(add, info_name="add", parent=ctx))
    assert model.name == "hub add"
    assert model.usage == "hub add [OPTIONS] MODULE"


def test_only_the_top_command_is_the_root():
    group, ctx = _root()
    add = group.commands["add"]
    assert build_model(group, ctx).is_root
    assert not build_model(add, click.Context(add, info_name="add", parent=ctx)).is_root


def test_a_leaf_has_no_command_sections():
    group, ctx = _root()
    add = group.commands["add"]
    assert build_model(add, click.Context(add, info_name="add", parent=ctx)).commands == ()


def test_examples_split_the_command_from_its_note_and_skip_blank_lines():
    group, ctx = _root()
    assert build_model(group, ctx).examples == (
        ("hub add sr", "bring sushiruntime in"),
        ("hub doctor", ""),
    )


def test_the_description_joins_wrapped_lines_and_stops_at_a_form_feed():
    group, ctx = _root()
    assert build_model(group, ctx).description == "Manage the stack.\n\nSecond paragraph."


def test_a_typer_app_groups_by_its_panels_and_keeps_typer_help_records():
    command, ctx = _typer_root()
    model = build_model(command, ctx)
    assert model.name == "tool"
    assert model.description == "Tend a garden."
    assert [(s.heading, s.entries) for s in model.commands] == [
        ("Garden", (("grow", "Grow a module."),)),
        ("Commands", (("rest", "Rest a while."),)),
    ]
    grow = command.get_command(ctx, "grow")
    leaf = build_model(grow, click.Context(grow, info_name="grow", parent=ctx))
    assert leaf.arguments == (("MODULE", "The module.  \\[required]"),)
    assert ("--kind TEXT", "Kind [x].  \\[default: a]") in leaf.options
    assert leaf.usage == "tool grow [OPTIONS] MODULE"


def test_a_plain_click_option_has_its_default_marker_escaped():
    @click.command(name="grow")
    @click.option("--kind", default="a", show_default=True, help="Kind.")
    def grow(kind):
        pass

    model = build_model(grow, click.Context(grow, info_name="grow"))
    assert ("--kind TEXT", r"Kind.  \[default: a]") in model.options


def test_a_plain_click_description_has_its_brackets_escaped():
    @click.command(name="grow", help="Close with [/] and [cyan]x[/cyan].")
    def grow():
        pass

    model = build_model(grow, click.Context(grow, info_name="grow"))
    assert model.description == r"Close with \[/] and \[cyan]x\[/cyan]."


def test_a_plain_click_argument_help_and_sub_command_help_are_escaped():
    @click.group(name="hub")
    def hub():
        pass

    @hub.command(name="reset", help="Reset [hard] mode.")
    @click.argument("target")
    def reset(target):
        pass

    reset.params[0].help = "The [target]."
    ctx = click.Context(hub, info_name="hub")
    assert build_model(hub, ctx).commands[0].entries == (("reset", r"Reset \[hard] mode."),)
    assert _leaf_model(reset, ctx).arguments == (("TARGET", r"The \[target]."),)


def test_terms_and_examples_are_never_escaped():
    @click.command(name="grow", epilog="grow [x]  # a [note]")
    @click.option("--kind", metavar="[KIND]", help="Kind.")
    def grow(kind):
        pass

    model = build_model(grow, click.Context(grow, info_name="grow"))
    assert ("--kind [KIND]", "Kind.") in model.options
    assert model.examples == (("grow [x]", "a [note]"),)


def test_a_rich_mode_command_keeps_its_markup_in_the_description_and_parameters():
    @click.command(name="grow", help="Paint [cyan]x[/cyan].")
    @click.option("--kind", help="Kind [b]y[/b].")
    def grow(kind):
        pass

    grow.rich_markup_mode = "rich"
    model = build_model(grow, click.Context(grow, info_name="grow"))
    assert model.description == "Paint [cyan]x[/cyan]."
    assert ("--kind TEXT", "Kind [b]y[/b].") in model.options


def test_each_command_is_read_in_its_own_markup_mode():
    group, ctx = _root()
    group.rich_markup_mode = "rich"
    group.help = "Paint [cyan]x[/cyan]."
    group.commands["doctor"].help = "Check [b]tools[/b]."
    group.commands["link"].rich_markup_mode = "rich"
    group.commands["link"].help = "Link [b]it[/b]."
    model = build_model(group, ctx)
    sections = {s.heading: dict(s.entries) for s in model.commands}
    assert model.description == "Paint [cyan]x[/cyan]."
    assert sections["Commands"]["doctor"] == r"Check \[b]tools\[/b]."
    assert sections["Modules"]["link"] == "Link [b]it[/b]."
