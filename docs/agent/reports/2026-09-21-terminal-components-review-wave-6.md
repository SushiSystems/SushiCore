# Review: terminal components, Wave 6 (Tasks 13 to 18)

Reviewer pass over the wordmark, the glow, the background decision, the logo choice and the
second round of review fixes. Sources: the spec
`docs/agent/specs/2026-09-21-terminal-components-design.md`, the plan
`docs/agent/plans/2026-09-21-terminal-components.md` (Global Constraints and Wave 6), the two
earlier reviews (`...-review-wave-2.md`, `...-review-wave-4.md`) and the worker reports 13 to 18.

Everything below was measured on this checkout with `PYTHONPATH=D:/Projects/sushicore`. The work
was committed while I was reading it (`442d505`, `d68be55`, `530200f`, `8f76a40`, `2ffc6bd`); the
files I quote are the committed ones.

---

## 1. SOLID shape

### 1.1 `LazyConsole` cannot serve `help_group`, so `--help` silently loses its page

`sushicore/cli_console.py:21-26`. `_ATTRS` lists the console attributes a CLI reaches through
`LazyConsole.attribute`. It has `console` and `accent` but neither `theme` (added in Task 1) nor
`dark_background` (added in Task 14). `LazyConsole` also has `__slots__` and no `__getattr__`, so
plain attribute access fails as well.

`_write_page` (`sushicore/typer_help.py:102-105`) reads all three: `console.console`,
`console.dark_background`, `console.theme`. A CLI whose provider hands back its `LazyConsole` —
the obvious reading of the spec's "a callable returning the CLI's `Console`" — gets the guard,
not the page:

```
lazy.theme -> AttributeError 'LazyConsole' object has no attribute 'theme'
lazy.dark_background -> AttributeError 'LazyConsole' object has no attribute 'dark_background'
attribute('theme') -> AttributeError no console attribute 'theme'
attribute('dark_background') -> AttributeError no console attribute 'dark_background'
provider returns the LazyConsole -> exit 0 | sushicore page? False
```

The failure is quiet: exit 0, one warning on a logger nothing configures, Typer's own screen. This
is Wave 5's first step, and `sushicore` is the repository that owns both halves. Either `_ATTRS`
gains the two names, or `_write_page` states the Protocol it needs and the spec says the provider
returns `lazy.get()`.

### 1.2 `Logo.width` and `Logo.render` measure the wordmark by two different rules

`sushicore/ui/logo.py:102` computes the wordmark's share of the width as
`len(K_WORDMARK_PIXELS[0])`, the first row. `_centred` (`logo.py:36`), which `render` goes
through, uses `max(len(row) for row in grid)`. For the committed rectangular grid the two agree.
For anything else they do not. With the first wordmark row shortened to `"ww"`:

```
--- ragged wordmark (row 0 shorter than the rest) ---
width property = 20  rendered widest row = 68
```

Task 17's report says "`width` and `render` both call `_trimmed(...)`, so they cannot disagree".
That is true of the mark and false of the wordmark, which `width` never routes through the same
helper. `width` should measure the grid `_pixels` will actually build.

Only `tests/test_brand.py::test_every_wordmark_row_has_the_same_width` keeps this latent, and that
test guards the data, not the code.

### 1.3 `Logo` reads its grids from module globals, and its helpers are shaped two ways

`logo.py:100,102,108` and `_pixels` at `logo.py:62` reach for `K_MARK_PIXELS`,
`K_WORDMARK_PIXELS`, `K_PALETTE` and `K_GLOW_PALETTE` as module globals. `python-code-style`
(class shape, rule 2) asks for dependencies through `__init__` and no hidden globals. The cost is
concrete: a second mark — a compact one for a 40-column console, say — cannot be a second `Logo`
instance; it is an edit to `logo.py` and to `brand.py`. Report 13 records the global reads as a
deliberate choice, and its reason is the monkeypatch in the tests, which is the tests shaping the
code.

The helpers are also inconsistent with each other. `_trimmed(grid, colours)` and
`_centred(grid, rows)` take their grid as an argument; `_pixels(mark, wordmark)` takes the mark as
an argument and then reaches for `K_WORDMARK_PIXELS` itself. Siblings that do the same kind of
thing are shaped the same; these two are not.

### 1.4 `_trimmed` returns an untrimmed grid when nothing is inked, and `width` then counts it

`logo.py:47-49`. When no pixel has a colour the function returns `rows` before trimming, and
without the bottom pad that keeps the row count even. `width` then counts columns that draw
nothing:

```
--- all-transparent mark ---
width = 6 rows = 0 []
with wordmark: width = 58 rows = 8 max = 58
```

Six columns claimed, nothing drawn. `choose_logo` would reserve room for a logo that is not there.
The committed mark always has colour, so this needs a monkeypatch to reach; it is the same
`width`/`render` split as 1.2, in the other branch.

`Logo(wordmark=False)` on an empty grid raises instead:
`ValueError: max() iterable argument is empty` from `logo.py:45`. An empty grid is not a real
input, but the two behaviours (silently wrong, and raising) come from adjacent lines.

### 1.5 `choose_logo`, `is_dark_background` and `Console.dark_background`: no finding

- `sushicore/help/logo_choice.py` is a brick. One responsibility, both inputs keyword-only, no
  width written as a number, the candidate's own `width` used for the comparison. A third variant
  costs one entry in the candidate tuple and touches nothing else.
- `sushicore/terminal_background.py` imports only `typing.Mapping`. `config.py:35` imports
  `K_AUTO` and `K_VALUES` from it, so the set of valid values lives in one place and the arrow
  points down. `is_dark_background` takes `environ` rather than reading `os.environ`, so the tests
  need no monkeypatch of the process.
- `Console` (`sushicore/console.py:24-56`) stores the bool and returns it. It reads nothing.
  `build_console` (`sushicore/__init__.py:76`) is the only caller of `is_dark_background`, and it
  is the only place `os.environ` is touched for this.
- Dependency direction holds: `typer_help` → `help` → `ui` → `theme`/`brand`;
  `config` → `terminal_background`; nothing points back. `tests/test_ui_architecture.py` still
  passes with `logo_choice.py` added, because no `ui/` file imports `help`.

### 1.6 Cost of adding a component or a logo variant

A tenth component costs its own file, one import and one `__all__` entry in
`sushicore/ui/__init__.py`, and its test file. `tests/test_ui_architecture.py` globs `ui/*.py`, so
it needs no edit. That is what the spec promised.

A new logo variant costs `brand.py` (the grid), `ui/logo.py` (a field, plus `width` and `render`
branches), `help/logo_choice.py` (one candidate), `tests/ui/test_logo.py` and a golden. Two of
those five are the price of 1.3.

### 1.7 Carried from wave 4, still open

Each was measured by the previous reviewer and is unchanged in this tree:

- `sushicore/help/model.py:9,17`: `HelpSection` and `HelpModel` are still not `@typing.final`.
- `sushicore/help/from_click.py:83`: `inspect.signature(make_metavar)` is still the one place
  library drift is defended against, while `get_params`, `get_short_help_str` and
  `collect_usage_pieces` are called raw. Task 16 touched this file and left both policies.
- `sushicore/ui/definition_list.py:15,28`: `K_INDENT = 2` is named, `padding=(0, 2)` is not.
- `sushicore/theme.py:35,92`: the preset named `"muted"` still sits beside the token `muted`.

---

## 2. Humanizer register and source comments

### 2.1 The reason-after-the-punctuation shape came back, in three new places

Task 16's item 5 removed exactly this from `renderer.py`, and Wave 6 added it elsewhere.

`sushicore/terminal_background.py:33`:

> `# An unreadable value is unknown, and unknown is not dark: a light terminal keeps its look.`

The clause after the colon is why the rule was chosen. `source-comments` sends that to a design
document. Plain: `# An unreadable value is not dark.`

`sushicore/ui/logo.py:106`:

> `"""Return the logo as styled text; its colours come from the brand, not from ``theme``."""`

The clause after the semicolon answers "why is `theme` unused", and `not from theme` is a
corrective contrast on top. Plain: `"""Return the logo as styled text, two pixel rows per
terminal row."""` — which is what the plan wrote at line 2005.

`sushicore/console.py:29-30`:

> `dark_background: What the caller decided about the terminal's background;`
> `    this console never reads the environment to find out.`

`Args:` is for a rule the caller must keep. "This console never reads the environment" is a fact
about the class, not about the caller, and it is a design reason. Plain:
`dark_background: Whether the terminal's background is dark.`

`sushicore/typer_help.py:104`:

> `# The page is drawn in full before the one write, so a failure leaves the formatter untouched.`

The invariant is the first clause; `so …` is the reason. Plain:
`# The page is drawn in full before the single write.`

### 2.2 `from_click.py`'s module docstring still carries the tail it was told to drop

`sushicore/help/from_click.py:1`:

> `"""Reads a Click or Typer command into a HelpModel by asking the command object for what it has.`

Task 16's item 5 asked for "a statement of what the module does". `by asking the command object
for what it has` is how it does it, and it is the surviving half of the sentence the wave-2 review
flagged. Plain: `"""Reads a Click or Typer command into a HelpModel."""`

### 2.3 `docs/README.md:58-60` states the wrong threshold and stops short of the answer

> `It is the roll with `SUSHI SYSTEMS` beside it when the console is 72 columns wide (68 without`
> `the glow), and the roll alone when it is narrower.`

"when the console is 72 columns wide" reads as exactly 72; the rule is at least 72. And "the roll
alone when it is narrower" is false below 16 columns (20 with the glow), where nothing is drawn —
measured in 3.1. Plain:

> The lockup needs 72 columns, or 68 without the glow. Below that the roll prints alone, which
> needs 20 columns with the glow and 16 without; below that, nothing.

### 2.4 The changelog is still not newest first, and one line carries two changes

`docs/reference/CHANGELOG.md:3` says "newest first". Lines 6 to 20 are `2026-09-21`, line 21
onward is `2026-09-22`. The wave-4 review reported this at its 2.1 and the block was extended
rather than moved.

Format otherwise holds: no line exceeds 240 characters (the longest is 193, line 23), every entry
is one sentence, past tense, path in backticks, no nesting, no "why".

One entry is two changes:

> `- 2026-09-21 — Kept markup in `Header` and `Panel` titles and stopped `import sushicore`
>   loading Rich (...).`

Those are two of Task 16's five items and belong on two lines. Nothing in the file records the
definition-list padding fix or `tests/conftest.py`, which is defensible for a test-only change but
leaves Task 16 represented by half of itself.

### 2.5 `docs/README.md` indexes none of the 23 documents this work added

The commit `442d505` added a spec, a plan and 21 reports under `docs/agent/`. `docs/README.md`
names exactly one document in the whole file (line 107, the hub design spec). The documentation
rule is that every document is reachable from the manual index. This is the same commit that
claims to "describe the terminal components", so the index is where the gap shows.

### 2.6 The spec's package layout no longer matches the package

`docs/agent/specs/2026-09-21-terminal-components-design.md:116-125` lists `brand.py`, `theme.py`,
`renderer.py`, `typer_help.py`, `ui/` and `help/`. It omits `terminal_background.py` and
`help/logo_choice.py`, both of which the same document describes in prose at lines 65-69. The
dependency sentence at line 127 also stops at `renderer → ui` and never places
`config → terminal_background`.

The rest of the spec's new "The logo" section is accurate. I checked every number in it against
the code: 18 by 16 mark, 50 by 16 wordmark, widths 72 / 68 / 20 / 16, `SUSHI` in the terminal
foreground, `SYSTEMS` amber, trimming on the mark only, the four-part visibility gate, and the
`[/]` known limit. All hold.

### 2.7 Report register

The six reports read as work notes, which is the right register, and they lead with the answer.
Two nits:

- Report 16 line 37: `**The plan and the review are wrong on one point.**` Bold belongs on the
  term being defined, not on the sentence the author wants noticed. The sentence is already first
  in its paragraph, which is the emphasis it needs.
- Report 15 line 58: "Review finding 3.4 reads as a sushicore defect; it is a Typer one that
  sushicore inherits." Correct and well evidenced; no change needed, noted because it is the
  model the other reports should follow when they disagree with the plan.

No em dash runs, no filler connectives, no closing summary paragraph in any of the six.

---

## 3. Correctness

Everything in this section was driven, not read. Commands and output are pasted as they came.

### 3.1 The logo at the boundary widths

A hub-like tree (`add` under `Modules`, `doctor` ungrouped, a `gui` sub-app), `rich_markup_mode="rich"`,
drawn through `help_group` on a forced truecolour terminal, colour codes stripped for this report:

```
=== dark=True width=200 exit=0 logo_rows=8 widest_logo_row=72 widest_any_line=104
=== dark=True width=72 exit=0 logo_rows=8 widest_logo_row=72 widest_any_line=72
    |     ▄▄▀▀▀▀▀▀▀▀▄      ▄█▀▀▀▀ ██  ██ ▄█▀▀▀▀ ██  ██ ██|
    |   ▄▀▀▀▀▀▀▀▀▀██▀▀▄    ▀█▄▄▄  ██  ██ ▀█▄▄▄  ██▄▄██ ██|
    |  ▄▀▀██▀▀▀▀▀██▀████       ██ ██  ██     ██ ██  ██ ██|
    |  ███████████▀██████  ▀▀▀▀▀   ▀▀▀▀  ▀▀▀▀▀  ▀▀  ▀▀ ▀▀|
    |  ██████████████████   ▄▄▄▄▄ ▄▄  ▄▄  ▄▄▄▄▄ ▄▄▄▄▄▄ ▄▄▄▄▄▄ ▄▄    ▄▄  ▄▄▄▄▄|
    |  █████▀▀██▀▀████▀▀▀  ██     ▀█▄▄█▀ ██       ██   ██     ███▄▄███ ██|
    |   ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀     ▀▀▀█▄   ██    ▀▀▀█▄   ██   ██▀▀   ██ ██ ██  ▀▀▀█▄|
    |     ▀▀▀▀▀▀▀▀▀▀▀      ▄▄▄▄█▀   ██   ▄▄▄▄█▀   ██   ██▄▄▄▄ ██    ██ ▄▄▄▄█▀|
=== dark=True width=71 exit=0 logo_rows=8 widest_logo_row=20 widest_any_line=71
=== dark=True width=68 exit=0 logo_rows=8 widest_logo_row=20 widest_any_line=68
=== dark=True width=67 exit=0 logo_rows=8 widest_logo_row=20 widest_any_line=67
=== dark=True width=20 exit=0 logo_rows=8 widest_logo_row=20 widest_any_line=20
=== dark=True width=19 exit=0 logo_rows=0 widest_logo_row=0 widest_any_line=19
=== dark=True width=16 exit=0 logo_rows=0 widest_logo_row=0 widest_any_line=16
=== dark=True width=15 exit=0 logo_rows=0 widest_logo_row=0 widest_any_line=15
=== dark=False width=200 exit=0 logo_rows=8 widest_logo_row=68 widest_any_line=104
=== dark=False width=72 exit=0 logo_rows=8 widest_logo_row=68 widest_any_line=72
=== dark=False width=71 exit=0 logo_rows=8 widest_logo_row=68 widest_any_line=71
=== dark=False width=68 exit=0 logo_rows=8 widest_logo_row=68 widest_any_line=68
    |                  ▄█▀▀▀▀ ██  ██ ▄█▀▀▀▀ ██  ██ ██|
    |   ▄▄▀▀▀▀▀▀██▄    ▀█▄▄▄  ██  ██ ▀█▄▄▄  ██▄▄██ ██|
    |  ▄██▀▀▀▀▀██▀██       ██ ██  ██     ██ ██  ██ ██|
    |  █████████▀████  ▀▀▀▀▀   ▀▀▀▀  ▀▀▀▀▀  ▀▀  ▀▀ ▀▀|
    |  ██████████████   ▄▄▄▄▄ ▄▄  ▄▄  ▄▄▄▄▄ ▄▄▄▄▄▄ ▄▄▄▄▄▄ ▄▄    ▄▄  ▄▄▄▄▄|
    |  ███▀▀██▀▀████▀  ██     ▀█▄▄█▀ ██       ██   ██     ███▄▄███ ██|
    |   ▀▀▀▀▀▀▀▀▀▀▀     ▀▀▀█▄   ██    ▀▀▀█▄   ██   ██▀▀   ██ ██ ██  ▀▀▀█▄|
    |                  ▄▄▄▄█▀   ██   ▄▄▄▄█▀   ██   ██▄▄▄▄ ██    ██ ▄▄▄▄█▀|
=== dark=False width=67 exit=0 logo_rows=6 widest_logo_row=16 widest_any_line=67
=== dark=False width=20 exit=0 logo_rows=6 widest_logo_row=16 widest_any_line=20
=== dark=False width=19 exit=0 logo_rows=6 widest_logo_row=16 widest_any_line=19
=== dark=False width=16 exit=0 logo_rows=6 widest_logo_row=16 widest_any_line=16
=== dark=False width=15 exit=0 logo_rows=0 widest_logo_row=0 widest_any_line=15
widths: {'lockup glow': 72, 'lockup plain': 68, 'mark glow': 20, 'mark plain': 16}
```

Every transition is where `Logo.width` says it should be, exit code is 0 at every width, and **no
line of any page is wider than its console** (`widest_any_line` never exceeds `width`).

One drift, and it is in the plan rather than the code. Task 15's acceptance criterion and the
Wave 6 preamble (`plan:1893`, `plan:2115`) both say "nothing below 20 columns". After Task 17's
trim the plain mark is 16 columns, so on a light terminal the logo prints at 16, 17, 18 and 19 —
see `dark=False width=19 … logo_rows=6`. The behaviour is right and the criterion is stale; the
plan's two sentences should say 20 with the glow, 16 without. `docs/README.md` inherits the same
gap (2.3).

A second observation, not a defect: on a dark terminal at widths 68 to 71 the glowing lockup (72)
does not fit and the glowing mark (20) is shown, although the *plain* lockup (68) would. That is
`choose_logo`'s stated rule — the glow follows the background, and the candidates are built at the
chosen glow — but it means a dark 70-column terminal loses the wordmark that a light one keeps.

### 3.2 `build_console` and the background decision

```
sushicore from D:\Projects\sushicore\sushicore\__init__.py
TOML background=dark, no env                  -> dark_background=True
COLORFGBG=15;0, no setting                    -> dark_background=True
COLORFGBG=0;15, no setting                    -> dark_background=False
SUSHI_CLI_BACKGROUND=light                    -> dark_background=False
SUSHI_CLI_BACKGROUND=light + COLORFGBG=15;0   -> dark_background=False
SUSHI_CLI_BACKGROUND=dark over TOML           -> dark_background=True
nothing at all                                -> dark_background=False
COLORFGBG=15;default;0                        -> dark_background=True
COLORFGBG=0;7 (light fg on grey bg)           -> dark_background=False
COLORFGBG=7;8                                 -> dark_background=True
COLORFGBG=15;9                                -> dark_background=False
COLORFGBG=default;default                     -> dark_background=False
SUSHI_CLI_BACKGROUND=DARK (uppercase)         -> dark_background=False
SUSHI_CLI_BACKGROUND=' dark ' (spaces)        -> dark_background=False
```

Every case the task asked for is right. The last two are the finding:
`SUSHI_CLI_BACKGROUND=DARK` and `SUSHI_CLI_BACKGROUND=" dark "` fall outside `K_VALUES`, become
`"auto"` at `config.py:117-118`, and the user gets a light terminal with no message. The same
holds for `[cli] background = "Dark"`. `color` behaves identically, so the siblings match and this
is not a regression; it is a trap a shell variable walks into far more often than a TOML key. One
`.strip().lower()` in `load_appearance`, applied to both keys, closes it.

### 3.3 Is the `COLORFGBG` rule right?

`K_DARK_INDICES = {0,1,2,3,4,5,6,8}` at `terminal_background.py:13` is vim's rule for the same
variable: vim reads the last `;`-separated field and calls the background dark when it is 0 to 6
or 8. Taking the last field with `rsplit(";", 1)` covers both writing conventions I know — the two
field `fg;bg` that rxvt-unicode and Konsole emit (`15;0`, `0;15`) and the three-field
`fg;default;bg`. Index 7 is light grey and is treated as light, index 8 is dark grey and as dark,
which is what vim does and what a reader of the variable would expect.

What I could not verify here, and what would settle each:

- Whether any terminal emits the fields in the other order (`bg;fg`). I know of none; a survey of
  the terminals the team actually uses would settle it, and the cost of being wrong is a glow on a
  light terminal.
- The behaviour of a real Windows Terminal, a real Konsole and a real urxvt. This session has no
  interactive terminal, so every run above is a forced Rich console.
- Staleness. `COLORFGBG` is set once when the shell starts and is inherited over `ssh`, into
  `tmux` and across a theme change, so it can describe a terminal that no longer exists. The
  `[cli] background` key is the answer and the docs already say so.

### 3.4 `Logo` at the edges

```
{}                                         width= 68 rendered_max= 68 rows=8
{'indent': 0}                              width= 66 rendered_max= 66 rows=8
{'wordmark': False}                        width= 16 rendered_max= 16 rows=6
{'indent': 0, 'wordmark': False}           width= 14 rendered_max= 14 rows=6
{'glow': True}                             width= 72 rendered_max= 72 rows=8
{'indent': 0, 'glow': True}                width= 70 rendered_max= 70 rows=8
{'wordmark': False, 'glow': True}          width= 20 rendered_max= 20 rows=8

--- odd-row mark after trimming ---
odd trim width = 4 rendered rows = 3 ['  ▀', '  ▀', '  ▀▀']
```

`indent=0` and the wordmark-less logo are exact: the widest rendered row equals `width` in all
seven combinations. An odd trimmed row count gains its transparent bottom row and pairs cleanly.
The ragged-wordmark and all-transparent cases are findings 1.2 and 1.4.

### 3.5 The wordmark's symmetry

The plan (Task 18, line 2107) claims `U H I T Y M` are mirror-symmetric and `S` is symmetric under
a half turn. Reading `K_WORDMARK_PIXELS` and cutting the letters at the blank columns:

```
S: 6x7  mirror=no   halfturn=YES
U: 6x7  mirror=YES  halfturn=no
H: 6x7  mirror=YES  halfturn=YES
I: 2x7  mirror=YES  halfturn=YES
Y: 6x7  mirror=YES  halfturn=no
T: 6x7  mirror=YES  halfturn=no
E: 6x7  mirror=no   halfturn=no
M: 8x7  mirror=YES  halfturn=no
```

The claim holds exactly: every named letter is mirror-symmetric, all five `S` are half-turn
symmetric, `E` is claimed for neither and is neither. Every letter is 7 rows, every vertical
stroke 2 columns, the grid is 50 by 16 and rectangular. No finding.

### 3.6 The guard

```
=== 1. provider raises ===
LOG sushicore.help WARNING: the help page for hub was not drawn (RuntimeError: no workspace here); Typer's own help is used instead
exit 0 | typer panel: True | exc: None

=== 2. provider returns an object with no .console ===
LOG sushicore.help WARNING: the help page for hub was not drawn (AttributeError: 'NoConsole' object has no attribute 'console'); Typer's own help is used instead
exit 0 | typer panel: True | exc: None

=== 3. stray [/] in a rich docstring ===
with help_group -> exit 1 exc MarkupError
plain Typer     -> exit 1 exc MarkupError

=== 4. provider returns None ===
LOG sushicore.help WARNING: the help page for hub was not drawn (AttributeError: 'NoneType' object has no attribute 'console'); Typer's own help is used instead
exit 0 | typer panel: True
```

The guard does what report 15 says. Case 3 confirms report 15's central claim: Typer 0.20 raises
the identical `MarkupError` on the identical input with no sushicore in the process, so the
`[/]` failure is inherited, not caused. The guard still logs its one warning and hands over; the
error comes from Typer's own renderer afterwards.

Case 2 is the shape of finding 1.1: a provider that returns something console-like but incomplete
costs the page and says so only in a log record.

### 3.7 `--help` under `COLUMNS=40`

A real `build_console` provider, `COLUMNS=40`, `FORCE_COLOR=1`, output piped:

```
[probe] width=39 is_terminal=True color_system=windows encoding=utf-8 no_color=True dark=True
cols.py
Manage the stack.

Usage: cols.py [OPTIONS] COMMAND
[ARGS]...

Commands
  add     Bring a module in.
  doctor  Check tools.

Options
  --install-completion  Install
                        completion for
                        the current
                        shell.
  ...
```

No line exceeds 39 columns, nothing wraps badly except the usage line, which Rich breaks at a
space. No logo, correctly: `no_color` is true because `_use_color("auto")` asks
`sys.stdout.isatty()` and the pipe says no, so `_logo_visible` rejects at its second clause.

Two things this run exposes that I could not chase further:

- Rich reports `width=39` for `COLUMNS=40` on Windows. The page is drawn at 39 and written into
  Click's formatter, which does not re-wrap, so the arithmetic is safe. It does mean the logo
  thresholds are one column tighter on Windows than the documented numbers.
- `color_system` came back as `"windows"`, which is not in `K_LOGO_COLOUR_SYSTEMS`. If a real
  Windows Terminal session also reports `"windows"`, the logo never appears there whatever the
  width, and the `background = "dark"` advice in `docs/README.md:62-71` would be advice for a
  screen that draws no logo. This needs one run in a real Windows Terminal to settle; I have no
  interactive terminal here.

### 3.8 Tests that pass for a reason other than the one they name

- `tests/ui/test_logo.py:35`, `test_two_pixel_rows_become_one_terminal_row`, asserts
  `len(_lines(Logo(indent=0, glow=True))) == len(K_MARK_PIXELS) // 2`. It uses the default
  `wordmark=True`, so the row count is `max(16, 16) // 2`; the wordmark's 16 rows carry the
  assertion just as well as the mark's. `Logo(indent=0, glow=True, wordmark=False)` says what the
  name means.
- `tests/test_renderer_components.py:66`,
  `test_the_delegating_methods_state_what_they_print_in_one_sentence`, asserts on docstring text
  (`";" not in summary and summary.count(".") == 1`). It is a source-comment checker wearing a
  test's clothes, it belongs in `tools/documentation/check_source_comments.py` where the repository
  rule puts it, and `summary.count(".") == 1` will fail the day a docstring says "e.g.".
- `tests/help/test_logo_choice.py` and `tests/test_typer_help.py` take every width from
  `Logo(...).width` and never a literal, exactly as Task 15 promised. Checked by reading both
  files; no finding.

### 3.9 Documentation claims the code does deliver

Verified, so they are not findings: the visibility gate (terminal, colour on, 256 or better,
UTF-8); grouping by `rich_help_panel` with `Commands` as the default; examples from `epilog` at
`command  # note`; the `background` key and `SUSHI_CLI_BACKGROUND`; the one warning under
`sushicore.help`; and `docs/README.md:76-77`, "Typer turns an app with one command and no callback
into a plain command" — driven, and Typer's boxed screen is what comes out.

---

## 4. Report and metadata honesty

### 4.1 My runs

```
$ PYTHONPATH=/d/Projects/sushicore python -m pytest tests -q -p no:cacheprovider
........................................................................ [ 22%]
........................................................................ [ 44%]
........................................................................ [ 66%]
........................................................................ [ 88%]
.......................................                                  [100%]
327 passed in 0.87s
```

Reversed file order:

```
$ PYTHONPATH=/d/Projects/sushicore python -m pytest $(ls tests/test_*.py | sort -r) tests/ui tests/help -q -p no:cacheprovider
........................................................................ [ 22%]
........................................................................ [ 44%]
........................................................................ [ 66%]
........................................................................ [ 88%]
.......................................                                  [100%]
327 passed in 0.91s
```

327 both ways. `tests/conftest.py` holds: the golden tests survive a reversed collection order,
which is what Task 16's item 1 was for.

Per-file counts I use below:

```
tests/ui/test_logo.py: 28 passed in 0.11s
tests/test_brand.py: 22 passed in 0.03s
tests/help/test_logo_choice.py: 11 passed in 0.06s
tests/test_typer_help.py: 24 passed in 0.22s
tests/test_ui_architecture.py: 43 passed in 0.08s
tests/help/test_logo_choice.py tests/help/test_page.py tests/test_typer_help.py: 42 passed
```

### 4.2 Report 13 (logo data and component)

Counts add up: "13 tests" in `test_brand.py` matches the 13 lines pasted from `-v`; "15 tests" in
`test_logo.py` matches the 14 shown before the paste is cut plus the dark golden named in the file
table. The red-before run is real pytest output (two collection `ImportError`s), the green run is
real, `283 passed` is consistent with the count at that point. The "what the shape looks like"
blocks are rendered output, not prose in a fence.

Honest about what it did not do, including "the rendered lockup has not been checked on a real
dark terminal". That limitation is still true today.

### 4.3 Report 14 (background detection)

The strongest report of the six. Counts add up (13 + 10 = the 23 pasted `PASSED` lines). It
declines to claim the acceptance criterion: "The acceptance criterion's second half, `python -m
pytest tests -q` green in full, is therefore unproven." It names the three collection errors it
saw and attributes each to the worker that owned the file, which I can confirm from reports 13 and
16. No invented output. No finding.

### 4.4 Report 15 (choose the logo and wire it in)

Counts add up: "11 cases" in `test_logo_choice.py` is exactly what 5 functions with 5 two-value
parametrisations produce, and `42 passed` for the three files reproduces here.

Three things to correct:

1. **The report describes a public name the code does not have.** Report 15 line 242: "`HelpPageError`
   is new public surface in `sushicore/typer_help.py` … Say the word and it becomes a private
   `_HelpPageError`." The committed code already has `_HelpPageError` (`typer_help.py:32`). The
   word was evidently said and the report was not updated, so the report's open question reads as
   open when it is closed.
2. Two test names in the red paste (`test_a_stray_close_tag_in_rich_help_falls_back_to_typers_help`)
   do not exist in the file, which now has `..._is_logged_and_handed_to_typers_help`. Consistent
   with a later rename, but the paste no longer matches the tree.
3. **The timings do not reproduce.** The report pastes `318 passed in 11.23s`, `11.05s` and
   `10.43s`. The same suite, 9 tests larger, runs in 0.87s here, and reports 16, 17 and 18 all
   report sub-second runs of the same directory. I cannot explain the factor of twelve and I am
   not calling it invented; the counts themselves are consistent with the tree at that point
   (318 + 9 added by Task 18 = 327). Worth one question to that worker.

Its analysis of the `[/]` case is correct and I reproduced it (3.6). Its "What a user sees" blocks
show the pre-Task-18 wordmark, which is right for when it ran.

### 4.5 Report 16 (review fixes)

The five items are each shown red then green, with real pytest output, and the counts move in the
right direction (223 → 230 → 231). It contradicts the plan on item 1 and says so in bold at the
top, then the appended "Orchestrator note" contradicts the report in turn and says the report's own
claim was also incomplete. Three layers of correction in one file is confusing to read, but every
layer is labelled and the final state (`tests/conftest.py` clearing every functools cache on
`Style` and `Color`) is what is in the tree and is what makes the reversed run above pass.

One gap the report declares itself: item 5's `from_click.py` half "has no test … a wording change
checked by eye". Finding 2.2 says the eye missed half of it.

### 4.6 Report 17 (trim the margin)

Red-then-green is real, the ten named failures are the ones the change would fix, and the two
identical SHA-256 lines for the untouched dark golden support "the dark golden is untouched"
(though the command that produced them is not shown). `28 passed` for `test_logo.py` still
reproduces.

One overstated claim, line 7: "`width` and `render` both call `_trimmed(K_MARK_PIXELS,
_colours(self.glow))`, so they cannot disagree." True for the mark, false as a general statement —
finding 1.2 shows them 48 columns apart.

### 4.7 Report 18 (wordmark and white glow)

Counts add up and reproduce: 22 + 28 + 43 = 93, which is the `93 passed` the report pastes, and
`327 passed in 0.90s` is within noise of my `0.87s`. The "Measured sizes" block matches my own
measurement line for line. The red run shows the old widths (65, 61, 59) and the old amber SGR
codes, which is the right reason to fail.

One claim its paste does not support. Under "After `python regen_goldens.py` … the dark golden
holds `140;140;140` and `61;61;61` and no `107;107`", the fenced output is
`wordmark identical to plan: True 16`, which says nothing about the golden or the codes. The claim
happens to be true — I counted it independently:

```
tests/golden/logo_dark_truecolor.txt: 140;140;140 -> 8; 61;61;61 -> 40; 107;107 -> 0
tests/golden/logo_light_truecolor.txt: 140;140;140 -> 0; 61;61;61 -> 0; 107;107 -> 0
```

— but the report pasted the wrong command's output under it, which is the one thing dispatch
line 4 exists to prevent.

The symmetry claim in its section "Symmetry test" is fully verified in 3.5.

### 4.8 Metadata

`docs/reference/CHANGELOG.md` covers Tasks 13 to 18 in five lines, four of them clean. Ordering
and the double entry are 2.4. `README.md` and `docs/README.md` gained the `ui` and `help` rows the
spec asked for; the Help screens section is new and is accurate except for 2.3. Every path I
followed in the new documentation resolves.

---

## What I did not check

- **Any real terminal.** Every run in this report is a forced Rich console in a pipe. The glow's
  appearance on a dark terminal, the trimmed mark's appearance on a light one, and whether a real
  Windows Terminal reports a colour system the logo gate accepts (3.7) are all unverified. One
  `hub --help` in Windows Terminal and one in a Linux terminal would settle all three.
- **`tests/help/test_from_click.py`, `tests/help/test_page.py`, `tests/ui/test_header.py`,
  `test_panel.py`, `test_definition_list.py`, `test_table.py`, `test_title.py`, `test_usage.py`**
  beyond the parts Task 16 touched. Waves 2 and 4 reviewed them; I read only what Wave 6 changed.
- **`sushicore/help/from_click.py`'s reading logic** against Click versions other than the 8.2.1
  installed here, and against `rich_markup_mode=None`/`"markdown"`. The spec's known limit stands
  unretested by me.
- **The `hub` side (Wave 5).** Finding 1.1 predicts a failure there; I did not open
  `D:/Projects/sushistack` to see which form its provider takes.
- **Performance.** I noticed report 15's unexplained 11-second suite runs (4.4) and did not chase
  the cause.
- **`pyproject.toml`, the version bump to 0.4.0 and the Typer extra.** Outside the scope I was
  given; the wave-4 review covered them.
