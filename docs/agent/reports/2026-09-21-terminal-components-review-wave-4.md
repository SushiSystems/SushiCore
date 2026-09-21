# Review: terminal components, Tasks 8 to 10 and 12

Reviewer pass over the uncommitted work of Tasks 8, 9, 10 and 12 in `D:/Projects/sushicore`.
Spec: `docs/agent/specs/2026-09-21-terminal-components-design.md`.
Plan: `docs/agent/plans/2026-09-21-terminal-components.md`, Global Constraints and Tasks 8 to 10.
Earlier review: `docs/agent/reports/2026-09-21-terminal-components-review-wave-2.md`.

Environment: Python 3.13.13, rich 15.0.0, click 8.2.1, typer 0.20.0, pytest 9.1.1, win32.
Every command below ran with `PYTHONPATH=D:/Projects/sushicore`.

---

## 1. SOLID shape

### 1.1 `renderer.py` now pulls Rich into `import sushicore`, and doubles the import cost

Most serious finding in this section. `sushicore/renderer.py:19-21` imports `.ui.header`,
`.ui.panel` and `.ui.table` at module scope. Those files import `rich.console`, `rich.rule`,
`rich.panel`, `rich.table`, `rich.box` and `rich.text` at module scope too. `sushicore/__init__.py`
imports `console.py`, which imports `renderer.py`, so `import sushicore` now imports all of Rich.

The same file defers Rich everywhere else on purpose: `from rich.console import Console as
_RichConsole` sits inside `RichRenderer.__init__` (line 95), `from rich.theme import Theme as
_RichTheme` beside it, `from rich.prompt import Prompt` inside `prompt` (line 139), and
`PlainRenderer.raw` and `JsonRenderer.raw` each import inside the property (lines 158, 239). Task 8
put three eager imports at the top of a file whose whole style is lazy, and nothing in the plan
asked for that placement.

Measured, five subprocess runs each, minimum taken, with `git stash` to get the pre-Task-8 tree:

```
$ python -c "import sys; import sushicore; print(any(m.startswith('rich') for m in sys.modules))"
True                      # current tree
False                     # same command with renderer.py stashed

after  min 0.103s         # python -c "import sushicore"
before min 0.053s
```

Every Sushi CLI pays 50 ms on every invocation, including `hub --version` and shell completion,
which never draw a table. The fix is one line per method: import the component inside `header`,
`panel` and `table`, the way `prompt` imports `Prompt`.

### 1.2 `RichRenderer` keeps three parameters it no longer honours

`sushicore/renderer.py:117,121,125`. `header(title, style)`, `panel(title, body, border_style)`
and `table(title, columns, rows, header_style)` all drop their style argument and read
`self._theme` instead. Before Task 8 all three used the argument (`git diff` shows
`rule(f"[{style}]{title}")`, `border_style=border_style`, `header_style=header_style`).

The Protocol at lines 35-45 still declares the parameters, so the signature promises something no
implementation keeps. `Console` happens to pass `theme.header` and `theme.panel_border`, which is
why nothing in the suite notices. A caller that holds a `RichRenderer` directly trips over it:

```python
RichRenderer(theme).panel("Failed", "cmake exited 1", border_style="red")
```

draws the border in `theme.panel_border`, not red. Report 8 records the choice at line 43 and cites
the plan, so this is a plan-level decision rather than a worker defect, but the decision leaves a
Protocol that lies. Either the parameters go (all three renderers ignore them now, so the Protocol
can drop them and `Console` can stop computing them), or `RichRenderer` passes them to the
component and the component takes an override.

### 1.3 `console_provider()` has no guard, and `HelpGroup` alone has no provider at all

`sushicore/typer_help.py:27,32,55`. `console_provider` is declared as a `ClassVar` with no value.
`help_group()` supplies one through `type(...)`; `HelpGroup` used directly does not have one, and
`--help` raises `AttributeError: type object 'HelpGroup' has no attribute 'console_provider'`.
A `ClassVar` annotation without a value is a promise the class does not keep; a
`NotImplementedError`-raising default, or an `__init_subclass__` check, says it.

The provider itself is called unguarded. The spec's whole reason for a provider is that `--help`
must work outside a workspace (spec, "Help", last sentence), and `docs/README.md` repeats the claim.
A provider that raises there takes `--help` with it:

```
$ python probe_edge.py            # provider raises RuntimeError("no workspace here")
========== provider raises
exit 1
  File "D:\Projects\sushicore\sushicore\typer_help.py", line 32, in format_help
    _write_page(self, ctx, formatter, self.console_provider())
  File "probe_edge.py", line 59, in bad_provider
    raise RuntimeError("no workspace here")
RuntimeError: no workspace here
```

`hub --help` outside a workspace would print a Python traceback. sushicore cannot know what a
provider does, which is exactly why the one call it makes should be the one place that decides what
happens when the provider fails: catch, fall back to a default `Console(RichRenderer(Theme()), ...)`,
and draw the page. There is no test for a failing provider.

### 1.4 The `get_command` seam: handing a child out twice is safe, mutating it is permanent

`sushicore/typer_help.py:34-39`. Verified sound on the first half of the question.
`_page_writer(command, provider)` closes over `command` and over `provider`, never over the
previous `format_help`, so repeated lookups replace the attribute instead of stacking. Click
returns the same object each time, so there is one page:

```
$ python -m pytest tests/test_typer_help.py::test_looking_a_child_up_twice_leaves_it_with_one_help_page -q
1 passed
```

This matters more than the test says, because `build_model` calls `get_command` for every child
while drawing a group's page (`sushicore/help/from_click.py:49`), so every root `--help` hands out
every child once.

What the seam does not bound: the mutation is permanent and global to the command object.
`click.Group.get_command` returns `self.commands[name]`, so `hub add sr` (a plain invocation, no
help involved) also rewrites `add.format_help`, and the closure keeps the provider alive for the
rest of the process. If a command object is ever reachable from two groups with different
providers, the last lookup wins and the earlier group's `--help` draws on the other group's console.
No current CLI does that, so this is a shape note, not a failure I could produce.

`staticmethod(console)` in `type("SushiGroup", ...)` is correct and is covered
(`test_the_provider_is_called_as_a_plain_function_not_bound_to_the_group`). A plain function there
would bind and pass the group as an argument.

### 1.5 `ui/__init__.py` and `help/__init__.py` are shaped alike now; nothing keeps them honest

Wave 2 finding 1.3 is fixed: `sushicore/help/__init__.py:5-9` now re-exports `HelpModel`,
`HelpSection`, `build_model` and `HelpPage` with an `__all__`, matching `sushicore/ui/__init__.py`.

Wave 2 finding 1.2 is not. `tests/test_ui_architecture.py` gained
`test_render_takes_exactly_self_and_theme` (Task 12, Fix C, and it does bite) but still has no case
comparing `set(sushicore.ui.__all__)` against the `ui/*.py` stems. Adding `sushicore/ui/spacer.py`
and forgetting the two lines in `__init__.py` passes all six checks and leaves the component
missing from `sushicore.ui`.

### 1.6 Dependency direction: no finding

`sushicore/help/page.py` imports `..theme`, `..ui.*` and `.model`, nothing upward.
`sushicore/typer_help.py` is the only module importing `typer`. No `ui/` file imports
`sushicore.help`; `test_file_imports_only_what_a_component_may` covers it and passes.
`sushicore/help/from_click.py` imports `inspect`, `typing.Any`, `rich.markup.escape` and `.model`
only. The `rich.markup` import is new in Task 12 and stays inside what the spec allows for `help/`.

### 1.7 Carried from wave 2, still open, each one line

- `sushicore/help/model.py:8,16`: `HelpSection` and `HelpModel` are not `@typing.final`, while
  every `ui/` component is (wave 2, 1.5).
- `sushicore/help/from_click.py:84` still sniffs `inspect.signature(make_metavar)` while
  `collect_usage_pieces` (line 26), `get_params` (line 61) and `get_short_help_str` (line 53) are
  called raw. Task 12 touched this file and left the two policies side by side (wave 2, 1.4).
- `sushicore/ui/definition_list.py:15,28`: `K_INDENT = 2` named, `padding=(0, 2)` not (wave 2, 1.6).
- `sushicore/theme.py:92` still registers a preset named `"muted"` beside the token `muted`
  (wave 2, 1.8).

---

## 2. Humanizer register and `source-comments`

### 2.1 The changelog is no longer newest first

`docs/reference/CHANGELOG.md:3` states the format: "One line per meaningful change, newest first."
Lines 6 to 15 are ten `2026-09-21` entries, and line 16 onward are the `2026-09-22` entries that
were already there. The file now reads 09-21, 09-21, ..., 09-22, 09-22. The ten new lines belong
below the 09-22 block, or the dates are wrong. This is the only rule the file states about itself
and the change breaks it.

Format otherwise holds: every new line is one sentence, the longest is 176 characters (line 8),
all start with a past-tense verb, all name a path in backticks, none says why, none is nested.

### 2.2 `renderer.py` explains an ignored parameter in three docstrings

`sushicore/renderer.py:118,122,126`:

```python
"""Print a section header; the renderer's own theme styles it."""
"""Print the body inside a bordered panel; the renderer's own theme styles it."""
"""Print the rows as a table under one header rule; the renderer's own theme styles it."""
```

The clause after each semicolon answers "why is the `style` argument unused". That is the reason for
a design, which `source-comments` sends to a design document. It is the same shape as wave 2
finding 2.4, which was fixed in `logo.py` and reintroduced here three times.

Plain replacements: `"""Print a section header."""`, `"""Print the body inside a bordered
panel."""`, `"""Print the rows as a table under one header rule."""` The fact that `RichRenderer`
styles from its own theme belongs in the class docstring at line 91, or in the spec, which already
says it.

### 2.3 `typer_help.py`'s module docstring argues for the design

`sushicore/typer_help.py:1-5`:

```
Wires the help page into Typer; the only module in sushicore that imports Typer.

Typer builds each command with its own class, so a group cannot hand its children a
help renderer. The group replaces each child's format_help as it hands the child out.
```

Sentence two is the reason the third sentence exists. Five lines is inside the six-line limit, so
this is content, not length. Plain replacement, three lines:

```
Wires the help page into Typer; the only module in sushicore that imports Typer.

The group replaces each child's format_help as it hands the child out, because Typer
builds each command with its own class: see docs/agent/specs/2026-09-21-terminal-components-design.md.
```

or, keeping the rule strictly, drop sentence two and cite the spec path alone.

### 2.4 `page.py` carries an evaluative tail twice

`sushicore/help/page.py:1`:

```python
"""Lays a HelpModel out as components: the order of a help screen, and nothing else."""
```

and line 27:

```python
"""Draws one help screen; it knows the order of the blocks, not how each draws."""
```

"and nothing else" and "not how each draws" are claims about the layering, not facts about the
type. This is wave 2 finding 2.5 in a new file; `help/model.py:18` was fixed the same way and now
reads `"""Holds everything one help screen shows."""`, which is the model.

Plain replacements: `"""Lays a HelpModel out as components, in the order a help screen shows
them."""` and `"""Draws one help screen as an ordered group of components."""`

### 2.5 `from_click.py`'s module docstring still argues, and Task 12 added to it

`sushicore/help/from_click.py:1-5`:

```
Reads a Click or Typer command into a HelpModel, by duck typing.

It imports neither Click nor Typer: it asks the command object for what it has. The model's
text is Rich markup, so text a command did not mark up is escaped on the way in.
```

Wave 2 finding 2.6 named sentence two as rationale and gave a replacement. Task 12 edited this file
and left it, then added a second "so" clause. Plain replacement: `Reads a Click or Typer command
into a HelpModel by asking the command object for what it has.` and `The model's text is Rich
markup; text from a command that does not write markup is escaped.`

### 2.6 Test helper docstrings are still inconsistent, in the same files that were flagged

Wave 2 finding 2.3 named this. The new files repeat it.

- `tests/test_renderer_components.py:9` `_lines(capsys)` has no docstring, and it is the only
  helper in the file.
- `tests/test_typer_help.py:28` `_app` and line 59 `_run` have none, while line 139 `__init__`,
  line 149 `_terminal_app`, line 165 `_shows_logo` and line 21 `_clear_shared_style_caches` all do.
  Four helpers with a docstring and two without, in one file.
- `tests/help/test_page.py:10,20` `_leaf` and `_root` have none, while
  `tests/help/test_markup_safety.py:14,19,27` gives all three of its helpers one.

Plain replacements: `"""Return the captured stdout as lines, trailing spaces stripped."""`,
`"""Return the hub-like test app whose help draws through the page."""`, `"""Return the output of
one CliRunner invocation, asserting it exited zero."""`, `"""Return the model of a leaf help
screen."""`, `"""Return the model of a root help screen."""`

### 2.7 Two documentation sentences state something other than a fact

`docs/README.md:60-61`:

> Typer turns an app with one command and no callback into a plain command. It never reaches the
> group, so it keeps Typer's own screen.

"It" in sentence two has no referent the reader can pin: the app, the command and the screen are all
candidates, and the two "it"s point at different things. Plain replacement: "Typer turns an app with
one command and no callback into a plain command, which never reaches the group, so that app keeps
Typer's own screen."

`README.md:20`:

> `sushicore.ui`, `sushicore.brand` | One file per terminal element (logo, header, panel, table,
> title, usage, definition list), each drawn from a `Theme`

"each drawn from a `Theme`" is false for the one element the row names first. `Logo.render` takes
`theme` and never reads it; its colours come from `brand.py`, which is why `brand` shares the row.
Plain replacement: "One file per terminal element (logo, header, panel, table, title, usage,
definition list); each reads its styles from a `Theme`, and the logo its colours from `brand`."

### 2.8 Reports: one em dash out of step with its siblings, nothing else

`docs/agent/reports/2026-09-21-terminal-components-task-10.md:1` is `# Task 10 — \`help_group\``.
Reports 8, 9 and 12 head themselves `# Task 8 report: ...`, `# Task 9 report: \`HelpPage\`` and
`# Terminal components, Task 12: four review fixes`. One em dash in a document of that length is
inside budget; the point is that four siblings use three shapes. A colon in report 10 makes them
one.

No hidden verbs, no filler connective, no "serves as", no evaluative adjective, no rule of three,
no closing summary paragraph in any of the four. All four end on a "not done" list.

Module docstrings in scope are all one to six lines. No two `#` lines in a row in any in-scope
source file; `from_click.py:103` is the only `#` and it states an invariant the next line depends
on. No TODO, no history line, no separator line, no commented-out code.

---

## 3. Correctness

### 3.1 The suite's green depends on a fixture in an unrelated file, and Rich leaks colour state

Most serious finding. `tests/test_typer_help.py:20-26` carries an autouse fixture that clears
`Style._add` and `Style.parse` after every test in that file. It exists to keep a golden in a
different file passing. Remove it and the tree goes red:

```
$ python -m pytest tests -q          # with the fixture deleted
FAILED tests/ui/test_logo.py::test_the_logo_matches_its_golden_file
1 failed, 231 passed in 0.65s
```

The poisoner is one case:

```
$ python -m pytest "tests/test_typer_help.py::test_the_root_page_shows_the_logo_on_a_terminal_with_256_colours_or_more[256]" tests/ui/test_logo.py -q
FAILED tests/ui/test_logo.py::test_the_logo_matches_its_golden_file
1 failed, 5 passed in 0.15s

$ python -m pytest ".....[truecolor]" tests/ui/test_logo.py -q
6 passed in 0.10s
```

Report 12 finding 4 names this and calls it a test-only concern ("production uses one colour system
per process"). It is not test-only. Reproduced with no pytest, no Typer and no `typer_help`,
rendering the same component twice through Rich:

```
$ python -c "render('256', 80); after = render('truecolor', 60); ..."
truecolour output equals the golden: False
ACTUAL: '     \x1b[38;5;234m▄\x1b[0m\x1b[38;5;234m▄\x1b[0m\x1b[38;5;234;48;5;255m▀...'
GOLDEN: '     \x1b[38;2;26;28;32m▄\x1b[0m\x1b[38;2;26;28;32m▄\x1b[0m\x1b[38;2;26;28;32;48;2;244;244;244m▀...'
after clearing the caches: True
```

The second render emits the 256-colour approximation of the brand nori, `38;5;234`, where
truecolour `38;2;26;28;32` was asked for. Rich 15's `Style._add` is a process-global `lru_cache`
and keeps the first colour system's resolution. `Style.parse` is not involved:

```
clearing only Style.parse: False
clearing only Style._add:  True
```

So `tests/test_typer_help.py:25` (`Style.parse.cache_clear()`) is a line that does nothing, and the
fixture is in the wrong file: it protects `tests/ui/test_logo.py`, it only works because
`tests/test_typer_help.py` is collected before `tests/ui/`, and any future 256-colour render
anywhere in the suite breaks the golden again. There is no `conftest.py` in the repository. Two
honest fixes: move the cache clearing into a root `tests/conftest.py` as an autouse fixture, or
have `tests/ui/test_logo.py` clear the cache itself before it compares, so the golden defends
itself.

The product exposure is narrower than the test exposure but real: any process that draws a
component to a 256-colour console and then to a truecolour one gets the 256-colour codes the
second time. `typer_help._draw` builds a fresh console per call from `raw.color_system`, so a CLI
that talks to one terminal is safe; a host that renders for two (a test harness, a GUI, a server)
is not. Whichever way it is fixed, the claim "production uses one colour system per process"
should be written down as an assumption somewhere other than a report's finding list.

### 3.2 Every list row on the help page is padded to the console width

`sushicore/ui/definition_list.py:35` wraps the grid in `rich.padding.Padding`, whose `expand`
defaults to `True`, so each line is right-padded to the full width. The title, description and
usage lines are not. Measured on a real run, not a test:

```
$ python hubish.py --help | cat -A | head -8
hubish.py^M$
Manage the stack.^M$
^M$
Usage: hubish.py [OPTIONS] COMMAND [ARGS]...^M$
^M$
Modules^M$
  add  Bring a module in.                                                      ^M$
^M$
```

At 200 columns the same line carries about 120 trailing spaces:

```
'  add  Bring a module in, cloning it when the workspace does not hold it yet.       (…to column 200)'
```

`tests/ui/capture.py:25` strips line ends, so no test can see it. Report 10 lines 213-220 found it,
named the cause, named the file and left it to the orchestrator; nobody picked it up, and Task 12
did not touch it. Concrete cost: `hub --help > help.txt` and any diff or golden built on help output
carries width-dependent whitespace, so the same command on two terminals produces two different
files. The fix is `Padding(grid, (0, 0, 0, K_INDENT), expand=False)` in `definition_list.py`, one
argument, and a test that asserts no line of a captured page ends in a space.

### 3.3 Header and panel titles stopped parsing markup; the changelog names only headers

`sushicore/ui/header.py:26` and `sushicore/ui/panel.py:54` wrap the title in `Text(...)`, which
prints it literally. The code they replaced interpolated it into a markup string
(`rule(f"[{style}]{title}")`, `title=f"[{border_style}]{title}"`). Measured through the public
path:

```
$ RichRenderer(...).header("[bold]Setup[/bold]"); .panel("[red]Failed[/red]", "body")
──────────────────── [bold]Setup[/bold] ────────────────────
╭─────────────────── [red]Failed[/red] ────────────────────╮
│ body                                                     │
╰──────────────────────────────────────────────────────────╯
```

`Console.header` and `Console.fail_panel` are existing 0.3.0 surface, so a downstream CLI that
passes a marked-up title now prints the brackets. `docs/reference/CHANGELOG.md:8` records half of
it: "tables lose their frame and headers stop parsing markup". Panel titles do too and the line
does not say so. Table cells still parse markup (`[i]x[/i]` renders as `x`), so the three paths now
disagree about whether a caller's string is markup, and nothing states the rule. The spec's
component table says the `Panel` and `Header` "Look unchanged", which is no longer true of a
marked-up title.

Nothing in `tests/` covers a marked-up title on any of the three, which is why the suite is green.

### 3.4 A `[/]` in help text under `rich_markup_mode="rich"` kills `--help` with a traceback

`sushicore/ui/title.py:27` and `definition_list.py:32` call `Text.from_markup`, and
`from_click._markup` passes rich-mode text through untouched, which is what the spec asks for. The
failure mode when the author's markup is wrong is a `rich.errors.MarkupError` that nothing catches:

```
$ typer.Typer(cls=help_group(...), help="Manage [/] the stack.", rich_markup_mode="rich")
========== rich markup mode rich: a stray [/] in help
exit 1
```

Task 12's Fix A closed the plain-Click half of wave 2 finding 3.1 and closed it well (see 3.6).
The rich half stays: an adopter who writes a bracket in a rich-mode docstring loses `--help`
entirely rather than one line of it. This is the same unguarded call path as 1.3, and one `try`
around `_write_page` would turn both into a degraded page instead of a traceback.
`tests/help/test_markup_safety.py` covers a stray `[/]` only in the escaped (plain Click) direction.

### 3.5 `rich_markup_mode=None` prints a visible backslash; recorded, not fixed

Confirmed report 12 finding 2 and the spec's "Known limit":

```
Arguments
  M  The module.  \[required]
```

Typer escapes its own extras whatever the mode, and the reader escapes them again. Any adopter
setting `rich_markup_mode=None` or `"markdown"` sees this on every leaf page. The spec names it and
report 12 lists it as open, so this is a tracked gap, not a surprise. It is the one place where the
escaping rule needs a decision (unescape Typer's own extras, or refuse non-rich modes loudly).

A related case that turned out fine: a sub-app added with `add_typer` inherits the parent's mode, so
a mixed screen where the root escapes and its children do not cannot arise. Verified with a parent
at `rich_markup_mode=None` and a child at the default; both sides came out escaped.

### 3.6 What I drove and what came out right

A hub-like tree: root with `rich_markup_mode="rich"`, an `add_typer` sub-app, a callback with
`invoke_without_command=True`, an eager `--json` declared before `--help`, a command with
`context_settings={"allow_extra_args": True, "ignore_unknown_options": True}`, a hidden command, an
option with `metavar="N"`, a second argument with a default, and `[cyan]` markup in a description.
`--help` at three levels, plus the bare invocation. No finding on any of it:

```
hub
Manage the stack.                       # [cyan]stack[/cyan] rendered, tags gone

Usage: hub [OPTIONS] COMMAND [ARGS]...

Modules
  add  Bring a module in.
  run  Run anything with extra args.

Commands
  doctor  Check tools.                  # secret, hidden=True, absent

Desktop app
  gui  The desktop application.

Options
  --json                Emit events instead.
  --install-completion  Install completion for the current shell.
  --show-completion     Show completion for the current shell, to copy it or
                        customize the installation.
  --help                Show this message and exit.
```

```
hub add
Bring a module in.

Usage: hub add [OPTIONS] MODULE [BRANCH]

Arguments
  MODULE    The module.  [required]
  [BRANCH]  Branch to use.  [default: main]

Options
  --depth N  Clone depth.  [default: 1]      # metavar honoured
  --dry-run  Show the plan only.
  --help     Show this message and exit.

Examples
  hub add sr  bring sushiruntime in
  hub add se                                  # a second epilog line, no note
```

`hub gui --help` draws the sub-group's own page (`Usage: hub gui [OPTIONS] COMMAND [ARGS]...`), and
`hub gui build --help` draws a leaf page with its Examples. The bare invocation, which goes through
`typer.echo(ctx.get_help())` in the root callback exactly as `hub` does, was byte-identical to
`--help`.

Width. No finding. `COLUMNS=40` reaches Rich and the page wraps:

```
$ COLUMNS=40 python hubish.py add --help
hubish.py add
Bring a module in.

Usage: hubish.py add [OPTIONS] MODULE

Arguments
  MODULE  The module.  [required]
```

and a 200-column console lays the description out on one line. `_draw` takes `raw.width`, and a
non-terminal console reports Rich's default 80.

The logo gate. No finding, every branch of `_logo_visible` measured:

```
color_system None       -> logo: False
color_system windows    -> logo: False
color_system standard   -> logo: False
color_system 256        -> logo: True
color_system truecolor  -> logo: True
no_color=True, truecolor-> logo: False
encoding cp1252         -> logo: False
```

`NO_COLOR=1` and a pipe both suppress it end to end. `FORCE_COLOR=1` piped on this Windows host
gives `is_terminal True, color_system windows`, so the gate closes there too; that is the right
answer for the wrong reason (Rich, not the gate, decided it), and a Linux host with `FORCE_COLOR`
and a pipe would report `truecolor` and draw the logo into a file. The spec says a terminal, and
`FORCE_COLOR` claims to be one, so I do not call it a defect.

Task 12's Fix A. No finding, and it closes wave 2 finding 3.1 for plain Click. Measured:

```
description: 'Do \\[a thing].'
option: ('--kind TEXT', 'Kind.  \\[default: a]')
option: ('--root TEXT', 'Path \\[default: /tmp] and a \\[/] slash.')

t c
Do [a thing].

Usage: t c [OPTIONS]

Options
  --kind TEXT  Kind.  [default: a]
  --root TEXT  Path [default: /tmp] and a [/] slash.
  --help       Show this message and exit.
```

The default no longer disappears and the `[/]` no longer raises.

Windows and Rich 15. `_draw` hard-codes `legacy_windows=False`, so on a console where
`raw.legacy_windows` is true, the page comes back with escape sequences rather than the Win32 calls
Rich would have used:

```
raw.legacy_windows True color_system windows
ANSI escapes in the drawn page: 10
'\x1b[1;33mhub\x1b[0m\nManage.\n\n\x1b[2mUsage: \x1b[0m…'
```

`click.echo` wraps stdout with colorama on Windows and translates those, so I could not turn this
into a visible break, and the plan asked for `legacy_windows=False`. Recording the measurement, not
calling it a defect.

### 3.7 Tests that pass for a reason other than the one they name

- `tests/test_renderer_components.py:21`, `assert not set("".join(lines)) & K_FRAME`, is sound:
  the old table drew `box.HEAVY_HEAD`, whose `┃` is in `K_FRAME`, so the line separates old from
  new. No finding on it.
- `tests/test_typer_help.py:92`, `test_a_command_with_no_panel_lands_under_commands` asserts
  `out.index("Commands") < out.index("  doctor")`. It holds only because the usage line spells the
  placeholder `COMMAND` in capitals; the heading is the sole lower-case occurrence by that accident.
  A search for `"\nCommands\n"` says what the test means.
- `tests/help/test_markup_safety.py:89,96`, `assert "\\" not in text`. Correct today. The page is
  captured at `K_WIDTH = 100` and the strings are short; the assertion is about the whole page
  rather than the entry it names, so a backslash arriving from any other line would also trip it.

No test covers: a failing provider (1.3), a marked-up header or panel title (3.3), a rich-mode
markup error (3.4), trailing whitespace on a page (3.2), or `sushicore.ui.__all__` completeness
(1.5).

---

## 4. Report and metadata honesty

### 4.1 My run of the suite

```
$ python -m pytest tests -q
........................................................................ [ 31%]
........................................................................ [ 62%]
........................................................................ [ 93%]
................                                                         [100%]
232 passed in 0.58s
```

**232 passed.** That matches report 12's final count exactly. It is green only with the fixture of
3.1 in place; without it, `1 failed, 231 passed`.

Line length across every in-scope file:

```
$ awk 'length>100 {print FILENAME": "FNR": "length}' sushicore/renderer.py sushicore/typer_help.py \
      sushicore/help/*.py sushicore/ui/__init__.py tests/test_renderer_components.py \
      tests/test_typer_help.py tests/test_ui_architecture.py tests/help/*.py
sushicore/renderer.py: 43: 102
sushicore/renderer.py: 125: 102
sushicore/renderer.py: 187: 102
sushicore/renderer.py: 263: 102
[end of over-100 list]
```

All four are the `table(...)` signature repeated in the Protocol and the three renderers, all 102
columns, all pre-existing. Report 8 line 44 declares two of them and explains why it left them. The
declaration is honest; the constraint says 100 and four lines are over it.

### 4.2 Report 8, the renderer

Supported, with one invented token. The Step 2 fence (lines 12-19) matches what the tree does: I
reverted `renderer.py`, and the table case fails on `assert '         Modules' == 'Modules'` while
the header and panel cases pass, exactly as pasted. The claim that the local `rich.panel` and
`rich.table` imports are gone is true (`git diff` shows their removal).

Line 27-28:

```
python -m py_compile sushicore/renderer.py tests/test_renderer_components.py
compiled
```

`py_compile` prints nothing on success. "compiled" is a word the worker chose, presented as the
command's output. This is the third report in this programme to do it, after reports 5 and 6 in
wave 2. A `; echo "exit $?"` line, which report 12 uses correctly, costs nothing and carries the
claim.

Line 38 says 192 passed at the time and names the shared tree as the reason the number is not
reproducible. Honest.

### 4.3 Report 9, `HelpPage`

Supported, with two presentation defects in the same fence.

Line 30, inside the Step 4 code fence:

```
... 12 test_from_click tests PASSED
```

That is a summary of output, not output. Line 47:

```
compiled-ok
```

Another invented token for `py_compile`.

The rest holds. `sushicore/help/page.py` is the plan's code character for character, and so is
`tests/help/test_page.py`. Its "Not done" is unusually candid: it says outright that the
implementation was written before the red run and that the red state was produced by moving the
file aside, which is the honest way to report a broken TDD order.

### 4.4 Report 10, `help_group`

The best-evidenced of the four on what it verified, with the same invented-token habit twice.

Line 131-135:

```
$ python -m py_compile sushicore/typer_help.py tests/test_typer_help.py
py_compile ok
```

followed by the sentence "`py_compile` printed nothing, which is its success". The report
contradicts its own fence one line later. Line 140-142 does it again with `scan clean` for the
`awk` check. Both claims are true (I re-ran both), neither is carried by the paste.

Everything else is supported. The Step 2 collection error, the ten-case Step 4 listing and the
version block match what the tree and the environment do. `configfile: pyproject.toml` in the
pasted header is not an invention: pytest 9 prints it for this repository even though
`pyproject.toml` holds no `[tool.pytest.ini_options]` table, which I confirmed with
`--collect-only`.

Two things the report gets right that deserve saying. The "What the user sees" blocks state that
trailing whitespace was stripped when pasting, rather than quietly presenting a clean page; that is
the disclosure 3.2 is built on. And the Typer single-command collapse (lines 56-62) is a real trap
for adopters that the plan did not know about, found by the worker and written down.

Its "Not done" says the 256 branch had no test. Task 12 added it.

### 4.5 Report 12, the four review fixes

Supported throughout, and the strongest of the four on evidence. Every failing run is a real paste
with real assertion text, the probe file is shown created and deleted with a directory listing, the
order-sensitivity of the grouping test is proved by a swap and a restore, and the syntax check is
the one report in this set that pastes a command whose output can be checked:

```
$ python -m py_compile ... ; echo "exit $?"
exit 0
```

Its five findings are all correct as far as I could check them. Finding 1 (`DefaultPlaceholder`) I
confirmed by reading `_markup` and by driving a default-mode Typer app. Finding 2 I reproduced
(3.5). Finding 3, that Fix D needed no production change, is supported by the two in-memory
mutation runs, which is the right way to show a test bites when there is nothing to break.

One claim I disagree with, and it is the one that matters. Finding 4, line 41: "This touches Rich's
caches from a test only; production uses one colour system per process." Section 3.1 shows the
corruption outside pytest with no Typer in the process. The claim about production may hold for a
CLI; it is asserted, not measured, and the fixture that acts on it sits in the wrong file. The
finding is real and well found; its conclusion outran its evidence.

Line 223 notes `sushicore/ui/logo.py` changed at 22:10 while the worker was running and disclaims
it. Correct and useful.

### 4.6 `pyproject.toml`

Both extras resolve. Read first, then dry-run only:

```
$ python -m pip install --dry-run -e ".[test]"
Requirement already satisfied: click>=8.0.0 ... (from typer>=0.12->sushicore==0.4.0) (8.2.1)
Requirement already satisfied: typing-extensions>=3.7.4.3 ... (4.15.0)
Requirement already satisfied: shellingham>=1.3.0 ... (1.5.4)
Would install sushicore-0.4.0

$ python -m pip install --dry-run -e ".[typer]"
Requirement already satisfied: click>=8.0.0 ... (8.2.1)
Requirement already satisfied: colorama ... (0.4.6)
Would install sushicore-0.4.0
```

Nothing was installed. `test = ["pytest>=7.0", "typer>=0.12"]` closes wave 2 finding 3.3: a clean
`pip install -e .[test]` now brings Click in through Typer, so `tests/help/` and
`tests/test_typer_help.py` collect. Version 0.4.0 is set, `rich>=13.0` is still the only runtime
dependency, and `packages.find` with `include = ["sushicore*"]` picks up `sushicore.ui` and
`sushicore.help`, both of which have an `__init__.py`.

Two soft spots, neither breaking:

- `typer>=0.12` is a bound nobody exercised. Report 10 says plainly that nothing ran below Typer
  0.20 or Click 8.2.1, and `_markup`'s `DefaultPlaceholder` unwrapping and `_metavar`'s signature
  sniffing both depend on library internals that moved inside that range. The bound is a claim the
  repository makes to PyPI without a test behind it.
- `requires-python = ">=3.10"` and the classifiers still list 3.10 and 3.11 only, while everything
  here was measured on 3.13. `dataclass(slots=True)` needs 3.10, so the floor is reachable;
  the classifiers are stale, which is pre-existing.

---

## What I did not check

- Anything outside the dispatch's file list. `sushicore/theme.py`, `sushicore/console.py`,
  `sushicore/brand.py`, `sushicore/ui/*.py` (other than reading them to explain a page defect) and
  `tests/ui/` belong to waves 1 and 2 and were reviewed there. The wave 2 items I repeat in 1.7 are
  status checks, not a fresh review of those files.
- Reports 1 to 7 and 11. Wave 2 covered 1 to 7; Task 11 has not run.
- Any Click below 8.2.1, any Typer below 0.20, any Rich below 15.0.0, any Python below 3.13.13.
  Everything measured here is one point in that grid, on win32.
- A real terminal. Every colour, width and encoding result above comes from a `StringIO` console or
  a pipe. Nobody has looked at the logo or the help page in a window at this point in the
  programme, and report 10 says so too.
- `tools/documentation/check_source_comments.py`. The repository still does not carry it, so
  section 2 is a manual read of five source files and five test files, not a checker run.
- Whether the golden `tests/golden/logo_truecolor.txt` should change. It matches; I did not
  regenerate it and would not.
- `hub`'s own adoption. Nothing in `D:/Projects/sushistack` was read or run; the hub-like tree in
  section 3 is my reconstruction from the spec's adoption table, not hub's real `cli.py`.
- The 50 ms import cost of 1.1 as felt by a real CLI. I measured `python -c "import sushicore"`,
  not `hub --version`, which does more.
