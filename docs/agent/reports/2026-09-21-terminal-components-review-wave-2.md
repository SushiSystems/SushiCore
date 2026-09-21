# Review: terminal components, Tasks 1 to 7

Reviewer pass over the uncommitted work of Tasks 1 to 7 in `D:/Projects/sushicore`.
Spec: `docs/agent/specs/2026-09-21-terminal-components-design.md`.
Plan: `docs/agent/plans/2026-09-21-terminal-components.md`.

Out of scope, not reviewed: `sushicore/renderer.py`, `tests/test_renderer_components.py`,
`sushicore/help/page.py`, `tests/help/test_page.py`. Two workers hold them.

Environment: Python 3.13.13, rich 15.0.0, click 8.2.1, typer 0.20.0, pytest 9.1.1, win32.

---

## 1. SOLID shape

### 1.1 A new component passes every architecture check while breaking the protocol

`tests/test_ui_architecture.py:43-97`. The five checks are: one public class named after the file,
frozen dataclass, `__slots__`, `@final` in the decorator list, allowed imports. None of them looks
at `render`'s signature, and none asserts `isinstance(component(...), Component)`.

Scenario: a worker adds `sushicore/ui/spacer.py` with

```python
@final
@dataclass(frozen=True, slots=True)
class Spacer:
    rows: int = 1
    def render(self) -> Text: ...
```

All five parametrised cases pass. `HelpPage._blocks` puts the object in the list, and
`HelpPage.render` calls `block.render(theme)`, which raises
`TypeError: Spacer.render() takes 1 positional argument but 2 were given` at `--help` time. The
guard the spec asks for ("every `ui/` file exports exactly one component") does not check the one
thing that makes it a component. One `assert isinstance(component(<defaults>), Component)` case, or
an `inspect.signature` check for a `theme` parameter, closes it.

### 1.2 `ui/__init__.py` is the list a new component has to edit

`sushicore/ui/__init__.py:5-23`. The spec states the goal as "adding the tenth component adds a file
and edits none of the nine". The eighth component today adds a file and edits two places in a ninth:
the import block and `__all__`. Nothing detects the omission, so a component can exist, pass the
architecture test and be absent from `sushicore.ui`.

This is the orchestrator's file by the plan, so it is a plan-level choice rather than a worker
defect. If the re-export list is kept, a test that compares `set(__all__)` against the `ui/*.py`
stems makes the omission fail; if it is not kept, the file goes back to the docstring the plan gives
in Task 2 and callers import by module path, as `help/page.py` already does.

### 1.3 The two new packages are shaped differently

`sushicore/ui/__init__.py` re-exports eight names with an `__all__`. `sushicore/help/__init__.py:1`
holds a docstring and nothing else. Both are new packages created in this change, both are meant to
have a public surface, and `python-code-style` says an `__init__.py` re-exports the public surface.
Siblings that do the same kind of thing are not shaped the same. Pick one form for both.

### 1.4 `from_click.py` defends against library drift in one place out of four

`sushicore/help/from_click.py:76-81` reads `inspect.signature(make_metavar)` so the module survives
both Click 8.1 and Click 8.2. The same file calls `command.collect_usage_pieces(ctx)` (line 22),
`command.get_params(ctx)` (line 56) and `sub.get_short_help_str(K_SHORT_HELP_LIMIT)` (line 49)
without any guard, while `list_commands`, `hidden`, `rich_help_panel`, `help`, `epilog` and
`get_help_record` are all read through `getattr`. Scenario: Click 8.1's `collect_usage_pieces` has
the same one-argument signature, so today nothing breaks, but the file states two contradictory
policies about the same duck-typed object. Either every call the module makes goes through one
adapter, or `_metavar` drops its signature sniffing and the module declares one supported Click
range.

### 1.5 `model.py`'s dataclasses are not `@final`

`sushicore/help/model.py:8,16`. `python-code-style` says a class not designed for inheritance is
marked `@typing.final`. Every `ui/` component carries it; `HelpSection` and `HelpModel` do not,
although they are frozen data with the same intent. The plan's own code omits it, so this is
inherited from the plan, not invented by the worker.

### 1.6 Hard-coded values

Colour: no finding. Every component reads its colours from `Theme` (`header`, `rule_line`,
`panel_border`, `info`, `muted`, `cmd`). `Logo` is the one exception and the spec grants it: the
brand palette comes from `brand.py` and its docstring says the theme does not reach it.

Layout: `sushicore/ui/definition_list.py:15,28` names the left indent `K_INDENT = 2` and then writes
the column gap as the literal `padding=(0, 2)` four lines below. Two numbers of the same kind, one
named and one not. `sushicore/ui/logo.py:35` puts the indent default `2` in the dataclass field,
which is the right place for it.

### 1.7 Dependency direction

No finding. `sushicore/help/from_click.py` imports only `typing.Any`, `inspect` and `.model`;
neither `click` nor `typer` appears. No file under `sushicore/ui/` imports `sushicore.help`.
`sushicore/help/model.py` imports nothing from sushicore. The architecture test's import rule
(`tests/test_ui_architecture.py:88-97`) passes for all seven component files.

### 1.8 Naming clash: the theme preset called `muted`

`sushicore/theme.py:92` registers a preset named `"muted"`; `sushicore/theme.py:35` adds a token
named `muted`. `get_theme("muted").muted` is now a legal and confusing expression, and a TOML file
saying `theme = "muted"` reads as if it set the token. No behaviour breaks; the collision is worth a
rename of one of the two before 0.4.0 ships the token as public surface.

---

## 2. Humanizer register and `source-comments`

### 2.1 `theme.py:34` states a reason, which source-comments forbids in source

```python
# "dim" quiets text without fixing a colour for an unknown terminal background.
```

This is the argument for choosing `dim`, not a statement of what the field is. `source-comments`
sends the reason to a design document that the comment may cite by path. Plain replacement: delete
the line, or reduce it to the fact, `# Rich style for secondary text and the rule under a table
header.` The worker was right to compress the plan's two `#` lines into one (report 1, "Decisions");
the remaining problem is the content, not the length.

The same line spells "colour" where the comment three lines above it, and the rest of the file,
spells "color". Pick the file's existing spelling.

### 2.2 `tests/ui/test_component.py:12` has a function with no docstring

```python
class _Hello:
    """Draws one word, ignoring the theme it is handed."""

    def render(self, theme: Theme) -> Text:
        return Text("hello")
```

`source-comments` asks for a docstring on every function, private ones included. Plain replacement:
`"""Return the word this stub draws."""`

### 2.3 Helper docstrings are inconsistent across the test files

`tests/test_ui_architecture.py:18,23,32` gives `_pascal`, `_absolute_name` and `_imported_modules` a
verb-first docstring each. `tests/test_brand.py:10` (`_used`), `tests/ui/test_logo.py:13`
(`_small_grid`) and `tests/help/test_from_click.py:9,43,48` (`_tree`, `_root`, `_typer_root`) carry
none. Same kind of helper, two shapes.

### 2.4 `logo.py:38` explains rather than states

```python
"""Return the mark as styled text; the brand's colours do not depend on ``theme``."""
```

The clause after the semicolon answers "why is the parameter unused". Plain replacement: `"""Return
the brand mark as styled text."""` plus, if the unused parameter must be recorded, `@pre`-style
wording in the class docstring rather than a justification in the method.

### 2.5 `help/model.py:18` carries an evaluative tail

```python
"""Holds everything one help screen shows, with no drawing decisions in it."""
```

"with no drawing decisions in it" is a claim about quality, not a fact about the type. Plain
replacement: `"""Holds the data of one help screen."""` The layering claim belongs in the spec,
which already makes it.

### 2.6 `help/from_click.py:1-4` uses the module docstring to argue

```
Reads a Click or Typer command into a HelpModel, by duck typing.

It imports neither Click nor Typer: it asks the command object for what it has.
```

The second sentence is the design rationale. Four lines is inside the six-line limit, so this is a
content point only. Plain replacement: `Reads a Click or Typer command into a HelpModel by asking
the command object for what it has.`

### 2.7 Em dashes in report 2

`docs/agent/reports/2026-09-21-terminal-components-task-2.md` lines 1, 71, 100, 125 use an em dash
four times in a document of roughly 1,500 words, three of them in headings that a colon would carry:
`# Task 2: the Component protocol and the architecture test`, `### Step 2: the failing run`,
`### Step 4: the passing run`, `### The probe: does the guard bite?`. Report 7 line 1 does the same
once, which is inside the budget.

### 2.8 Reports: no other finding

No hidden verbs, no `serves as`, no filler connectives, no evaluative adjectives, no closing summary
paragraph in any of the seven. Every one ends on a "not done" list, which is the right ending.
Report 3's comparison section ("amber spans columns 3 to 15 of 22, the source 3.6 to 15.3") is the
model for putting a number where an adjective wants to go.

Module docstrings: all seven in-scope source files are one to six lines. No two `#` lines in a row,
no TODO, no history line, no separator line anywhere in scope.

---

## 3. Correctness against the spec

### 3.1 Rich markup eats Click's own help text, and one form of it crashes `--help`

Most serious finding. `sushicore/ui/definition_list.py:32` and `sushicore/ui/title.py:25` pass entry
text and the description through `Text.from_markup`. `sushicore/help/from_click.py:70` hands them
whatever Click's `get_help_record` returned, unescaped. Click writes its own square brackets into
that string.

Measured:

```
$ python -c "
import click
from sushicore.help.from_click import build_model
@click.group(name='t')
def t(): pass
@t.command()
@click.option('--kind', default='a', show_default=True, help='Kind.')
@click.option('--n', type=click.Choice(['x','y']), help='Pick.')
def c(kind,n): pass
ctx=click.Context(t, info_name='t')
sub=t.commands['c']
m=build_model(sub, click.Context(sub, info_name='c', parent=ctx))
print(m.options)
"
(('--kind TEXT', 'Kind.  [default: a]'), ('--n [x|y]', 'Pick.'), ('--help', 'Show this message and exit.'))
```

and what the component then draws:

```
$ python -c "... DefinitionList('O',(('--k','Kind.  [default: a]'),)).render(Theme()) ..."
'O\n  --k  Kind.                                                \n'
```

The default silently disappears. A wider probe through `Title`:

```
'Use [OPTIONS].'       -> 'Use [OPTIONS].'
'A [/] slash'          -> RAISED MarkupError closing tag '[/]' at position 2 has nothing to close
'Range [1-9]'          -> 'Range [1-9]'
'Path [default: /tmp]' -> 'Path '
'Bad [not a style] here' -> 'Bad  here'
```

Two distinct failures. A plain-Click CLI with `show_default=True` loses every default from its help
screen. A command whose help text contains `[/]`, for example a description of a path root, makes
`--help` raise `rich.errors.MarkupError` instead of printing.

Typer escapes its own brackets, which is why `tests/help/test_from_click.py:152-153` shows
`"The module.  \\[required]"` and the suite stays green. Plain Click does not escape, and the spec
promises `from_click` reads "a Click command", not only a Typer one. The boundary needs one owner:
either `from_click` escapes what it emits (`rich.markup.escape`) and the components stop calling
`from_markup`, or the components keep markup and `from_click` escapes at the point it reads a Click
record. The spec's Task 6 line "Descriptions and entry text are Rich markup" picks the second, and
nothing implements it. No test in scope covers a bracket coming out of `from_click`.

### 3.2 "Order of first appearance" is alphabetical order for plain Click, and the test cannot tell

`sushicore/help/from_click.py:44` iterates `list_commands(ctx)`. `click.Group.list_commands` returns
`sorted(self.commands)`; `typer.core.TyperGroup` overrides it and returns registration order.
Measured:

```
$ python -c "import click, inspect; print(inspect.getsource(click.Group.list_commands))"
    def list_commands(self, ctx: Context) -> list[str]:
        """Returns a list of subcommand names in the order they should appear."""
        return sorted(self.commands)
```

Consequences:

1. The spec's own worked example is wrong for plain Click. `hub`'s groups are listed as Workspace,
   Modules, Dependencies, Desktop app, Account, "in the order each first appears among the
   commands". Sorted command names give `add` (Modules) before `doctor` (Dependencies) before `gui`
   (Desktop app) before `home` (Workspace), so a plain-Click tree would print Modules, Dependencies,
   Desktop app, Workspace, Account. `hub` is a Typer app, so it gets the spec's order. The two
   readings of "first appearance" differ and nothing records which one holds.
2. `tests/help/test_from_click.py:66-70` passes for the wrong reason. Its tree registers `add`,
   `link`, `init`, `doctor`, `secret`; sorted, that is `add, doctor, init, link`, which yields
   `["Modules", "Commands", "Workspace"]` and `["add", "link"]`. Registration order yields the same
   two answers. Swap the registration of `add` and `link` in `_tree` and the assertion still passes,
   so the test cannot distinguish the behaviour the docstring names from alphabetical sorting.
   `test_a_typer_app_groups_by_its_panels_and_keeps_typer_help_records` (line 141) has the same
   ambiguity: `grow` sorts before `rest` and is registered before it.

A case with a tree whose registration order and sorted order differ would pin the intent.

### 3.3 The suite cannot be installed as the plan describes

`pyproject.toml:32` is still `test = ["pytest>=7.0"]` and there is no `typer` extra.
`tests/help/test_from_click.py:4` imports `typer` at module scope and line 3 imports `click`.
Scenario: a clean `pip install -e .[test]` followed by `python -m pytest tests -q` stops at
collection with `ModuleNotFoundError: No module named 'click'`. The plan hands `pyproject.toml` to
the orchestrator (plan line 31), so this is a missing orchestrator step rather than a worker defect,
but until it lands the suite only runs in an environment that happens to carry Typer.

Independently: the Typer case is the only thing in `tests/help/` that needs Typer, and the spec says
`sushicore/help/` is independent of Typer. Either the case moves to `tests/test_typer_help.py`
(Task 10's file) or it guards itself with `typer = pytest.importorskip("typer")`, so a Typer-less
install still proves the Click reader.

### 3.4 Windows, `NO_COLOR` and encoding

No finding. Checked, all green:

```
$ NO_COLOR=1 python -m pytest tests/ui tests/test_ui_architecture.py -q
56 passed in 0.12s
$ FORCE_COLOR=1 python -m pytest tests/ui -q
20 passed in 0.10s
$ TERM=dumb python -m pytest tests/ui -q
20 passed in 0.10s
$ COLUMNS=40 python -m pytest tests/ui -q
20 passed in 0.09s
```

`tests/ui/capture.py:16-23,31-38` passes `legacy_windows=False` and `no_color=False` explicitly on
both consoles, which is what keeps the rounded box characters in `test_panel.py` and the golden
bytes in `test_logo.py` stable on this host. Report 2 sections 1 and 2 document both fixes with
their own measurement; that work holds up.

Golden file: `tests/golden/logo_truecolor.txt` is 5,589 bytes, LF only, 10 lines, UTF-8. The
repository has `core.autocrlf=true` and no `.gitattributes`, so the file will sit on disk as CRLF
after a fresh clone. `Path.read_text` translates universal newlines, so the comparison still holds:

```
$ python -c "... p.write_bytes(src.replace(b'\n', b'\r\n')); print(back == original)"
crlf file read equals lf content: True
```

A `tests/golden/** -text` line in a `.gitattributes` would keep the bytes on disk identical to the
bytes committed and keep `git diff` quiet, but nothing fails without it.

Report 4's note that a print of the logo to a cp1252 stdout raises `UnicodeEncodeError` is accurate
and does not touch the tests, which compare strings in memory. The console-encoding gate the spec
describes belongs to `typer_help` (Task 10) and is not in scope here.

### 3.5 An odd grid silently drops its last row

`sushicore/ui/logo.py:40` zips the even and odd slices of `K_LOGO_PIXELS`. With 21 rows, row 20 is
never drawn and nothing says so. `tests/test_brand.py:18` asserts the committed grid has an even
count, so today the data cannot trigger it; a future retrace with an odd height would lose a row
quietly. Report 4 names this in its "not done" list, correctly. A `@pre` on `render` or a pad in
`_cell`'s caller closes it.

### 3.6 Spec items delivered

No finding on these, checked individually:

- `Theme().muted == "dim"`, `as_rich_styles()["muted"]`, `merged({"muted": ...})`,
  `Console.theme is theme` (`tests/test_theme_muted.py`, 4 passed).
- Four brand colours, rectangular grid, even row count, palette keys only
  (`tests/test_brand.py`, 7 passed).
- Seven component files, each a `@final` frozen slots dataclass with `render(theme)`.
- `Table` uses `box.SIMPLE_HEAD`, `show_edge=False`, `header_style=theme.header`,
  `border_style=theme.muted`, exactly as the spec's "Table look is one place" paragraph asks.
- `Usage` prints its string literally through `Text.assemble`, so `hub [OPTIONS] COMMAND [ARGS]...`
  survives. This is the one place the markup problem of 3.1 does not apply, and it is the right
  choice.
- `build_model` produces the eight fields with the names Tasks 9 and 10 were told to expect.
- Hidden commands are dropped; a non-string `rich_help_panel` falls back to `Commands`.

---

## 4. Report honesty

### 4.1 My own run

```
$ python -m pytest tests -q
........................................................................ [ 36%]
........................................................................ [ 72%]
......................................................                   [100%]
198 passed in 0.50s
```

That count includes the two in-flight tasks. Scoped to the files in this review:

```
$ python -m pytest tests/test_theme_muted.py tests/test_brand.py tests/test_ui_architecture.py \
      tests/ui tests/help/test_from_click.py -q
........................................................................ [ 91%]
.......                                                                  [100%]
79 passed in 0.21s
```

**The count I got: 79 in scope, 198 for the whole tree.** 79 reconciles exactly: 4 (`test_theme_muted`)
+ 7 (`test_brand`) + 36 (architecture: 1 protocol case, 5 checks over 7 component files) + 20 (the
eight `tests/ui/` files) + 12 (`test_from_click`). 198 is 79 + the 110 baseline the plan names + 9
from Tasks 8 and 9.

```
$ awk 'length>100 {print FILENAME": "FNR": "length}' <every in-scope source and test file>
LINECHECK_DONE
```

No line over 100 columns anywhere in scope.

### 4.2 Report 1 (Theme and Console)

Supported. The Step 2 failure text, the Step 4 counts and the `py_compile` line all match what the
files do. Its "Decisions" note about compressing the plan's two `#` lines is honest and correct
about the rule, and its "Not done" correctly records that no comment checker was run. One
qualification the report already makes itself, at line 25: the fourth test failed on
`Theme(muted=...)` in its own setup, not on the missing `Console.theme`, so `Console.theme` was
never seen failing for its own reason. Naming it is the right call; the gap stays.

### 4.3 Report 2 (Component protocol and architecture test)

**Two claims are false of the tree as it stands.** Lines 62-67 ("it checks neither `@final` nor
`slots`") and line 221 ("The `@final` and `slots=True` constraints are unguarded") do not describe
`tests/test_ui_architecture.py`, which contains `test_component_uses_slots` (line 71) and
`test_component_is_marked_final` (line 76). File mtimes put the report at 21:54:04 and the test file
at 21:56:06, so the two cases were added after the report was written, by the orchestrator or
another hand. No report in the set records adding them. Reports 4, 5 and 6 all run against the
five-check version and say so. Nothing is wrong with the code; the written record has a two-minute
hole in it and report 2's "not done" section now misinforms the next reader.

Line 203-205 is the other soft spot:

```
$ awk 'length>100 {print FILENAME": "FNR": "length}' ...
over-100 lines listed above (none if blank)
```

The fenced block holds an explanatory sentence, not the command's output. The claim is true (I
re-ran the check), but the paste does not carry it.

Everything else in report 2 is supported and unusually well evidenced. The two probe runs, the
second one deliberately chosen so each rule fails on its own assertion rather than on an import
error, are exactly what "seen failing for the right reason" means. The probe removal is shown with a
directory listing.

### 4.4 Report 3 (brand data)

Supported, and the strongest of the seven on evidence. Sample counts per palette region, the crop
box, the classifier thresholds and the reason the plan's nearest-colour rule was replaced are all
concrete. The committed `K_PALETTE` and `K_LOGO_PIXELS` match the report's "Final `K_LOGO_PIXELS`"
block character for character, including the measured nori `#1a1c20` rather than the plan's
`#1d1e20`. Its "Not done" correctly flags that the full suite was not run and that the look is
unapproved.

One consequence the report does not draw: `tests/ui/test_logo.py:10` still pins the plan's old nori
`#1d1e20` in its local `K_PALETTE`, which the monkeypatched cases use. That is deliberate isolation
(the small grid is a fixture, not the brand), but the two files now disagree on the value of `n`
with nothing saying they may.

### 4.5 Report 4 (Logo)

Supported, with one presentation defect. Line 48 sits inside the Step 4 code fence:

```
(plus the protocol case and the header.py, panel.py, table.py cases, all PASSED)
```

That is a summary sentence dressed as terminal output. The count on the next line, 26 passed, is
plausible and the tests do pass now, but the fence is not a paste.

The report is candid where it matters: it says the golden was checked with `wc -l`, `od -c` and
`grep -c` rather than read back with the Read tool as the plan asked, it names the cp1252
`UnicodeEncodeError`, and it names the odd-row gap of 3.5 above. The ten-row plain-text rendering it
includes matches what `Logo(indent=0)` draws from the committed grid.

### 4.6 Report 5 (Header, Panel, Table)

**Weakest paste of the seven.** Line 38 inside the Step 4 fence:

```
tests/test_ui_architecture.py::... [header.py], [panel.py], [table.py] (and [logo.py], Task 4's file): all 5 parametrised checks PASSED
```

Prose in a code fence again. The syntax check, lines 42-48, is worse: the command is given as
"`python -m py_compile` on the six files I wrote", with no file list, and the output is the token
`PYCOMPILE_OK`, which is an echo the worker chose. Constraint 5 asks for the command and its output;
neither is here. The claim holds (I re-ran the whole suite), but nothing in the report establishes it.

Its honest part: lines 50-62 say plainly that `python -m pytest tests -q` could not finish because
Task 6's test files were on disk without their implementations, and give the `--ignore` run and its
count instead of hiding the collection errors. That is the right way to report a cross-worker
collision.

### 4.7 Report 6 (Title, Usage, DefinitionList)

Supported, thinnest of the seven. It pastes only the last line of the Step 4 run (`43 passed`) and
the token `py_compile exit 0`, and reports the over-100-column check as "awk check printed nothing"
in prose rather than as a paste. The seven case count matches the files (3 + 1 + 3). The three
components are the plan's code unchanged, which I verified line by line.

The report claims "The plan's tests are unchanged in what they assert", and that holds: the two
wrapped assertions in `test_title.py:16-17` and `test_usage.py:8-9` introduce a local variable and
change nothing else.

### 4.8 Report 7 (HelpModel and the Click reader)

Supported, and the three deviations it documents are all correct and all improvements on the plan.
`_text` guarding `help`, `epilog`, `rich_help_panel` and `param.help` against Typer's truthy
`DefaultPlaceholder` is a real defect the plan would have shipped. `_metavar` reading
`inspect.signature` rather than catching a `TypeError` that could have come from inside the call is
the right instinct, and it is stated as such.

Two things the report asserts that deserve a mark. Line 111: "Typer escapes the markup itself, so
the reader passes both strings through untouched." True for Typer, and the report treats it as
closing the question. Section 3.1 above shows plain Click does not escape and the text is lost or
raises. The report's own test data contains the evidence (`\\[required]` from Typer, versus the
unescaped Click records the rest of the file works with) and does not follow it.

Line 138: "The reader was exercised against Click 8.2.1 and Typer 0.20 only" and the `make_metavar`
branch for older Click was never run. Correctly named as not done.

### 4.9 Whole-suite counts across reports

Report 2 says 124, report 4 says 167, report 6 says 177, report 7 says 189, and I get 198. The
reports disagree because each ran while other workers were writing files into the same tree, and
report 2 says so explicitly with its arithmetic. Report 4's 167 is the one I could not reconstruct
from any combination of the files that existed at 21:57. I do not call it dishonest; I call it
unreproducible, which is what a shared working tree does to a whole-suite count. The number that
matters is the one in 4.1.

---

## What I did not check

- `sushicore/renderer.py`, `tests/test_renderer_components.py`, `sushicore/help/page.py`,
  `tests/help/test_page.py`, and reports 8 and 9, which exist in the tree. Out of scope by the
  dispatch; two workers hold them.
- Whether the traced logo grid looks like `sushiweb/apps/web/public/images/logo-icon.png`. Report 3
  gives a column-by-column comparison and the preview PNG path; the owner approves the look, and I
  did not open either image.
- `tools/documentation/check_source_comments.py`. The repository does not carry it, so the
  `source-comments` findings above are a manual read of the seven source files and ten test files in
  scope, not a checker run.
- Behaviour on Click 8.1 or any Rich below 15.0.0. Everything measured here is Click 8.2.1,
  Typer 0.20.0, Rich 15.0.0, Python 3.13.13, win32. The plan's tech stack line says Rich 13+ and
  nothing pins it; report 2 raises the same point.
- `pyproject.toml`, `README.md`, `docs/README.md` and `docs/reference/CHANGELOG.md` beyond the one
  fact in 3.3 that the `typer` extra is absent. The plan assigns them to the orchestrator and no
  worker touched them.
- Task 10 and Task 11, and the console gate (terminal, `no_color`, colour system, encoding) that
  decides whether the logo is asked for. That logic does not exist yet.
- Whether a golden file regeneration is warranted. I did not regenerate it and would not; the golden
  matches and the rule is to report a difference, not to rewrite the file.
