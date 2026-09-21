# Terminal components Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give sushicore a maki logo, a quiet table and a grouped help screen, each drawn by one small component of the same shape.

**Architecture:** `sushicore/ui/` holds one frozen-dataclass component per file, drawn from `Theme`. `RichRenderer.table`, `panel` and `header` delegate to them. `sushicore/help/` turns a Click command into a `HelpModel` and a `HelpPage` composes components from it. `sushicore/typer_help.py` is the only module that imports Typer.

**Tech Stack:** Python 3.10+, Rich 13+, Typer 0.20 / Click 8.2 (optional extra), pytest.

**Spec:** `docs/agent/specs/2026-09-21-terminal-components-design.md`

## Global Constraints

- Repository: `D:/Projects/sushicore`. Baseline: `python -m pytest tests -q` reports `110 passed`.
- `Renderer` Protocol, `PlainRenderer` and `JsonRenderer` do not change.
- `rich>=13.0` stays the only runtime dependency. Typer is an optional extra, `typer = ["typer>=0.12"]`, and joins `test`.
- Only `sushicore/typer_help.py` imports `typer`. No `ui/` file imports `sushicore.help`.
- A `ui/` file imports only the standard library, `rich`, `..theme`, `..brand` and `.component`.
- A component is `@final` and `@dataclass(frozen=True, slots=True)` with `render(self, theme: Theme) -> RenderableType`. The file is named after it in snake case.
- The logo prints only when the Rich console is a terminal, `no_color` is false, the colour system is `256` or `truecolor`, and the encoding starts with `utf`.
- Python style (`python-code-style`): 100 columns, double quotes, `from __future__ import annotations` after the module docstring, module constants `K_UPPER_SNAKE`, no `utils.py`.
- Comments (`source-comments`): a module docstring of at most six lines; every class and function has a docstring whose first sentence starts with its verb; `#` only alone, one line, stating an invariant; no TODO, no history, no separator lines.
- Tests: fixed widths, no wall-clock, no network. A golden file is created once by its task and is changed afterwards only with the owner's approval.
- Version 0.3.0 becomes 0.4.0 and `docs/reference/CHANGELOG.md` gets one line per task, written by the orchestrator in the task's commit.

---

## How this plan runs

The owner chose waves. The orchestrator (this session) dispatches one worker per task, reviews each report, integrates, edits the changelog, the `__init__.py` files and `pyproject.toml`, and commits. Workers never commit, never edit `pyproject.toml`, `docs/reference/CHANGELOG.md`, `README.md` or `docs/README.md`.

### Dispatch header

Every worker prompt opens with these five lines, verbatim, and then carries the task text, its file list, its acceptance criterion and the skills to load.

```
1. SOLID, without exception. Every unit is a brick: one responsibility, detachable and
   re-attachable without touching its neighbours, rebuildable on its own. Siblings that do the
   same kind of thing are shaped the same. Engineer it once carefully, run it a thousand times
   cheaply. No quick hacks that happen to pass.
2. Before writing any prose (a comment that explains, a commit message, a report, a reply),
   invoke the `humanizer` skill and apply its rules in the language of the prose.
3. Do not start any process that runs `se`, `cmake`, `ninja` or `ctest`, in the foreground or
   the background, and do not write or edit any build configuration file.
4. Report what was done and what was not. Paste the output of every verification you claim.
5. Before reporting, syntax-check what you wrote without building: C++ through
   `compile_commands.json` with `clang -fsyntax-only`, GLSL through `shader_compiler.exe`.
   Paste the command and its output.
```

Additions every dispatch carries, because a worker cannot see this conversation:

- The repository is Python. Line 5 becomes `python -m py_compile <every file you wrote>`; paste its output. `pytest` is the project's own runner and is allowed, scoped to the task's test files.
- Load `python-code-style`, `source-comments`, `testing` and `humanizer` before writing.
- Write the report to `docs/agent/reports/2026-09-21-terminal-components-task-<N>.md`: files changed, each command run with its pasted output, what was not done.
- Match the surrounding `sushicore` code where this plan is silent.

Model per dispatch, set explicitly: **opus**, effort `high`, for Tasks 2, 7 and 10 (each fixes an interface); **sonnet**, effort `medium`, for every other task; reviewers **opus**, effort `high`.

### Waves

| Wave | Tasks | Files (disjoint) | Waits on | Build the owner runs after it |
| --- | --- | --- | --- | --- |
| 1 | 1 Theme token and `Console.theme` | `sushicore/theme.py`, `sushicore/console.py`, `tests/test_theme_muted.py` | nothing | `python -m pytest tests -q` |
| 1 | 2 Component protocol and architecture test | `sushicore/ui/__init__.py`, `sushicore/ui/component.py`, `tests/ui/__init__.py`, `tests/ui/capture.py`, `tests/ui/test_component.py`, `tests/test_ui_architecture.py` | nothing | same |
| 1 | 3 Brand data | `sushicore/brand.py`, `tests/test_brand.py` | nothing | same |
| 2 | 4 Logo | `sushicore/ui/logo.py`, `tests/ui/test_logo.py`, `tests/golden/logo_truecolor.txt` | 2, 3 | `python -m pytest tests -q` |
| 2 | 5 Header, Panel, Table | `sushicore/ui/header.py`, `panel.py`, `table.py`, `tests/ui/test_header.py`, `test_panel.py`, `test_table.py` | 1, 2 | same |
| 2 | 6 Title, Usage, DefinitionList | `sushicore/ui/title.py`, `usage.py`, `definition_list.py`, `tests/ui/test_title.py`, `test_usage.py`, `test_definition_list.py` | 1, 2 | same |
| 2 | 7 Help model and Click reader | `sushicore/help/__init__.py`, `sushicore/help/model.py`, `sushicore/help/from_click.py`, `tests/help/__init__.py`, `tests/help/test_from_click.py` | nothing | same |
| 3 | 8 Renderer delegation | `sushicore/renderer.py`, `tests/test_renderer_components.py` | 5 | `python -m pytest tests -q` |
| 3 | 9 Help page | `sushicore/help/page.py`, `tests/help/test_page.py` | 4, 6, 7 | same |
| 4 | 10 Typer help group | `sushicore/typer_help.py`, `tests/test_typer_help.py` | 7, 9 | same |
| 5 | 11 `hub` adopts the help group (repository `D:/Projects/sushistack`) | `sushihub/cli/sushistack/console.py`, `sushihub/cli/sushistack/cli.py`, `sushihub/cli/tests/test_help_screen.py` | 10, and sushicore 0.4.0 installed in the environment the hub tests run in | `python -m pytest sushihub/cli/tests -q` from `D:/Projects/sushistack` |

Between waves the orchestrator: reads every report against the task's acceptance criterion; sends back a report that lacks the file list, pasted output or the "not done" section; runs the wave's build; dispatches an opus reviewer that checks, as named items, SOLID shape (one responsibility per file, siblings shaped the same, dependency direction) and humanizer register (docstrings, the report); and commits by path, one commit per task, each with its changelog line. The orchestrator also writes `ui/__init__.py` after Wave 2 and `help/__init__.py` after Wave 3 (both are shared files, so no worker owns them).

Wave 5 is gated. It starts only when the owner has published sushicore 0.4.0, or installed the local checkout into the environment the hub tests use. Nothing before it needs that.

---

## Wave 1

### Task 1: The `muted` token and `Console.theme`

**Acceptance criterion:** `Theme().muted == "dim"`, the token reaches Rich's style map and `merged()`, and a `Console` exposes its theme.

**Files:**
- Modify: `sushicore/theme.py`
- Modify: `sushicore/console.py`
- Test: `tests/test_theme_muted.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `Theme.muted: str = "dim"`; `Console.theme -> Theme` (read-only property). Every later component reads `theme.muted`; `typer_help` reads `console.theme`.

- [ ] **Step 1: Write the failing test** `tests/test_theme_muted.py`

```python
"""The muted token and the console's public theme."""

import io

from sushicore.console import Console
from sushicore.icons import IconSet
from sushicore.renderer import PlainRenderer
from sushicore.theme import Theme


def test_muted_defaults_to_dim():
    assert Theme().muted == "dim"


def test_muted_reaches_the_rich_style_map():
    assert Theme(muted="italic").as_rich_styles()["muted"] == "italic"


def test_muted_is_overridable_like_every_other_token():
    assert Theme().merged({"muted": "grey50"}).muted == "grey50"


def test_console_exposes_the_theme_it_was_built_with():
    theme = Theme(muted="grey50")
    console = Console(PlainRenderer(stream=io.StringIO()), theme, IconSet())
    assert console.theme is theme
```

- [ ] **Step 2: Run it and see it fail**

Run: `python -m pytest tests/test_theme_muted.py -v`
Expected: 4 failures (`AttributeError: ... 'muted'` / `'theme'`).

- [ ] **Step 3: Implement**

In `sushicore/theme.py`, add the field after `rule_line`:

```python
    # Secondary text and the rule under a table header: quieter than the
    # terminal's own foreground, without picking a colour for an unknown background.
    muted: str = "dim"
```

and add `"muted": self.muted,` to the dict returned by `as_rich_styles`, next to `"rule.line"`.

In `sushicore/console.py`, add beside the `accent` property:

```python
    @property
    def theme(self) -> Theme:
        """Return the theme this console styles its output with."""
        return self._theme
```

- [ ] **Step 4: Run the whole suite**

Run: `python -m pytest tests -q`
Expected: `114 passed`.

Orchestrator's commit: `feat: add the muted token and Console.theme`. Changelog line: `- 2026-09-21 — Added `Theme.muted` and `Console.theme` (`sushicore/theme.py`, `sushicore/console.py`).`

---

### Task 2: The `Component` protocol and the architecture test

**Acceptance criterion:** `sushicore/ui/component.py` declares the protocol, and `tests/test_ui_architecture.py` enforces the one-component-per-file shape on every future `ui/` file.

**Files:**
- Create: `sushicore/ui/__init__.py`, `sushicore/ui/component.py`
- Create: `tests/ui/__init__.py`, `tests/ui/capture.py`, `tests/ui/test_component.py`
- Create: `tests/test_ui_architecture.py`

**Interfaces:**
- Consumes: `sushicore.theme.Theme`.
- Produces: `Component` protocol (`render(self, theme: Theme) -> RenderableType`, runtime-checkable); `tests.ui.capture.capture(component, width=60, theme=None) -> str` and `capture_ansi(component, width=60, theme=None) -> str`, used by every later component test.

- [ ] **Step 1: Write the tests**

`tests/ui/__init__.py` is empty.

`tests/ui/capture.py`:

```python
"""Renders a component to the text a terminal would show, with or without colour."""

from __future__ import annotations

import io

from rich.console import Console

from sushicore.theme import Theme
from sushicore.ui.component import Component


def capture(component: Component, width: int = 60, theme: Theme | None = None) -> str:
    """Return the component's plain text at ``width`` columns, trailing spaces stripped per line."""
    console = Console(
        file=io.StringIO(), width=width, color_system=None, force_terminal=False,
        legacy_windows=False,
    )
    console.print(component.render(theme or Theme()))
    lines = console.file.getvalue().split("\n")
    return "\n".join(line.rstrip() for line in lines)


def capture_ansi(component: Component, width: int = 60, theme: Theme | None = None) -> str:
    """Return the component's output as a truecolour terminal would receive it."""
    console = Console(
        file=io.StringIO(), width=width, color_system="truecolor", force_terminal=True,
        legacy_windows=False, no_color=False,
    )
    console.print(component.render(theme or Theme()))
    return console.file.getvalue()
```

`tests/ui/test_component.py`:

```python
"""The Component protocol accepts anything that draws itself from a theme."""

from rich.text import Text

from sushicore.theme import Theme
from sushicore.ui.component import Component


class _Hello:
    def render(self, theme: Theme) -> Text:
        return Text("hello")


def test_a_class_with_render_satisfies_the_protocol():
    assert isinstance(_Hello(), Component)


def test_a_class_without_render_does_not():
    assert not isinstance(object(), Component)
```

`tests/test_ui_architecture.py`:

```python
"""Every ui/ file is one component, shaped like its siblings, importing only what it may."""

import ast
import dataclasses
import importlib
import sys
from pathlib import Path

import pytest

UI = Path(__file__).resolve().parent.parent / "sushicore" / "ui"
K_PACKAGE = ["sushicore", "ui"]
K_ALLOWED_INTERNAL = {"sushicore.theme", "sushicore.brand", "sushicore.ui.component"}
K_ALLOWED_EXTERNAL = {"rich"}
FILES = sorted(p for p in UI.glob("*.py") if p.name not in {"__init__.py", "component.py"})


def _pascal(stem: str) -> str:
    return "".join(word.capitalize() for word in stem.split("_"))


def _imported_modules(tree: ast.AST) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = K_PACKAGE[: len(K_PACKAGE) - (node.level - 1)] if node.level else []
            names.append(".".join(base + ([node.module] if node.module else [])))
    return names


def test_the_protocol_file_declares_render():
    module = importlib.import_module("sushicore.ui.component")
    assert callable(module.Component.render)


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_file_defines_one_public_class_named_after_the_file(path):
    module = importlib.import_module(f"sushicore.ui.{path.stem}")
    public = [
        name for name, value in vars(module).items()
        if isinstance(value, type) and value.__module__ == module.__name__ and not name.startswith("_")
    ]
    assert public == [_pascal(path.stem)]


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_component_is_a_frozen_dataclass_with_render(path):
    module = importlib.import_module(f"sushicore.ui.{path.stem}")
    component = getattr(module, _pascal(path.stem))
    assert dataclasses.is_dataclass(component)
    assert component.__dataclass_params__.frozen
    assert callable(component.render)


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_file_imports_only_what_a_component_may(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for name in _imported_modules(tree):
        root = name.split(".")[0]
        allowed = (
            root in sys.stdlib_module_names
            or root in K_ALLOWED_EXTERNAL
            or name in K_ALLOWED_INTERNAL
        )
        assert allowed, f"{path.name} imports {name}"
```

- [ ] **Step 2: Run and see the protocol tests fail**

Run: `python -m pytest tests/ui/test_component.py tests/test_ui_architecture.py -v`
Expected: collection error `ModuleNotFoundError: sushicore.ui`.

- [ ] **Step 3: Implement**

`sushicore/ui/__init__.py`:

```python
"""Terminal components: one file per element, each drawn from a Theme."""
```

`sushicore/ui/component.py`:

```python
"""The one shape every terminal component has."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from rich.console import RenderableType

from ..theme import Theme


@runtime_checkable
class Component(Protocol):
    """Describes a piece of terminal output that draws itself from a theme."""

    def render(self, theme: Theme) -> RenderableType:
        """Return the Rich renderable this component draws in ``theme``."""
        ...
```

- [ ] **Step 4: Run and see it pass**

Run: `python -m pytest tests/ui/test_component.py tests/test_ui_architecture.py -v`
Expected: 3 passed (the parametrised architecture tests collect no cases yet).

Orchestrator's commit: `feat(ui): add the Component protocol`. Changelog line: `- 2026-09-21 — Added the `Component` protocol and the architecture test that guards `ui/` (`sushicore/ui/component.py`, `tests/test_ui_architecture.py`).`

---

### Task 3: The brand data

**Acceptance criterion:** `sushicore/brand.py` holds the four brand colours and a rectangular pixel grid of the maki, and an enlarged preview of the grid looks like `sushiweb/apps/web/public/images/logo-icon.png`.

**Files:**
- Create: `sushicore/brand.py`
- Test: `tests/test_brand.py`
- Scratch, not committed: the tracing script and the preview PNG, in the session scratchpad.

**Interfaces:**
- Consumes: nothing.
- Produces: `K_TRANSPARENT: str = "."`; `K_PALETTE: dict[str, str]` mapping the keys `n` (nori), `r` (rice), `a` (amber), `g` (green) to `#rrggbb`; `K_LOGO_PIXELS: tuple[str, ...]`, equal-length strings, an even number of rows, every character a palette key or `K_TRANSPARENT`. Only `ui/logo.py` reads it.

- [ ] **Step 1: Write the test** `tests/test_brand.py`

```python
"""The logo data is a well-formed pixel grid over the brand palette."""

import re

from sushicore.brand import K_LOGO_PIXELS, K_PALETTE, K_TRANSPARENT

K_MAX_SIDE = 24


def _used() -> set[str]:
    return set("".join(K_LOGO_PIXELS))


def test_every_row_has_the_same_width():
    assert len({len(row) for row in K_LOGO_PIXELS}) == 1


def test_the_grid_has_an_even_number_of_rows():
    assert len(K_LOGO_PIXELS) % 2 == 0


def test_the_grid_stays_small_enough_for_a_help_screen():
    assert len(K_LOGO_PIXELS) <= K_MAX_SIDE and len(K_LOGO_PIXELS[0]) <= K_MAX_SIDE


def test_the_grid_uses_only_palette_keys_and_the_transparent_key():
    assert _used() <= set(K_PALETTE) | {K_TRANSPARENT}


def test_every_palette_key_appears_in_the_grid():
    assert set(K_PALETTE) <= _used()


def test_palette_values_are_lowercase_hex_colours():
    assert all(re.fullmatch(r"#[0-9a-f]{6}", value) for value in K_PALETTE.values())


def test_the_palette_names_the_four_brand_keys():
    assert set(K_PALETTE) == {"n", "r", "a", "g"}
```

- [ ] **Step 2: Run and see it fail**

Run: `python -m pytest tests/test_brand.py -v`
Expected: `ModuleNotFoundError: sushicore.brand`.

- [ ] **Step 3: Trace the grid and write `brand.py`**

The source is `D:/Projects/sushiweb/apps/web/public/images/logo-icon.png` (1000×1000, a maki: near-black nori, off-white rice, amber and green fill). Pillow 12 is installed. In the scratchpad write a script that:

1. Opens the PNG as RGBA. If its alpha channel is fully opaque, flood-fills the white background from the four corners (`ImageDraw.floodfill`, `thresh=6`) to transparent, so the off-white rice inside the outline survives.
2. Crops to the bounding box of pixels with alpha above 40.
3. Resizes to 22 columns with `Image.LANCZOS`; the height follows the aspect ratio, rounded up to an even number.
4. For each pixel with alpha below 128 writes `.`; otherwise writes the key of the nearest palette colour by squared RGB distance.
5. Measures the four palette colours from the PNG (median of each region) and reports them; the starting values are nori `#1d1e20`, rice `#f4f4f4`, amber `#f0a500`, green `#4caf50`.
6. Writes a 16× nearest-neighbour preview PNG of the grid.

Look at the preview with the Read tool and compare it with the source. Fix the palette or the crop until the roll reads as the source does. Then write `sushicore/brand.py`:

```python
"""The Sushi Systems maki as data: a palette and a pixel grid.

Palette keys: n nori, r rice, a amber, g green; "." is transparent.
The grid is traced from sushiweb/apps/web/public/images/logo-icon.png.
Only ui/logo.py reads this module.
"""

from __future__ import annotations

K_TRANSPARENT = "."

K_PALETTE: dict[str, str] = {
    "n": "#1d1e20",
    "r": "#f4f4f4",
    "a": "#f0a500",
    "g": "#4caf50",
}

K_LOGO_PIXELS: tuple[str, ...] = (
    "<one string per pixel row, from the trace>",
)
```

The last line above is the shape only: the worker replaces it with the traced rows, one string per row, and uses the measured palette values.

- [ ] **Step 4: Run and see it pass**

Run: `python -m pytest tests/test_brand.py -v`
Expected: 7 passed.

The worker reports the grid size, the measured palette, and the path of the preview PNG so the orchestrator can view it. The owner approves the look at the Wave 1 review.

Orchestrator's commit: `feat(brand): add the maki logo data`. Changelog line: `- 2026-09-21 — Added the maki logo as a palette and a pixel grid (`sushicore/brand.py`).`

---

## Wave 2

### Task 4: `Logo`

**Acceptance criterion:** `Logo().render(theme)` draws the brand grid two pixel rows per terminal row, and its truecolour output equals `tests/golden/logo_truecolor.txt`.

**Files:**
- Create: `sushicore/ui/logo.py`
- Test: `tests/ui/test_logo.py`, `tests/golden/logo_truecolor.txt`

**Interfaces:**
- Consumes: `K_LOGO_PIXELS`, `K_PALETTE` from `sushicore.brand`; `Theme`; `tests.ui.capture.capture`, `capture_ansi`.
- Produces: `Logo(indent: int = 2)` with `render(theme) -> Text`. Task 9 composes it.

- [ ] **Step 1: Write the tests** `tests/ui/test_logo.py`

```python
"""The logo draws the brand grid in half-block characters."""

from pathlib import Path

from sushicore.brand import K_LOGO_PIXELS
from sushicore.ui.logo import Logo
from tests.ui.capture import capture, capture_ansi

GOLDEN = Path(__file__).resolve().parents[1] / "golden" / "logo_truecolor.txt"
K_PALETTE = {"a": "#f0a500", "n": "#1d1e20", "g": "#4caf50"}


def _small_grid(monkeypatch):
    monkeypatch.setattr("sushicore.ui.logo.K_LOGO_PIXELS", ("a.n..g", "a.a.g."))
    monkeypatch.setattr("sushicore.ui.logo.K_PALETTE", K_PALETTE)


def test_two_pixel_rows_become_one_terminal_row():
    lines = capture(Logo(indent=0)).split("\n")[:-1]
    assert len(lines) == len(K_LOGO_PIXELS) // 2


def test_indent_prefixes_every_non_empty_row():
    lines = [line for line in capture(Logo(indent=3)).split("\n") if line]
    assert lines and all(line.startswith("   ") for line in lines)


def test_each_cell_picks_the_block_that_shows_its_two_pixels(monkeypatch):
    _small_grid(monkeypatch)
    assert capture(Logo(indent=0)).rstrip("\n") == "█ ▀ ▄▀"


def test_two_different_colours_share_one_cell_as_foreground_and_background(monkeypatch):
    _small_grid(monkeypatch)
    assert "\x1b[38;2;29;30;32;48;2;240;165;0m▀\x1b[0m" in capture_ansi(Logo(indent=0))


def test_the_logo_matches_its_golden_file():
    assert capture_ansi(Logo(), width=80) == GOLDEN.read_text(encoding="utf-8")
```

- [ ] **Step 2: Run and see it fail**

Run: `python -m pytest tests/ui/test_logo.py -v`
Expected: `ModuleNotFoundError: sushicore.ui.logo`.

- [ ] **Step 3: Implement** `sushicore/ui/logo.py`

```python
"""Draws the Sushi Systems maki in half-block characters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from rich.console import RenderableType
from rich.style import Style
from rich.text import Text

from ..brand import K_LOGO_PIXELS, K_PALETTE
from ..theme import Theme


def _cell(top: str, bottom: str) -> Text:
    """Return the one character that shows a vertical pair of logo pixels."""
    top_colour = K_PALETTE.get(top)
    bottom_colour = K_PALETTE.get(bottom)
    if top_colour is None and bottom_colour is None:
        return Text(" ")
    if bottom_colour is None:
        return Text("▀", style=Style(color=top_colour))
    if top_colour is None:
        return Text("▄", style=Style(color=bottom_colour))
    if top_colour == bottom_colour:
        return Text("█", style=Style(color=top_colour))
    return Text("▀", style=Style(color=top_colour, bgcolor=bottom_colour))


@final
@dataclass(frozen=True, slots=True)
class Logo:
    """Draws the brand mark, two pixel rows per terminal row."""

    indent: int = 2

    def render(self, theme: Theme) -> RenderableType:
        """Return the mark as styled text; the brand's colours do not depend on ``theme``."""
        rows = []
        for top, bottom in zip(K_LOGO_PIXELS[0::2], K_LOGO_PIXELS[1::2]):
            cells = [_cell(t, b) for t, b in zip(top, bottom)]
            rows.append(Text(" " * self.indent).append_text(Text("").join(cells)))
        return Text("\n").join(rows)
```

- [ ] **Step 4: Create the golden and run**

Write `capture_ansi(Logo(), width=80)` to `tests/golden/logo_truecolor.txt` with `newline="\n"` and UTF-8 once, by a one-line script in the scratchpad, then read the file back with the Read tool and report the row count. Run:

`python -m pytest tests/ui/test_logo.py tests/test_ui_architecture.py -v`
Expected: all pass, including the four architecture cases for `logo.py`.

Orchestrator's commit: `feat(ui): add the Logo component`. Changelog line: `- 2026-09-21 — Added the `Logo` component (`sushicore/ui/logo.py`, `tests/golden/logo_truecolor.txt`).`

---

### Task 5: `Header`, `Panel`, `Table`

**Acceptance criterion:** the three components draw what `RichRenderer.header`, `panel` and `table` draw today, except that a table has a header rule and no frame, and their tests pass.

**Files:**
- Create: `sushicore/ui/header.py`, `sushicore/ui/panel.py`, `sushicore/ui/table.py`
- Test: `tests/ui/test_header.py`, `tests/ui/test_panel.py`, `tests/ui/test_table.py`

**Interfaces:**
- Consumes: `Theme` (`header`, `rule_line`, `panel_border`, `info`, `muted`); `Component`.
- Produces: `Header(title: str)`, `Panel(title: str, body: str)`, `Table(columns: tuple[str, ...], rows: tuple[tuple[str, ...], ...], title: str = "")`, each with `render(theme)`. Task 8 calls them from `RichRenderer`.

- [ ] **Step 1: Write the tests**

`tests/ui/test_header.py`:

```python
"""A header is a blank line and a titled rule."""

from sushicore.ui.header import Header
from tests.ui.capture import capture


def test_header_is_a_blank_line_then_a_rule_holding_the_title():
    assert capture(Header("Setup"), width=20) == "\n────── Setup ───────\n"
```

`tests/ui/test_panel.py`:

```python
"""A panel is a bordered body under a title."""

from sushicore.ui.panel import Panel
from tests.ui.capture import capture


def test_panel_puts_the_title_on_the_top_border_and_the_body_inside():
    lines = capture(Panel("Build failed", "cmake exited 1"), width=30).rstrip("\n").split("\n")
    assert lines[0].startswith("╭") and "Build failed" in lines[0]
    assert "cmake exited 1" in lines[1]
    assert lines[-1].startswith("╰")


def test_panel_body_keeps_rich_markup():
    text = capture(Panel("t", "[bold]done[/bold]"), width=30)
    assert "done" in text and "[bold]" not in text
```

`tests/ui/test_table.py`:

```python
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
```

- [ ] **Step 2: Run and see them fail**

Run: `python -m pytest tests/ui/test_header.py tests/ui/test_panel.py tests/ui/test_table.py -v`
Expected: `ModuleNotFoundError` for each.

- [ ] **Step 3: Implement**

`sushicore/ui/header.py`:

```python
"""Draws a blank line and a titled rule."""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from rich.console import Group, RenderableType
from rich.rule import Rule
from rich.text import Text

from ..theme import Theme


@final
@dataclass(frozen=True, slots=True)
class Header:
    """Draws a section header: a blank line, then a rule holding the title."""

    title: str

    def render(self, theme: Theme) -> RenderableType:
        """Return the header in the theme's header and rule styles."""
        return Group(
            Text(""),
            Rule(Text(self.title, style=theme.header), style=theme.rule_line),
        )
```

`sushicore/ui/panel.py`:

```python
"""Draws a bordered body under a title."""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from rich.console import RenderableType
from rich.panel import Panel as RichPanel
from rich.text import Text

from ..theme import Theme


@final
@dataclass(frozen=True, slots=True)
class Panel:
    """Draws a body inside a border coloured with the theme's panel border."""

    title: str
    body: str

    def render(self, theme: Theme) -> RenderableType:
        """Return the panel; the body keeps its Rich markup."""
        return RichPanel(
            self.body,
            title=Text(self.title, style=theme.panel_border),
            border_style=theme.panel_border,
        )
```

`sushicore/ui/table.py`:

```python
"""Draws rows under one header rule, with no frame around them."""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from rich import box
from rich.console import RenderableType
from rich.table import Table as RichTable

from ..theme import Theme


@final
@dataclass(frozen=True, slots=True)
class Table:
    """Draws a titled table of string cells."""

    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    title: str = ""

    def render(self, theme: Theme) -> RenderableType:
        """Return the table: header row, a rule in the muted style, then the rows."""
        table = RichTable(
            title=self.title or None,
            title_justify="left",
            title_style=theme.info,
            box=box.SIMPLE_HEAD,
            show_edge=False,
            pad_edge=False,
            header_style=theme.header,
            border_style=theme.muted,
        )
        for column in self.columns:
            table.add_column(column)
        for row in self.rows:
            table.add_row(*row)
        return table
```

- [ ] **Step 4: Run and see them pass**

Run: `python -m pytest tests/ui/test_header.py tests/ui/test_panel.py tests/ui/test_table.py tests/test_ui_architecture.py -v`
Expected: all pass, including the architecture cases for the three files.

Orchestrator's commit: `feat(ui): add Header, Panel and Table components`. Changelog line: `- 2026-09-21 — Added the `Header`, `Panel` and `Table` components; the table has a header rule and no frame (`sushicore/ui/`).`

---

### Task 6: `Title`, `Usage`, `DefinitionList`

**Acceptance criterion:** the three components draw the help screen's title, usage line and headed two-column lists, and their tests pass.

**Files:**
- Create: `sushicore/ui/title.py`, `sushicore/ui/usage.py`, `sushicore/ui/definition_list.py`
- Test: `tests/ui/test_title.py`, `tests/ui/test_usage.py`, `tests/ui/test_definition_list.py`

**Interfaces:**
- Consumes: `Theme` (`header`, `muted`, `cmd`); `Component`.
- Produces: `Title(name: str, description: str = "")`, `Usage(usage: str)`, `DefinitionList(heading: str, entries: tuple[tuple[str, str], ...])`. Descriptions and entry text are Rich markup; terms and the usage string are literal. Task 9 composes all three.

- [ ] **Step 1: Write the tests**

`tests/ui/test_title.py`:

```python
"""A title is a name and, under it, a description."""

from sushicore.ui.title import Title
from tests.ui.capture import capture


def test_title_draws_the_name_then_the_description():
    assert capture(Title("hub", "One tree for the stack.")) == "hub\nOne tree for the stack.\n"


def test_title_without_a_description_is_the_name_alone():
    assert capture(Title("hub add")) == "hub add\n"


def test_description_interprets_rich_markup():
    assert capture(Title("gui", "Builds into [cyan]build/hub[/cyan].")) == "gui\nBuilds into build/hub.\n"
```

`tests/ui/test_usage.py`:

```python
"""The usage line prints its string literally."""

from sushicore.ui.usage import Usage
from tests.ui.capture import capture


def test_usage_keeps_square_brackets_literal():
    assert capture(Usage("hub [OPTIONS] COMMAND [ARGS]...")) == "Usage: hub [OPTIONS] COMMAND [ARGS]...\n"
```

`tests/ui/test_definition_list.py`:

```python
"""A definition list is a heading over a term column and a text column."""

from sushicore.ui.definition_list import DefinitionList
from tests.ui.capture import capture


def test_entries_align_and_the_text_wraps_inside_its_column():
    entries = (
        ("add", "Bring one or more stack modules into the workspace, with what they need."),
        ("install-cli", "Install a [cyan]module[/cyan]'s CLI."),
    )
    assert capture(DefinitionList("Modules", entries), width=50) == (
        "Modules\n"
        "  add          Bring one or more stack modules\n"
        "               into the workspace, with what they\n"
        "               need.\n"
        "  install-cli  Install a module's CLI.\n"
    )


def test_a_term_with_brackets_is_printed_literally():
    text = capture(DefinitionList("Options", (("--type [debug|release]", "The build type."),)))
    assert "--type [debug|release]" in text


def test_an_entry_without_text_prints_its_term_alone():
    assert capture(DefinitionList("Examples", (("hub doctor", ""),))) == "Examples\n  hub doctor\n"
```

- [ ] **Step 2: Run and see them fail**

Run: `python -m pytest tests/ui/test_title.py tests/ui/test_usage.py tests/ui/test_definition_list.py -v`
Expected: `ModuleNotFoundError` for each.

- [ ] **Step 3: Implement**

`sushicore/ui/title.py`:

```python
"""Draws a command's name and its description."""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from rich.console import Group, RenderableType
from rich.text import Text

from ..theme import Theme


@final
@dataclass(frozen=True, slots=True)
class Title:
    """Draws a name in the header style with an optional markup description under it."""

    name: str
    description: str = ""

    def render(self, theme: Theme) -> RenderableType:
        """Return the name alone, or the name over its description."""
        name = Text(self.name, style=theme.header)
        if not self.description:
            return name
        return Group(name, Text.from_markup(self.description))
```

`sushicore/ui/usage.py`:

```python
"""Draws a command's usage line."""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from rich.console import RenderableType
from rich.text import Text

from ..theme import Theme


@final
@dataclass(frozen=True, slots=True)
class Usage:
    """Draws ``Usage:`` and the usage string, which is printed literally."""

    usage: str

    def render(self, theme: Theme) -> RenderableType:
        """Return the line with the label muted and the usage in the command style."""
        return Text.assemble(("Usage: ", theme.muted), (self.usage, theme.cmd))
```

`sushicore/ui/definition_list.py`:

```python
"""Draws a heading over a two-column list of terms and their text."""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from rich.console import Group, RenderableType
from rich.padding import Padding
from rich.table import Table as RichTable
from rich.text import Text

from ..theme import Theme

K_INDENT = 2


@final
@dataclass(frozen=True, slots=True)
class DefinitionList:
    """Draws commands, arguments, options or examples: a term, then what it means."""

    heading: str
    entries: tuple[tuple[str, str], ...]

    def render(self, theme: Theme) -> RenderableType:
        """Return the heading and the indented grid; terms are literal, text is markup."""
        grid = RichTable.grid(padding=(0, 2))
        grid.add_column(no_wrap=True)
        grid.add_column()
        for term, text in self.entries:
            grid.add_row(Text(term, style=theme.cmd), Text.from_markup(text))
        return Group(
            Text(self.heading, style=theme.header),
            Padding(grid, (0, 0, 0, K_INDENT)),
        )
```

- [ ] **Step 4: Run and see them pass**

Run: `python -m pytest tests/ui/test_title.py tests/ui/test_usage.py tests/ui/test_definition_list.py tests/test_ui_architecture.py -v`
Expected: all pass. `K_INDENT` is a module constant, not a class, so the architecture test's one-public-class rule holds.

Orchestrator's commit: `feat(ui): add Title, Usage and DefinitionList`. Changelog line: `- 2026-09-21 — Added the `Title`, `Usage` and `DefinitionList` components (`sushicore/ui/`).` The same commit adds a `sushicore.ui` row to the module table in `README.md` (`One file per terminal element, each drawn from a Theme: logo, header, panel, table, title, usage, definition list`) and a matching bullet under "Design" in `docs/README.md`.

---

### Task 7: `HelpModel` and the Click reader

**Acceptance criterion:** `build_model(command, ctx)` turns a Click or Typer command into a `HelpModel` with grouped commands, arguments, options and examples, and its tests pass.

**Files:**
- Create: `sushicore/help/__init__.py`, `sushicore/help/model.py`, `sushicore/help/from_click.py`
- Create: `tests/help/__init__.py`
- Test: `tests/help/test_from_click.py`

**Interfaces:**
- Consumes: nothing from sushicore. It reads a Click command by duck typing (`params`, `get_params`, `list_commands`, `get_command`, `get_short_help_str`, `collect_usage_pieces`, `epilog`, `help`, `rich_help_panel`) and never imports `click` or `typer`.
- Produces:
  - `HelpSection(heading: str, entries: tuple[tuple[str, str], ...])`
  - `HelpModel(name, description, usage: str; is_root: bool; commands: tuple[HelpSection, ...]; arguments, options, examples: tuple[tuple[str, str], ...])`
  - `build_model(command: Any, ctx: Any) -> HelpModel`
  Tasks 9 and 10 depend on these exact names.

- [ ] **Step 1: Write the tests** `tests/help/test_from_click.py`

`tests/help/__init__.py` is empty. `help/__init__.py` in the package holds the docstring `"""Help screens: the data they are drawn from and the page that draws them."""` only.

```python
"""build_model reads a Click command tree into a HelpModel."""

import click

from sushicore.help.from_click import build_model


def _tree() -> click.Group:
    @click.group(name="hub", help="Manage the\nstack.\n\nSecond paragraph.\f hidden",
                 epilog="hub add sr  # bring sushiruntime in\n\nhub doctor")
    def hub():
        pass

    @hub.command(name="add", help="Bring a module in.")
    @click.argument("module")
    @click.option("--dry-run", is_flag=True, help="Show the plan only.")
    def add(module, dry_run):
        pass

    @hub.command(name="link", help="Register a checkout.")
    def link():
        pass

    @hub.command(name="init", help="Mark a workspace.")
    def init():
        pass

    @hub.command(name="doctor", help="Check tools.")
    def doctor():
        pass

    @hub.command(name="secret", help="Hidden.", hidden=True)
    def secret():
        pass

    add.rich_help_panel = "Modules"
    link.rich_help_panel = "Modules"
    init.rich_help_panel = "Workspace"
    return hub


def _root():
    group = _tree()
    return group, click.Context(group, info_name="hub")


def test_commands_are_grouped_by_panel_in_order_of_first_appearance():
    group, ctx = _root()
    sections = build_model(group, ctx).commands
    assert [s.heading for s in sections] == ["Modules", "Commands", "Workspace"]
    assert [term for term, _ in sections[0].entries] == ["add", "link"]


def test_a_command_with_no_panel_falls_into_commands():
    group, ctx = _root()
    commands = dict(build_model(group, ctx).commands[1].entries)
    assert commands == {"doctor": "Check tools."}


def test_a_placeholder_panel_is_not_a_heading():
    group, ctx = _root()
    group.commands["doctor"].rich_help_panel = object()
    assert [s.heading for s in build_model(group, ctx).commands] == ["Modules", "Commands", "Workspace"]


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
```

- [ ] **Step 2: Run and see it fail**

Run: `python -m pytest tests/help/test_from_click.py -v`
Expected: `ModuleNotFoundError: sushicore.help`.

- [ ] **Step 3: Implement**

`sushicore/help/model.py`:

```python
"""The data a help screen is drawn from."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HelpSection:
    """Holds a heading and the term and text pairs listed under it."""

    heading: str
    entries: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class HelpModel:
    """Holds everything one help screen shows, with no drawing decisions in it."""

    name: str
    description: str
    usage: str
    is_root: bool
    commands: tuple[HelpSection, ...]
    arguments: tuple[tuple[str, str], ...]
    options: tuple[tuple[str, str], ...]
    examples: tuple[tuple[str, str], ...]
```

`sushicore/help/from_click.py`:

```python
"""Reads a Click or Typer command into a HelpModel, by duck typing.

It imports neither Click nor Typer: it asks the command object for what it has.
"""

from __future__ import annotations

from typing import Any

from .model import HelpModel, HelpSection

K_DEFAULT_GROUP = "Commands"
K_SHORT_HELP_LIMIT = 120


def build_model(command: Any, ctx: Any) -> HelpModel:
    """Return the help model of ``command`` as seen from ``ctx``."""
    return HelpModel(
        name=ctx.command_path,
        description=_description(command),
        usage=" ".join([ctx.command_path, *command.collect_usage_pieces(ctx)]),
        is_root=ctx.parent is None,
        commands=_command_sections(command, ctx),
        arguments=_param_entries(command, ctx, "argument"),
        options=_param_entries(command, ctx, "option"),
        examples=_examples(command),
    )


def _description(command: Any) -> str:
    """Return the help text up to a form feed, each paragraph on one line."""
    text = (command.help or "").split("\f")[0]
    paragraphs = [" ".join(paragraph.split()) for paragraph in text.split("\n\n")]
    return "\n\n".join(paragraph for paragraph in paragraphs if paragraph)


def _command_sections(command: Any, ctx: Any) -> tuple[HelpSection, ...]:
    """Return the visible sub-commands grouped by panel, in order of first appearance."""
    list_commands = getattr(command, "list_commands", None)
    if list_commands is None:
        return ()
    grouped: dict[str, list[tuple[str, str]]] = {}
    for name in list_commands(ctx):
        sub = command.get_command(ctx, name)
        if sub is None or getattr(sub, "hidden", False):
            continue
        panel = getattr(sub, "rich_help_panel", None)
        heading = panel if isinstance(panel, str) else K_DEFAULT_GROUP
        grouped.setdefault(heading, []).append((name, sub.get_short_help_str(K_SHORT_HELP_LIMIT)))
    return tuple(HelpSection(heading, tuple(entries)) for heading, entries in grouped.items())


def _param_entries(command: Any, ctx: Any, kind: str) -> tuple[tuple[str, str], ...]:
    """Return the visible parameters of one kind as term and text pairs."""
    entries = []
    for param in command.get_params(ctx):
        if param.param_type_name != kind or getattr(param, "hidden", False):
            continue
        entry = _entry(param, ctx)
        if entry is not None:
            entries.append(entry)
    return tuple(entries)


def _entry(param: Any, ctx: Any) -> tuple[str, str] | None:
    """Return the parameter's help record, or its metavar when it has none."""
    get_record = getattr(param, "get_help_record", None)
    record = get_record(ctx) if get_record is not None else None
    if record is not None:
        return record[0], record[1] or ""
    if param.param_type_name == "argument":
        return param.make_metavar(ctx), getattr(param, "help", None) or ""
    return None


def _examples(command: Any) -> tuple[tuple[str, str], ...]:
    """Return one example per non-empty epilog line, split at the first ``" # "``."""
    entries = []
    for line in (command.epilog or "").splitlines():
        line = line.strip()
        if line:
            example, _, note = line.partition(" # ")
            entries.append((example.strip(), note.strip()))
    return tuple(entries)
```

- [ ] **Step 4: Run and see it pass**

Run: `python -m pytest tests/help/test_from_click.py -v`
Expected: 11 passed. Requires `click`, present because Typer is installed here; the plan's `test` extra installs it.

Orchestrator's commit: `feat(help): read a Click command into a HelpModel`. Changelog line: `- 2026-09-21 — Added `HelpModel` and `build_model`, which reads a Click or Typer command into help data (`sushicore/help/model.py`, `sushicore/help/from_click.py`).`

---

## Wave 3

### Task 8: The renderer delegates to components

**Acceptance criterion:** `RichRenderer.table`, `panel` and `header` print through `Table`, `Panel` and `Header`, and the whole suite passes.

**Files:**
- Modify: `sushicore/renderer.py`
- Test: `tests/test_renderer_components.py`

**Interfaces:**
- Consumes: `Header`, `Panel`, `Table` from `sushicore.ui.header`, `sushicore.ui.panel`, `sushicore.ui.table`; the theme `RichRenderer` already receives.
- Produces: no new names. `Renderer`, `PlainRenderer` and `JsonRenderer` are untouched. The style arguments of `header`, `panel` and `table` stay in the signatures because the Protocol declares them; `RichRenderer` styles from its own theme.

- [ ] **Step 1: Write the test** `tests/test_renderer_components.py`

```python
"""RichRenderer draws its table, panel and header through the components."""

from sushicore.renderer import RichRenderer
from sushicore.theme import Theme

K_FRAME = set("│┃┌┐└┘╭╮╰╯|+")


def _lines(capsys) -> list[str]:
    return [line.rstrip() for line in capsys.readouterr().out.split("\n")]


def test_table_has_a_title_a_header_a_rule_and_no_frame(capsys):
    RichRenderer(Theme(), no_color=True).table(
        "Modules", ["Module", "State"], [["sushiruntime", "cloned"]], header_style="bold",
    )
    lines = _lines(capsys)
    assert lines[0] == "Modules"
    assert lines[1].startswith("Module")
    assert set(lines[2]) == {"─"}
    assert not set("".join(lines)) & K_FRAME


def test_header_prints_a_blank_line_then_a_rule_holding_the_title(capsys):
    RichRenderer(Theme(), no_color=True).header("Setup", style="bold")
    lines = _lines(capsys)
    assert lines[0] == "" and "Setup" in lines[1] and "─" in lines[1]


def test_panel_prints_its_title_and_body_inside_a_border(capsys):
    RichRenderer(Theme(), no_color=True).panel("Failed", "cmake exited 1", border_style="red")
    lines = _lines(capsys)
    assert lines[0][0] in "╭┌" and "Failed" in lines[0]
    assert "cmake exited 1" in lines[1] and lines[2][0] in "╰└"
```

- [ ] **Step 2: Run and see the table test fail**

Run: `python -m pytest tests/test_renderer_components.py -v`
Expected: `test_table_has_a_title_a_header_a_rule_and_no_frame` fails (the frame is still there).

- [ ] **Step 3: Implement**

In `sushicore/renderer.py`, import the components at the top of the module, next to `from .theme import Theme`:

```python
from .ui.header import Header
from .ui.panel import Panel
from .ui.table import Table
```

In `RichRenderer.__init__`, keep the theme: add `self._theme = theme` before the console is built. Replace the bodies of the three methods:

```python
    def header(self, title: str, style: str) -> None:
        """Print a section header; the renderer's own theme styles it."""
        self._console.print(Header(title).render(self._theme))

    def panel(self, title: str, body: str, border_style: str) -> None:
        """Print the body inside a bordered panel; the renderer's own theme styles it."""
        self._console.print(Panel(title, body).render(self._theme))

    def table(self, title: str, columns: list[str], rows: list[list[str]], header_style: str) -> None:
        """Print the rows as a table under one header rule; the renderer's own theme styles it."""
        table = Table(tuple(columns), tuple(tuple(row) for row in rows), title)
        self._console.print(table.render(self._theme))
```

Remove the now-unused local imports of `rich.panel.Panel` and `rich.table.Table` from those methods.

- [ ] **Step 4: Run the whole suite**

Run: `python -m pytest tests -q`
Expected: everything passes, the 110 baseline tests unchanged among them.

Orchestrator's commit: `feat(renderer): draw table, panel and header through components`. Changelog line: `- 2026-09-21 — Changed `RichRenderer.table`, `panel` and `header` to draw through components; tables lose their frame (`sushicore/renderer.py`).`

---

### Task 9: `HelpPage`

**Acceptance criterion:** `HelpPage(model, show_logo).render(theme)` lays out title, usage, command groups, arguments, options and examples in that order, omits empty sections, and shows the logo only on a root page when asked.

**Files:**
- Create: `sushicore/help/page.py`
- Test: `tests/help/test_page.py`

**Interfaces:**
- Consumes: `HelpModel`, `HelpSection` (Task 7); `Logo`, `Title`, `Usage`, `DefinitionList` (Tasks 4, 6); `Component`; `Theme`.
- Produces: `HelpPage(model: HelpModel, show_logo: bool = False)` with `render(theme) -> RenderableType`. Task 10 calls it.

- [ ] **Step 1: Write the tests** `tests/help/test_page.py`

```python
"""HelpPage lays a HelpModel out from components."""

from sushicore.help.model import HelpModel, HelpSection
from sushicore.help.page import HelpPage
from tests.ui.capture import capture

K_BLOCKS = "▀▄█"


def _leaf() -> HelpModel:
    return HelpModel(
        name="hub add", description="Bring a module in.", usage="hub add [OPTIONS] MODULE",
        is_root=False, commands=(),
        arguments=(("MODULE", "The module."),),
        options=(("--dry-run", "Show the plan only."),),
        examples=(("hub add sr", "Bring sushiruntime in"),),
    )


def _root() -> HelpModel:
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


def test_the_logo_shows_on_a_root_page_when_asked():
    assert any(ch in capture(HelpPage(_root(), show_logo=True)) for ch in K_BLOCKS)


def test_the_logo_stays_off_unless_asked():
    assert not any(ch in capture(HelpPage(_root())) for ch in K_BLOCKS)


def test_the_logo_never_shows_on_a_sub_command_page():
    assert not any(ch in capture(HelpPage(_leaf(), show_logo=True)) for ch in K_BLOCKS)
```

- [ ] **Step 2: Run and see it fail**

Run: `python -m pytest tests/help/test_page.py -v`
Expected: `ModuleNotFoundError: sushicore.help.page`.

- [ ] **Step 3: Implement** `sushicore/help/page.py`

```python
"""Lays a HelpModel out as components: the order of a help screen, and nothing else."""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from rich.console import Group, RenderableType
from rich.text import Text

from ..theme import Theme
from ..ui.component import Component
from ..ui.definition_list import DefinitionList
from ..ui.logo import Logo
from ..ui.title import Title
from ..ui.usage import Usage
from .model import HelpModel

K_ARGUMENTS = "Arguments"
K_OPTIONS = "Options"
K_EXAMPLES = "Examples"


@final
@dataclass(frozen=True, slots=True)
class HelpPage:
    """Draws one help screen; it knows the order of the blocks, not how each draws."""

    model: HelpModel
    show_logo: bool = False

    def render(self, theme: Theme) -> RenderableType:
        """Return the blocks in order, one blank line between neighbours."""
        parts: list[RenderableType] = []
        for block in self._blocks():
            if parts:
                parts.append(Text(""))
            parts.append(block.render(theme))
        return Group(*parts)

    def _blocks(self) -> list[Component]:
        """Return the components to draw: logo, title, usage, then each non-empty list."""
        model = self.model
        blocks: list[Component] = []
        if self.show_logo and model.is_root:
            blocks.append(Logo())
        blocks.append(Title(model.name, model.description))
        blocks.append(Usage(model.usage))
        blocks += [DefinitionList(s.heading, s.entries) for s in model.commands]
        for heading, entries in (
            (K_ARGUMENTS, model.arguments),
            (K_OPTIONS, model.options),
            (K_EXAMPLES, model.examples),
        ):
            if entries:
                blocks.append(DefinitionList(heading, entries))
        return blocks
```

- [ ] **Step 4: Run and see it pass**

Run: `python -m pytest tests/help -v`
Expected: all pass. `HelpPage` imports `sushicore.ui.*`, so it must not be imported by any `ui/` file; the architecture test still passes.

Orchestrator's commit: `feat(help): add HelpPage`. Changelog line: `- 2026-09-21 — Added `HelpPage`, which lays a help model out from components (`sushicore/help/page.py`).` After this task the orchestrator also writes `sushicore/ui/__init__.py` (re-exporting the seven components) and `sushicore/help/__init__.py` (re-exporting `HelpModel`, `HelpSection`, `build_model`, `HelpPage`) and adds a `sushicore.help` row to `README.md` and `docs/README.md`.

---

## Wave 4

### Task 10: `help_group`

**Acceptance criterion:** `typer.Typer(cls=help_group(provider))` prints the `HelpPage` for `--help` at the root, at a sub-group and at a leaf, and for a bare `ctx.get_help()`.

**Files:**
- Create: `sushicore/typer_help.py`
- Test: `tests/test_typer_help.py`

**Interfaces:**
- Consumes: `Console` (`.console` the raw Rich console, and `.theme` from Task 1); `build_model` (Task 7) and `HelpPage` (Task 9).
- Produces: `HelpGroup(TyperGroup)` and `help_group(console: Callable[[], Console]) -> type[HelpGroup]`. Adopters write `typer.Typer(cls=help_group(provider))` on the root and on every `add_typer` sub-app.

Findings this task rests on, measured on Typer 0.20 / Click 8.2.1 in the session: `command_class` on a group is ignored, because Typer builds every command with `command_info.cls or TyperCommand`; wrapping the group's `get_command` and replacing the child's `format_help` works for `--help` at every level; a nested group built with its own `cls` must not be re-wrapped by its parent, or it loses its own page.

- [ ] **Step 1: Write the tests** `tests/test_typer_help.py`

```python
"""help_group draws every --help level as a HelpPage."""

import io

import typer
from rich.console import Console as RichConsole
from typer.testing import CliRunner

from sushicore.console import Console
from sushicore.icons import IconSet
from sushicore.renderer import PlainRenderer
from sushicore.theme import Theme
from sushicore.typer_help import help_group


def _app() -> typer.Typer:
    console = Console(PlainRenderer(stream=io.StringIO()), Theme(), IconSet())
    group = help_group(lambda: console)
    app = typer.Typer(cls=group, name="hub", help="Manage the stack.", rich_markup_mode="rich")
    gui = typer.Typer(cls=group, name="gui", help="The desktop application.")
    app.add_typer(gui, name="gui", rich_help_panel="Desktop app")

    @app.callback(invoke_without_command=True)
    def root(ctx: typer.Context):
        if ctx.invoked_subcommand is None:
            typer.echo(ctx.get_help())
            raise typer.Exit(0)

    @app.command("add", rich_help_panel="Modules", epilog="hub add sr  # bring sushiruntime in")
    def add(
        module: str = typer.Argument(..., help="The module."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Show the plan only."),
    ):
        """Bring a module in."""

    @app.command("doctor")
    def doctor():
        """Check tools."""

    @gui.command("build", epilog="hub gui build --type release")
    def build():
        """Build it."""

    return app


def _run(*args: str) -> str:
    result = CliRunner().invoke(_app(), list(args))
    assert result.exit_code == 0, result.output
    return result.output


def test_root_help_groups_commands_under_their_panels():
    out = _run("--help")
    assert "Modules" in out and "Desktop app" in out and "Commands" in out
    assert out.index("Modules") < out.index("  add") < out.index("Desktop app") < out.index("  gui")


def test_a_bare_invocation_prints_the_same_page():
    assert _run() == _run("--help")


def test_leaf_help_lists_arguments_options_and_examples():
    out = _run("add", "--help")
    assert "Arguments" in out and "MODULE" in out
    assert "--dry-run" in out and "Show the plan only." in out
    assert "Examples" in out and "hub add sr" in out and "bring sushiruntime in" in out


def test_a_sub_group_draws_its_own_page_not_a_leaf_page():
    out = _run("gui", "--help")
    assert "build" in out and "Usage: hub gui" in out


def test_a_leaf_below_a_sub_group_draws_a_page():
    out = _run("gui", "build", "--help")
    assert "Usage: hub gui build" in out and "hub gui build --type release" in out


def test_a_command_with_no_panel_lands_under_commands():
    out = _run("--help")
    assert out.index("Commands") < out.index("  doctor")


def test_no_logo_on_a_console_that_is_not_a_terminal():
    assert not any(ch in _run("--help") for ch in "▀▄█")


class _TerminalConsole:
    """Stands in for a sushicore Console whose Rich console is a truecolour terminal."""

    theme = Theme()
    console = RichConsole(
        file=io.StringIO(), force_terminal=True, color_system="truecolor", width=80,
    )


def test_the_root_page_shows_the_logo_on_a_colour_terminal_and_a_leaf_does_not():
    group = help_group(lambda: _TerminalConsole())
    app = typer.Typer(cls=group, name="hub", help="Manage the stack.")

    @app.command("add")
    def add():
        """Bring a module in."""

    @app.command("doctor")
    def doctor():
        """Check tools."""

    runner = CliRunner()
    assert any(ch in runner.invoke(app, ["--help"]).output for ch in "▀▄█")
    assert not any(ch in runner.invoke(app, ["add", "--help"]).output for ch in "▀▄█")
```

- [ ] **Step 2: Run and see it fail**

Run: `python -m pytest tests/test_typer_help.py -v`
Expected: `ModuleNotFoundError: sushicore.typer_help`.

- [ ] **Step 3: Implement** `sushicore/typer_help.py`

```python
"""Wires the help page into Typer; the only module in sushicore that imports Typer.

Typer builds each command with its own class, so a group cannot hand its children a
help renderer. The group replaces each child's format_help as it hands the child out.
"""

from __future__ import annotations

import io
from typing import Any, Callable, ClassVar

import click
from rich.console import Console as RichConsole
from typer.core import TyperGroup

from .console import Console
from .help.from_click import build_model
from .help.page import HelpPage
from .theme import Theme

K_LOGO_COLOUR_SYSTEMS = ("256", "truecolor")


class HelpGroup(TyperGroup):
    """Draws its own help, and its children's, as a HelpPage."""

    console_provider: ClassVar[Callable[[], Console]]
    draws_help_page: ClassVar[bool] = True

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Write this group's help page into the formatter."""
        _write_page(self, ctx, formatter, self.console_provider())

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        """Return the child command, with its help redirected to the page unless it draws its own."""
        command = super().get_command(ctx, cmd_name)
        if command is not None and not getattr(command, "draws_help_page", False):
            provider = self.console_provider
            command.format_help = lambda c, f, _command=command: _write_page(
                _command, c, f, provider(),
            )
        return command


def help_group(console: Callable[[], Console]) -> type[HelpGroup]:
    """Return a HelpGroup subclass that draws with the console ``console()`` returns."""
    return type("SushiGroup", (HelpGroup,), {"console_provider": staticmethod(console)})


def _write_page(command: Any, ctx: click.Context, formatter: click.HelpFormatter, console: Console) -> None:
    """Build the page for ``command`` and write it, drawn for ``console``, into ``formatter``."""
    raw = console.console
    page = HelpPage(build_model(command, ctx), show_logo=_logo_visible(raw))
    formatter.write(_draw(page, console.theme, raw))


def _logo_visible(raw: RichConsole) -> bool:
    """Report whether the console can show the logo: a UTF-8 terminal with 256 colours or more."""
    return (
        raw.is_terminal
        and not raw.no_color
        and raw.color_system in K_LOGO_COLOUR_SYSTEMS
        and raw.encoding.lower().startswith("utf")
    )


def _draw(page: HelpPage, theme: Theme, raw: RichConsole) -> str:
    """Return the page as text shaped like ``raw``: its width, colour system and colour setting."""
    target = RichConsole(
        file=io.StringIO(),
        width=raw.width,
        force_terminal=raw.is_terminal,
        color_system=raw.color_system,
        no_color=raw.no_color,
        legacy_windows=False,
        highlight=False,
    )
    target.print(page.render(theme))
    return target.file.getvalue()
```

- [ ] **Step 4: Run and see it pass**

Run: `python -m pytest tests -q`
Expected: everything passes. A Click `echo` strips colour codes from a non-terminal stream, so the tests read plain text.

Orchestrator's commit: `feat: add help_group, the Typer help screen`. Changelog line: `- 2026-09-21 — Added `help_group`, the Typer group that draws every help screen as a `HelpPage` (`sushicore/typer_help.py`).` The same commit adds the `typer` extra and its `test` inclusion to `pyproject.toml`, a `sushicore.typer_help` row to `README.md`, and raises the version to 0.4.0.

---

## Wave 5: `hub` adopts it (repository `D:/Projects/sushistack`)

Gated on the owner publishing sushicore 0.4.0, or installing the local checkout into the environment the hub tests use. The orchestrator raises `sushicore>=0.3.0` to `sushicore>=0.4.0` in `sushihub/cli/pyproject.toml`.

### Task 11: `hub` groups its commands and adds examples

**Acceptance criterion:** `hub --help` shows the five command groups, and `hub add --help` and `hub gui build --help` show an Examples section.

**Files:**
- Modify: `sushihub/cli/sushistack/console.py`
- Modify: `sushihub/cli/sushistack/cli.py`
- Test: `sushihub/cli/tests/test_help_screen.py`

**Interfaces:**
- Consumes: `sushicore.typer_help.help_group`; the module's `_lazy` console.
- Produces: `sushistack.console.current() -> sushicore.Console`, the provider handed to `help_group`.

- [ ] **Step 1: Write the test** `sushihub/cli/tests/test_help_screen.py`

```python
"""hub's help screen groups its commands and carries examples."""

from typer.testing import CliRunner

from sushistack.cli import app


def _run(*args: str) -> str:
    result = CliRunner().invoke(app, list(args))
    assert result.exit_code == 0, result.output
    return result.output


def test_root_help_shows_the_five_groups_in_order_of_first_appearance():
    lines = [line.rstrip() for line in _run("--help").splitlines()]
    positions = [lines.index(h) for h in ("Workspace", "Modules", "Dependencies", "Desktop app", "Account")]
    assert positions == sorted(positions)


def test_every_top_level_command_is_listed():
    out = _run("--help")
    for name in ("init", "home", "status", "add", "link", "install-cli", "update",
                 "sync", "install", "doctor", "remove", "login", "logout", "whoami",
                 "license", "gui"):
        assert f"  {name}" in out


def test_a_command_help_carries_examples():
    assert "hub add sr" in _run("add", "--help")


def test_a_gui_command_help_carries_examples():
    out = _run("gui", "build", "--help")
    assert "Examples" in out and "hub gui build" in out
```

- [ ] **Step 2: Run and see it fail**

Run: `python -m pytest sushihub/cli/tests/test_help_screen.py -v` from `D:/Projects/sushistack`
Expected: failures (`Workspace` is not in Typer's help yet).

- [ ] **Step 3: Implement**

In `sushihub/cli/sushistack/console.py` add, below `is_machine`:

```python
def current():
    """Return the sushicore Console this run prints through, building it on first use."""
    return _lazy.get()
```

In `sushihub/cli/sushistack/cli.py` import `from sushicore.typer_help import help_group`, define `_help_group = help_group(console.current)` above `app`, and pass `cls=_help_group` to both `typer.Typer(...)` calls (`app`, `gui_app`). Change `app.add_typer(gui_app, name="gui")` to `app.add_typer(gui_app, name="gui", rich_help_panel="Desktop app")`. Add `rich_help_panel` and `epilog` to every top-level command decorator:

| Command | `rich_help_panel` | `epilog` lines |
| --- | --- | --- |
| `init` | Workspace | `hub init  # Mark this directory as a workspace` |
| `home` | Workspace | `hub home` |
| `status` | Workspace | `hub status` and `hub status --check-updates  # Fetch each checkout first` |
| `add` | Modules | `hub add sr  # Bring sushiruntime in`, `hub add all --dry-run  # Show the plan only`, `hub add se --binary  # Install sushiengine from its release` |
| `link` | Modules | `hub link se ../sushiengine  # Register an existing checkout` |
| `install-cli` | Modules | `hub install-cli sr` |
| `update` | Modules | `hub update`, `hub update sr --dry-run` |
| `sync` | Modules | `hub sync` |
| `install` | Dependencies | `hub install`, `hub install --customize  # Pick toolchains interactively`, `hub install --dry-run` |
| `doctor` | Dependencies | `hub doctor` |
| `remove` | Dependencies | `hub remove --all --dry-run  # Show what --all would remove` |
| `login` | Account | `hub login` |
| `logout` | Account | `hub logout` |
| `whoami` | Account | `hub whoami` |
| `license` | Account | `hub license` |
| `gui build` | none | `hub gui build --type release`, `hub gui build --clean` |
| `gui test` | none | `hub gui test --filter <pattern>`, `hub gui test --repeat 5` |
| `gui run` | none | `hub gui run` |
| `gui clean` | none | `hub gui clean` |

Before writing each `epilog` the worker checks the example against the command's real options (the `@app.command` signature in `cli.py`, and `sushihub/cli/README.md`), and drops or corrects an example that names an option the command does not have. An `epilog` is one string with one example per line, `command  # note`, the note optional.

- [ ] **Step 4: Run the hub suite**

Run: `python -m pytest sushihub/cli/tests -q` from `D:/Projects/sushistack`
Expected: everything passes; `test_json_streams.py` and `test_module_manifest.py` are untouched by help text, and `hub --describe` still serialises the same catalogue.

Orchestrator's commit: `feat(cli): group hub's help and add examples`. Changelog line in `docs/reference/CHANGELOG.md` of SushiStack, in that file's existing format. The same commit updates `sushihub/cli/README.md` (a short "Help" paragraph naming the five groups and where an example lives) and `pyproject.toml`.

---

## Self-review

**Spec coverage.** Component layer and `Component` protocol: Task 2. `Theme.muted`: Task 1. `brand.py` and the logo: Tasks 3, 4. Quiet table, header, panel: Task 5, delegated by Task 8. Title, usage, lists: Task 6. Help model and Click reader: Task 7. Page: Task 9. Typer group, logo visibility rule, string route that keeps `ctx.get_help()` working: Task 10. Machine output: Task 10 writes through Click's formatter and touches no `JsonRenderer` path. Architecture test: Task 2. Tests: every task. Docs and release: changelog per task, README and `docs/README.md` rows in Tasks 6, 9 and 10, version and extra in Task 10's commit. `hub` adoption and its five groups: Task 11.

**Departures from the spec, each recorded in the spec's amended text.** `CommandGroup`, `ParamList` and `Examples` are one `DefinitionList`, because all three were a heading over two columns. `Console.theme` is a new public property the spec did not list, needed so `typer_help` can read the theme. The Typer `command_class` question is settled by measurement: it does not work, and the group wraps each child's `format_help`. Help is written through Click's formatter, so it goes to stdout as it does today, not to the console's own stream.

**Type consistency.** `HelpSection`, `HelpModel` field names, `build_model(command, ctx)`, `HelpPage(model, show_logo)`, `Logo(indent)`, `Table(columns, rows, title)`, `DefinitionList(heading, entries)`, `help_group(console)` and `console.current` are spelled the same wherever they appear.

**Not verified.** The logo grid and the truecolour golden depend on a human look at the traced preview and at a real terminal; the plan makes the owner approve both at the Wave 1 and Wave 2 reviews. Nothing has been run against Click older than 8.2.1 (`make_metavar(ctx)` takes a context there).


---

## Wave 6: a smaller logo, a wordmark and a dark-terminal glow

Added 2026-09-21 after the owner reviewed the built logo. The owner's decisions:

- The logo is too tall (10 terminal rows). It shrinks, and the words "SUSHI SYSTEMS" go beside it so it is not empty, in the site's font.
- On a dark terminal the nori (black seaweed) disappears. A soft neon back-light fixes it: choice **C**, two pixels falling off from an inner bright ring to a dim outer one.
- A light terminal stays as it was: no glow.
- Dark or light is decided by `COLORFGBG` when the terminal sets it, and otherwise the glow stays off. A `[cli] background = "dark"` setting turns it on.

Design. The mark is 18 by 16 pixels (a 14 by 12 roll and a 2-pixel halo), 8 terminal rows. The wordmark is two lines, `SUSHI` over `SYSTEMS`, 43 by 14 pixels, in a hand-drawn heavy condensed pixel font. Auto-resampling the site's wordmark was tried and is unreadable at this height. `SUSHI` uses the terminal's own foreground colour, so it reads on dark and light terminals alike, and `SYSTEMS` is amber. The full lockup is 2 + 18 + 2 + 43 = 65 columns. On a narrower console the wordmark is dropped, and below 20 columns the logo is dropped.

Interfaces fixed here, which Task 15 and later adopters depend on:

- `sushicore.brand`: `K_TRANSPARENT`, `K_FOREGROUND_KEY = "w"`, `K_PALETTE`, `K_GLOW_PALETTE`, `K_MARK_PIXELS`, `K_WORDMARK_PIXELS`. `K_LOGO_PIXELS` is removed; only `ui/logo.py` read it.
- `Logo(indent: int = 2, wordmark: bool = True, glow: bool = False)` with a `width` property (columns, indent included).
- `sushicore.terminal_background.is_dark_background(setting: str, environ: Mapping[str, str]) -> bool`.
- `AppearanceSpec.background: str = "auto"`, the `[cli] background` key and the `SUSHI_CLI_BACKGROUND` variable; `Console(renderer, theme, icons, dark_background: bool = False)` with a `dark_background` property.
- `sushicore.help.logo_choice.choose_logo(*, width: int, dark_background: bool) -> Logo | None`.
- `HelpPage(model, logo: Component | None = None)` replaces `HelpPage(model, show_logo: bool = False)`.

Wave 6 runs as 6a (Tasks 13, 14 and 16, disjoint files) then 6b (Tasks 15 and 17, on disjoint files; Task 15 reads `Logo.width` and never a literal, so it does not wait for 17). Models: opus for Tasks 13, 14 and 15, because each fixes a public interface; sonnet for Task 16.

| Wave | Tasks | Files | Waits on | Build the owner runs after it |
| --- | --- | --- | --- | --- |
| 6a | 13 Logo data and component | `sushicore/brand.py`, `sushicore/ui/logo.py`, `tests/test_brand.py`, `tests/ui/test_logo.py`, `tests/golden/logo_*_truecolor.txt` | Wave 4 | `python -m pytest tests -q` |
| 6a | 14 Background detection | `sushicore/terminal_background.py`, `sushicore/config.py`, `sushicore/console.py`, `sushicore/__init__.py`, `tests/test_terminal_background.py`, `tests/test_appearance_background.py` | Wave 4 | same |
| 6a | 16 Review fixes outside the logo | `sushicore/renderer.py`, `sushicore/ui/header.py`, `sushicore/ui/panel.py`, `sushicore/ui/definition_list.py`, `sushicore/help/from_click.py`, `tests/conftest.py`, `tests/ui/capture.py`, `tests/ui/test_header.py`, `tests/ui/test_panel.py`, `tests/ui/test_definition_list.py`, `tests/test_renderer_components.py` | Wave 4 | same |
| 6b | 17 Trim the logo's empty margin | `sushicore/ui/logo.py`, `tests/ui/test_logo.py`, `tests/golden/logo_light_truecolor.txt` | 13 | same |
| 6c | 18 Larger, symmetric wordmark and a white glow | `sushicore/brand.py`, `tests/test_brand.py`, `tests/ui/test_logo.py`, `tests/golden/logo_dark_truecolor.txt`, `tests/golden/logo_light_truecolor.txt` | 17 | same |
| 6b | 15 Choose and wire the logo | `sushicore/help/logo_choice.py`, `sushicore/help/page.py`, `sushicore/typer_help.py`, `tests/help/test_logo_choice.py`, `tests/help/test_page.py`, `tests/test_typer_help.py` | 13, 14, 16 | same |

### Task 13: the logo data and component

**Acceptance criterion:** `Logo` draws the mark, optionally the wordmark and the glow, from `brand.py`; `python -m pytest tests -q` passes; the old golden is replaced by two goldens.

**Data.** `sushicore/brand.py` becomes:

```python
"""The Sushi Systems mark and wordmark as data: palettes and pixel grids.

Mark keys: n nori, r rice, a amber, g green, h inner glow, H outer glow.
Wordmark keys: w the terminal's own foreground, a amber. "." is transparent.
Only ui/logo.py reads this module.
"""

from __future__ import annotations

K_TRANSPARENT = "."
K_FOREGROUND_KEY = "w"

K_PALETTE: dict[str, str] = {
    "n": "#1a1c20",
    "r": "#f4f4f4",
    "a": "#f0a500",
    "g": "#4caf50",
}

K_GLOW_PALETTE: dict[str, str] = {
    "h": "#5c3f00",
    "H": "#2a1d00",
}

K_MARK_PIXELS: tuple[str, ...] = (
    ".....HHHHHHHH.....",
    "...HHhhhhhhhhH....",
    "..HhhnnnnnnnnhH...",
    ".HhnrrrrrrrnnnhH..",
    ".HhrrrrrrrrrnnnhH.",
    "HhnrraaaaarrrnnhH.",
    "HhnraaaaaaarrnnnhH",
    "HhnraaaaaaaarnnnhH",
    "HhnraaaaaaaarnnnhH",
    "HhnraaaaaaaarnnnhH",
    "HhnrragggggrrnnnhH",
    "HhnrrrrggrrrrnnhH.",
    ".HhnrrrrrrrrnnhH..",
    "..HhhnnnnnnnhhH...",
    "...HHhhhhhhhHH....",
    ".....HHHHHHH......",
)

K_WORDMARK_PIXELS: tuple[str, ...] = (
    ".wwww.ww.ww..wwww.ww.ww.ww.................",
    "ww....ww.ww.ww....ww.ww.ww.................",
    ".www..ww.ww..www..wwwww.ww.................",
    "...ww.ww.ww....ww.wwwww.ww.................",
    "...ww.ww.ww....ww.ww.ww.ww.................",
    "wwww...www..wwww..ww.ww.ww.................",
    "...........................................",
    "...........................................",
    ".aaaa.aa.aa..aaaa.aaaaa.aaaaa.aaa.aaa..aaaa",
    "aa....aa.aa.aa......a...aa....aaaaaaa.aa...",
    ".aaa...aaa...aaa....a...aaaa..aaaaaaa..aaa.",
    "...aa...a......aa...a...aa....aa.a.aa....aa",
    "...aa...a......aa...a...aa....aa...aa....aa",
    "aaaa....a...aaaa....a...aaaaa.aa...aa.aaaa.",
)
```

The mark is the traced roll from Task 3, resampled to 14 by 12 and wrapped in two rings (`h` next to the roll, `H` outside it, four-neighbour growth). The wordmark is drawn by hand: each letter is 6 pixels tall, `S U H E T Y` are 5 wide, `I` is 2 wide, `M` is 7 wide, one blank column between letters, two blank rows between the lines. Keep the strings exactly as given.

**`Logo`.** In `sushicore/ui/logo.py`:

```python
K_GAP = 2  # transparent pixel columns between the mark and the wordmark


@final
@dataclass(frozen=True, slots=True)
class Logo:
    """Draws the brand mark, with the wordmark beside it and a glow behind it when asked."""

    indent: int = 2
    wordmark: bool = True
    glow: bool = False

    @property
    def width(self) -> int:
        """Return the columns one row takes, indent included."""

    def render(self, theme: Theme) -> Text:
        """Return the logo as styled text, two pixel rows per terminal row."""
```

Rules: the pixel grid is the mark; with `wordmark` it is the mark, `K_GAP` transparent columns, and the wordmark, each vertically centred in the taller of the two (`(rows - height) // 2` blank rows above), padded with transparent pixels to a common width and to an even number of rows. The colour of a key is `K_PALETTE[key]`, plus `K_GLOW_PALETTE[key]` when `glow` is true, plus the terminal's default colour (`"default"`) for `K_FOREGROUND_KEY`. A key with no colour is transparent, so with `glow=False` the two ring keys draw nothing. `_cell` keeps its cases (both transparent, top only, bottom only, equal, different) and takes the colour dict as an argument. `width` is `indent + mark width` plus `K_GAP + wordmark width` when `wordmark`.

**Tests.**

- `tests/test_brand.py`: each grid is rectangular; the mark has an even number of rows; the wordmark has an even number of rows; the mark uses only `K_PALETTE`, `K_GLOW_PALETTE` and `K_TRANSPARENT` keys; the wordmark uses only `K_FOREGROUND_KEY`, `"a"` and `K_TRANSPARENT`; every key of each palette appears in the mark or wordmark; palette values are lowercase `#rrggbb`; the mark is at most 24 by 24 and the wordmark at most 48 by 16.
- `tests/ui/test_logo.py`: the two-pixel-rows-to-one-row test; a default `Logo()` is 8 terminal rows and its `width` is 65; `Logo(wordmark=False)` has `width` 20 and no row wider than 20; `Logo(indent=0).width` is 63; with `glow=False` no glow colour appears in `capture_ansi` output, and with `glow=True` a tiny-grid test shows `h` as `\x1b[38;2;92;63;0m` and `H` as `\x1b[38;2;42;29;0m` (monkeypatch `sushicore.ui.logo.K_MARK_PIXELS`, `K_WORDMARK_PIXELS`, `K_PALETTE` and `K_GLOW_PALETTE` with tiny grids for the cell tests, as the existing tests do); the wordmark's default-foreground pixels emit SGR `39`; two goldens, `tests/golden/logo_dark_truecolor.txt` for `Logo(glow=True)` and `tests/golden/logo_light_truecolor.txt` for `Logo(glow=False)`, both at width 80. Delete `tests/golden/logo_truecolor.txt`. The owner approved this redesign, so replacing the golden is an approved update: say so in the report.

### Task 14: background detection

**Acceptance criterion:** `is_dark_background` decides from a setting and `COLORFGBG`; `[cli] background` and `SUSHI_CLI_BACKGROUND` reach `Console.dark_background` through `build_console`; `python -m pytest tests -q` passes.

**`sushicore/terminal_background.py`:**

```python
"""Decides whether a terminal's background is dark, from a setting and COLORFGBG."""

from __future__ import annotations

from typing import Mapping

K_DARK = "dark"
K_LIGHT = "light"
K_AUTO = "auto"
K_VALUES = (K_AUTO, K_DARK, K_LIGHT)


def is_dark_background(setting: str, environ: Mapping[str, str]) -> bool:
    """Report whether the background is dark: the setting when it names one, COLORFGBG otherwise."""
```

`"dark"` returns true and `"light"` false. `"auto"` reads `COLORFGBG` (`"15;0"` or `"15;default;0"`): the last `;`-separated part, when it is a non-negative integer, is the background colour index, dark when it is 0 to 6 or 8 and light for anything else. A missing, empty or unparsable value is unknown, and unknown is `False`: no guessing, so a light terminal never gets a glow.

**Config.** `AppearanceSpec` gains `background: str = "auto"`. `load_appearance` reads `[cli] background` (a string, also under `[cli.<platform>]`, like the other keys) and `SUSHI_CLI_BACKGROUND`, the environment winning. A value outside `K_VALUES` becomes `"auto"`, as `color` does. The schema in the module docstring of `config.py` gains `background = "auto"      # auto | dark | light`.

**Console.** `Console.__init__(self, renderer, theme, icons, dark_background: bool = False)` stores it; a read-only `dark_background` property returns it. `build_console` computes `is_dark_background(spec.background, os.environ)` and passes it. `Console` still never reads the environment itself.

**Tests.** `tests/test_terminal_background.py`: `"dark"` and `"light"` ignore `COLORFGBG`; auto with `"15;0"`, `"15;default;0"`, `"7;6"` and `"7;8"` is true; auto with `"0;15"`, `"0;7"`, `"15;9"`, `""`, `"garbage"` and no variable is false. `tests/test_appearance_background.py`: default is `"auto"`; `[cli] background = "dark"` in a temp TOML file; the environment overrides the file; an invalid value becomes `"auto"`; `Console(..., dark_background=True).dark_background` is true and the default false; `build_console([config_with_dark])` gives a console whose `dark_background` is true, and with `COLORFGBG="15;0"` in the environment and no setting it is true, without both it is false. Follow how `tests/test_lazy_console.py` and `tests/test_config_writer.py` build temp config. Use `monkeypatch` for the environment, and clear `COLORFGBG` and `SUSHI_CLI_BACKGROUND` in every test that does not set them.


### Task 16: fixes from the second review

Source: `docs/agent/reports/2026-09-21-terminal-components-review-wave-4.md`. The findings below were measured by the reviewer; the worker reproduces each before fixing it. Task 15 takes the two findings that live in `typer_help.py`.

**Acceptance criterion:** each of the five items below has a test that fails first and passes after, and `python -m pytest tests -q` passes.

1. **Rich's style cache poisons the suite.** `Style._add` caches ANSI codes per style without keying on the colour system, so rendering a style to a 256-colour console and then to a truecolour one emits the 256-colour codes. Move the clearing out of `tests/test_typer_help.py` into an autouse fixture in a new `tests/conftest.py`, so no collection order can break `tests/ui/test_logo.py`'s golden, and clear `Style._add` only (`Style.parse.cache_clear()` does nothing for this). Leave the fixture in `tests/test_typer_help.py` in place: Task 15 removes it. Prove the fixture is needed: with it disabled and a 256-colour render placed before the truecolour golden, the golden test fails.
2. **`import sushicore` loads Rich.** `sushicore/renderer.py` imports `Header`, `Panel` and `Table` at module level, and every other Rich import in that file sits inside a method. Move the three imports into the methods that use them. Add a test that runs `python -c "import sys, sushicore; sys.exit('rich' in sys.modules)"` in a subprocess with `PYTHONPATH` set to the repository and asserts exit code 0.
3. **Header and panel titles stopped parsing markup.** `Console.header("[bold]Setup[/bold]")` and `Console.fail_panel("[red]Failed[/red]", ...)` worked in 0.3.0 and now print the brackets. Restore it: `Header` and `Panel` build their title with `Text.from_markup(title, style=...)`, the theme style applied under the markup. Tests in `tests/ui/test_header.py`, `tests/ui/test_panel.py` and `tests/test_renderer_components.py`: a marked-up title prints without its tags. `Text.from_markup` raises on a stray `[/]`, so a title with one escapes it with `rich.markup.escape` in the test's input, not in the component.
4. **Every definition-list row is padded to the console width.** `rich.padding.Padding` expands by default. Pass `expand=False` in `sushicore/ui/definition_list.py`. Add a `capture_raw` helper to `tests/ui/capture.py` that keeps trailing spaces, and a test that at width 200 no line of a two-entry list is longer than 60 characters.
5. **Comments and docstrings.** In `renderer.py` the three delegating methods' docstrings each explain the ignored style argument after a semicolon: shorten each to one sentence stating what it prints. `sushicore/help/from_click.py`'s module docstring argues ("It imports neither Click nor Typer: it asks the command object for what it has"): make it a statement of what the module does, at most three lines.

Not fixed on purpose: `RichRenderer` still accepts the style arguments the `Renderer` Protocol declares and ignores them, because changing the Protocol is a breaking change for every CLI; the second review's finding stays on record.


### Task 17: trim the logo's empty margin

Source: the orchestrator's measurement after Task 13. With `glow=False` the two outer glow rings draw nothing, but the mark still keeps them: four blank pixel rows (0, 1, 14, 15) and four blank columns (0, 1, 16, 17), so a light terminal gets a blank first line and a two-column left shift. The owner asked that a light terminal "stay normal".

**Acceptance criterion:** with `glow=False` the logo has no empty edge row and no empty edge column, with `glow=True` it is unchanged, and `python -m pytest tests -q` passes.

**Rule.** After `Logo` has chosen its colours, it trims the mark before composing: leading and trailing pixel rows in which no pixel has a colour are removed, and so are leading and trailing columns in which no pixel has a colour. If the trimmed mark has an odd number of rows, one transparent row is added at the bottom, so half-block pairing holds. Trimming applies to the mark only; the wordmark grid is used as it is. `width` and `render` use the same trimmed mark, so they cannot disagree, and both still read the module globals at call time. The result: `Logo(glow=True)` keeps its 18 by 16 mark, 8 terminal rows and width 65; `Logo(glow=False)` has a 14 by 12 mark, 7 terminal rows (the wordmark, 14 pixel rows, is the taller side) and width 61; `Logo(glow=False, wordmark=False)` has 6 terminal rows and width 16; `Logo(glow=True, wordmark=False)` has 8 rows and width 20.

**Tests** in `tests/ui/test_logo.py`: the four combinations above, measured (rows from `capture`, width from the property); a tiny-grid test in which a fully transparent top row, bottom row, left column and right column disappear with `glow=False` and stay with `glow=True`; a tiny-grid test where trimming leaves an odd row count and one transparent row is added; `Logo(glow=False, wordmark=False)` has no blank first line. Replace `tests/golden/logo_light_truecolor.txt` (the dark golden must not change). The owner asked for this look, so replacing the light golden is an approved update: say so in the report.


### Task 18: a larger, symmetric wordmark and a white glow

Source: the owner, after seeing the built logo. The heavy 6-pixel wordmark had an `M` that looked out of proportion, and the amber glow did not match the site's logo, which has a faint white halo behind the icon. The owner asked for a slightly larger wordmark with letters "as symmetric as possible", and a glow in white tones. Two sets of letters and two white glows were drawn and compared by eye; the owner chose set A with the strong glow.

**Acceptance criterion:** the wordmark is the 7-pixel-tall set below, the two glow colours are white tones, the sizes in `test_brand.py` and `test_logo.py` follow, and `python -m pytest tests -q` passes.

**Data.** In `sushicore/brand.py`:

```python
K_GLOW_PALETTE: dict[str, str] = {
    "h": "#8c8c8c",
    "H": "#3d3d3d",
}

K_WORDMARK_PIXELS: tuple[str, ...] = (
    ".wwwww.ww..ww..wwwww.ww..ww.ww....................",
    "ww.....ww..ww.ww.....ww..ww.ww....................",
    "ww.....ww..ww.ww.....ww..ww.ww....................",
    ".wwww..ww..ww..wwww..wwwwww.ww....................",
    "....ww.ww..ww.....ww.ww..ww.ww....................",
    "....ww.ww..ww.....ww.ww..ww.ww....................",
    "wwwww...wwww..wwwww..ww..ww.ww....................",
    "..................................................",
    "..................................................",
    ".aaaaa.aa..aa..aaaaa.aaaaaa.aaaaaa.aa....aa..aaaaa",
    "aa.....aa..aa.aa.......aa...aa.....aaa..aaa.aa....",
    "aa......aaaa..aa.......aa...aa.....aaaaaaaa.aa....",
    ".aaaa....aa....aaaa....aa...aaaa...aa.aa.aa..aaaa.",
    "....aa...aa.......aa...aa...aa.....aa.aa.aa.....aa",
    "....aa...aa.......aa...aa...aa.....aa....aa.....aa",
    "aaaaa....aa...aaaaa....aa...aaaaaa.aa....aa.aaaaa.",
)
```

Copy the wordmark exactly. It is drawn by hand: every letter is 7 pixels tall and its vertical strokes are 2 pixels wide. `S U H T Y E` are 6 wide, `I` is 2 wide, `M` is 8 wide, one blank column between letters, two blank rows between the lines. `U H I T Y M` are mirror-symmetric and `S` is symmetric under a half turn. The mark grid, `K_PALETTE`, `K_FOREGROUND_KEY` and everything else in `brand.py` stay as they are. Update the module docstring's key line so it no longer says the glow is amber.

**What changes in the sizes.** The wordmark is 50 by 16 pixels. The mark is unchanged (18 by 16 with glow, 14 by 12 without). `Logo(glow=True)` has width `2 + 18 + 2 + 50 = 72` and 8 terminal rows. `Logo(glow=False)` has width `2 + 14 + 2 + 50 = 68` and 8 terminal rows, because the wordmark, 16 pixel rows, is now the taller side. `Logo(wordmark=False)` is unchanged: width 16 and 6 rows without glow, width 20 and 8 rows with it.

**Tests.** In `tests/test_brand.py` raise the wordmark limits to at most 56 columns by 16 rows, keeping the rectangular, even-row, key-set and palette checks, and assert the wordmark has exactly 16 rows. In `tests/ui/test_logo.py` update every number that came from the old wordmark (widths 61 to 68 and 65 to 72, plain rows 7 to 8) and the glow colour codes in the tiny-grid test: `h` is `#8c8c8c`, SGR `38;2;140;140;140`, and `H` is `#3d3d3d`, SGR `38;2;61;61;61`. Add a test that the wordmark's letters are symmetric where they should be: split each line into its letters by the blank columns, and check that `U H I T Y` and `M` read the same mirrored. Regenerate both goldens once from the implementation with a throwaway script; the owner asked for this look, so replacing both goldens is an approved update, and the report says so.

### Task 15: choose the logo and wire it into the page

**Acceptance criterion:** `--help` at the root draws the lockup on a wide dark colour terminal, the mark alone on a narrow one, nothing when even the mark does not fit, and no glow unless `console.dark_background`; `python -m pytest tests -q` passes.

**`sushicore/help/logo_choice.py`:**

```python
"""Chooses which logo, if any, fits a console."""

from __future__ import annotations

from ..ui.logo import Logo


def choose_logo(*, width: int, dark_background: bool) -> Logo | None:
    """Return the widest logo that fits ``width`` columns, or None when none does."""
```

It builds the two candidates, `Logo(glow=dark_background)` and `Logo(wordmark=False, glow=dark_background)`, and returns the first whose own `width` is at most `width`, or `None`. A logo's width depends on `glow`, so the comparison uses the candidate's `width`, never `Logo().width` and never a number.

**`HelpPage`** takes `logo: Component | None = None` in place of `show_logo`; the logo block is added first on a root page when `logo` is not None. **`typer_help`**: `_logo_visible(raw)` keeps the terminal, colour and encoding gate; `_write_page` builds `choose_logo(width=raw.width, dark_background=console.dark_background)` when the gate passes and `None` otherwise, and hands it to `HelpPage`. The stand-in console in `tests/test_typer_help.py` gains `dark_background`.

**Tests.** `tests/help/test_logo_choice.py`: for `glow` on and off, the width of the full lockup and one column below it, the width of the mark alone and one column below it, all read from `Logo(...).width`, and the `glow` and `wordmark` fields of what comes back. `tests/help/test_page.py`: a `Logo` passed as `logo` shows on a root page and not on a leaf; `None` shows nothing; the tests that used `show_logo` are rewritten. `tests/test_typer_help.py`: the terminal tests use a console 80 columns wide and show a logo, one wide enough for the mark but not the lockup shows the mark only (measure its widest row against `Logo(wordmark=False, glow=...).width`), one narrower than the mark shows none; take every width from `Logo(...).width`; a non-terminal console still shows none.


**Amendments to Task 15 from the second review.** In `typer_help.py`:

- `HelpGroup.console_provider` defaults to `None`. When it is `None`, or when building the page raises any `Exception` (a provider that fails outside a workspace, a stray `[/]` in a `rich` docstring), the group logs one warning through `logging.getLogger("sushicore.help")` naming the exception, and falls back to Typer's own help: `TyperGroup.format_help(self, ctx, formatter)` for a group and `type(command).format_help(command, ctx, formatter)` for a child. It never lets a traceback reach `--help`. Tests: a provider that raises `RuntimeError` and one that raises `SystemExit`-free `ValueError` both leave `--help` exit code 0 with Typer's screen and one warning record (`caplog`); `HelpGroup` used directly, without `help_group`, also falls back.
- Remove the Rich style-cache fixture from `tests/test_typer_help.py`; Task 16's `tests/conftest.py` replaces it.
- The module docstring of `typer_help.py` and the docstring of `HelpPage` state what they do in at most three lines each; remove "and nothing else" and "not how each draws".


---

## Wave 7: a readable table for `hub doctor`

Added 2026-09-21 after the owner ran `hub doctor` and found its table unreadable: the `Detail` column wraps
long manifest descriptions to three to six lines, the `Owner` value repeats on every row, and nothing
separates one row from the next. The owner chose, from three drawn layouts, option C: rows grouped by
owner under a heading, the status words coloured, and after the table a one-line summary and a
"Needs attention" list of what is missing. The choice was made on the mock in
`docs/agent/reports/` (Task 19's report reproduces it).

Two changes, in two repositories, in order: Task 19 in sushicore, then Task 20 in `hub`.

**Interface fixed here (Task 19).** `Console.table(columns, rows, title="", *, group_by=None)` and
`Renderer.table(title, columns, rows, header_style, group_by=None)`. `group_by` is the header of one column
or `None`. The `Renderer` Protocol gains that one optional parameter and nothing else. `Console.table` passes
`group_by` to the renderer only when it is not `None`, so a renderer written before this change keeps working
for every call that does not group. `JsonRenderer` ignores it: the `table` event carries the same
`columns` and `rows` as before, so the desktop application's parser and its fixtures do not change.
`PlainRenderer` ignores it too and prints the flat table it always did.

| Wave | Tasks | Files | Waits on | Build the owner runs after it |
| --- | --- | --- | --- | --- |
| 7a | 19 Grouped, coloured `Table` | `sushicore/ui/table.py`, `sushicore/renderer.py`, `sushicore/console.py`, `tests/ui/test_table.py`, `tests/test_renderer_components.py`, `tests/test_console_semantics.py`, `tests/test_json_renderer.py` | Wave 6 | `python -m pytest tests -q` |
| 7b | 20 `hub doctor` uses it | `sushihub/cli/sushistack/setup/steps.py`, `sushihub/cli/tests/test_doctor_table.py` | 19 | `python -m pytest tests -q` from `sushihub/cli`, with `PYTHONPATH` set to the sushicore checkout |

### Task 19: a grouped and coloured `Table`

**Acceptance criterion:** `Table(columns, rows, title, group_by="Owner")` draws a heading per owner with the
remaining columns aligned across all groups, status words are coloured from the theme, nothing changes for a
table drawn without `group_by`, and `python -m pytest tests -q` passes.

**`Table` in `sushicore/ui/table.py`.**

- New field `group_by: str | None = None`, last, after `title`. It must name one of `columns`; anything else
  raises `ValueError` with the column names in the message.
- Without `group_by`, the table is drawn exactly as today (header row, one rule, no frame), with one
  addition: a cell whose whole text equals a status word, compared case-insensitively, is drawn in the theme
  style that word maps to. The map is a module constant, `K_STATUS_STYLES`, from word to `Theme` field name:
  `OK` to `success`; `MISSING`, `FAIL`, `FAILED` and `ERROR` to `error`; `WARN` and `WARNING` to `warn`;
  `NOT NEEDED`, `SKIPPED` and `N/A` to `muted`. Any other cell is drawn as it is today (as Rich markup).
- With `group_by`, the named column is removed from the columns. Rows are grouped by that column's value in
  order of first appearance, and each group keeps its rows in the given order. The title, when there is one,
  comes first as before, then a blank line. Each group is a heading line in `theme.header`, then its rows
  indented two spaces, then a blank line before the next group (no trailing blank line after the last). All
  groups share the same column widths: every column but the last is as wide as its widest cell across all
  groups, on one line; the last column takes what is left of the console width and wraps, and its wrapped
  lines line up under its first line. Column headers are drawn once, under the title and above the first
  group, in `theme.header` with the muted rule the flat table uses, aligned with the columns below them.
  Status cells are coloured as above. A group value that is empty is drawn as `-`.

**`Console`, `Renderer` and the three renderers.** `Console.table(columns, rows, title="", *, group_by=None)`
forwards `group_by` only when it is not `None`. The `Renderer` Protocol's `table` gains `group_by: str | None
= None`. `RichRenderer.table` builds the `Table` with it. `PlainRenderer.table` and `JsonRenderer.table` accept
it and ignore it; their output is unchanged, and a test proves the JSON event is byte-identical with and
without `group_by`.

**Tests.** `tests/ui/test_table.py`: the existing tests still pass untouched; a grouped table on a small
fixed set of rows (two groups, one long last-column text that wraps) checks the headings, the shared column
alignment across groups, the blank line between groups and none after the last, the repeated group column
being gone, the column headers appearing once, and `group_by` naming an unknown column raising `ValueError`;
status colouring is checked through `capture_ansi`: `OK` carries the success style's codes, `MISSING` the error
style's, `NOT NEEDED` the muted style's, a plain cell carries none. `tests/test_renderer_components.py`: a
grouped table through `RichRenderer`. `tests/test_console_semantics.py` and `tests/test_json_renderer.py`: the
JSON `table` event is identical with and without `group_by`, and a renderer whose `table` does not accept
`group_by` still works for an ungrouped call.

### Task 20: `hub doctor` groups its table and lists what is missing

Repository `D:/Projects/sushistack`, package `sushihub/cli`. Run every command and test with
`PYTHONPATH=D:/Projects/sushicore`; nothing is installed.

**Acceptance criterion:** `hub doctor` prints the inventory grouped by owner, then one summary line, then a
"Needs attention" list when something is missing, and every existing hub test and the `--json` event stream
for the inventory are unchanged.

**Change.** In `sushistack/setup/steps.py`, `run` passes `group_by="Owner"` to `console.table`; the columns
and rows it passes are unchanged. After the table and the existing two `console.info` lines about vendored
dependencies, it counts the rows by status text (`OK`, `MISSING`, `NOT NEEDED`, and any other status counted
under its own name) and prints one `console.info` line, `9 OK | 1 missing | 1 not needed`, with zero counts
left out. When at least one row is `MISSING` it prints `console.warn("Needs attention")`, then one
`console.info` line per missing row, `<component>  <detail>`, and last `console.info("Run `hub install` to
provision what is missing.")`. When nothing is missing it prints neither. The summary and list are computed
from the same rows the table shows, in one small function beside `inventory_rows`, so the table and the
summary cannot disagree.

**Tests** in `sushihub/cli/tests/test_doctor_table.py`: with a fake set of rows (one OK, one MISSING, one NOT
NEEDED, two owners) the human output has the two group headings, the summary line and the attention list; with
no MISSING row there is a summary and no attention list; the machine (`--json`) event for the table has the
same four columns and the same rows as before, and no `group_by` key. Follow how existing tests in
`sushihub/cli/tests/` drive the doctor step and capture console output. Do not edit `sushihub/gui/`, the
contract schemas, or any fixture; if a GUI fixture or a golden test fails, stop and report it.


### Task 21: a bracket in table data stays text

Source: Task 20's report and the owner's own `hub doctor` output. A table cell is read as Rich markup, so
`Dear ImGui (imgui[glfw-binding,opengl3-binding])` prints as `Dear ImGui (imgui)` and `hdf5[core,zlib]` as
`hdf5`: the bracket is taken for a style tag and dropped. The 0.3.0 table did the same, so this is an old
data-loss bug, not a regression. It cannot be fixed by making cells plain text, because `sushitrack` puts
markup in its cells on purpose (`[success]ok[/success]`, `[error]FAIL[/error]`, `[dim]...[/dim]`,
`[cmd]0[/cmd]`). A bracket is markup only when what it names is a style.

**Acceptance criterion:** a table cell keeps every bracket that does not name a style, a cell that does name one
is still styled, and `python -m pytest tests -q` passes.

**`sushicore/markup.py`** (new; it is not a component, so it lives beside `theme.py`):

```python
def escape_unknown_tags(text: str, known_styles: Collection[str]) -> str:
    """Return ``text`` with every bracket escaped that does not open or close a known style."""
```

A bracket is `[` then any characters but `[` and `]` then `]`. It is left as it is when the text between the
brackets is empty, or is `/` alone (Rich's close-everything tag), or, after removing one leading `/`, is in
`known_styles` or is accepted by `rich.style.Style.parse` (a parse that raises `rich.errors.StyleSyntaxError`
or `rich.errors.ColorParseError` means "not a style"). Any other bracket gets a backslash before its `[`.
A `[` already preceded by a backslash is left alone, so nothing is escaped twice. The function reads no
console and no global state.

**`Table`** in `sushicore/ui/table.py`: every cell that is not a status word goes through
`Text.from_markup(escape_unknown_tags(cell, theme.as_rich_styles()))` in both the flat and the grouped
layout, so the theme's own names (`success`, `error`, `warn`, `cmd`, `header`, `muted`) count as known. The
architecture test's allowed-import set gains `sushicore.markup`; that is the only edit to
`tests/test_ui_architecture.py`.

**Tests.** `tests/test_markup.py`: `[core,zlib]` escaped; `[red]x[/red]` and `[bold red]x[/]` untouched;
`[success]ok[/success]` untouched when `success` is in `known_styles` and escaped when it is not and is not a
Rich style; `[/]` untouched; an already escaped bracket untouched; several brackets in one string, mixed;
a string with no brackets unchanged; `[link https://example.com]x[/link]` untouched. `tests/ui/test_table.py`:
`Dear ImGui (imgui[glfw-binding,opengl3-binding])` prints whole in a flat and in a grouped table; a cell
`[error]FAIL[/error]` prints `FAIL` in the error style through `capture_ansi`; the existing tests pass untouched.


### Task 22: switch on virtual terminal processing in a Windows console

Source: the owner ran `hub` in a classic `cmd` window and in a PowerShell window and saw no logo. A classic
Windows console starts a native program with virtual terminal (VT) processing off. Rich reads that as a legacy
console, picks the 16-colour Windows renderer, and the help page's gate (256 or true colour) hides the logo.
Windows Terminal and the VS Code terminal run with VT on, which is why the logo appears there. Turning VT on
for the console before Rich looks is what `colorama.just_fix_windows_console()` does and what many tools do;
the mode belongs to the console buffer, so it stays on after the program exits, which shells cope with.

**Acceptance criterion:** on Windows, building a `RichRenderer` asks the console for VT processing on stdout
and stderr, on any other platform or when a stream is not a console nothing is touched, and
`python -m pytest tests -q` passes.

**`sushicore/windows_console.py`** (new):

```python
def enable_virtual_terminal(kernel32=None) -> bool:
    """Turn on virtual terminal processing for stdout and stderr and report whether either was turned on."""
```

It does nothing and returns `False` unless `sys.platform == "win32"`. Otherwise, for the standard output
handle (`-11`) and the standard error handle (`-12`) it calls `GetStdHandle`, then `GetConsoleMode`; when that
succeeds and bit `0x0004` (`ENABLE_VIRTUAL_TERMINAL_PROCESSING`) is not set it calls `SetConsoleMode` with the
mode or `0x0004`, and counts the handle as turned on when `SetConsoleMode` succeeds. A handle whose
`GetConsoleMode` fails (redirected to a file or a pipe) is skipped. `kernel32` is any object with those three
functions; when `None` it is `ctypes.windll.kernel32`, imported inside the function so the module imports on
every platform. Any `OSError` or `AttributeError` from the calls is caught and the result is `False`, because
this is best effort and must never stop a command. A handle that already has the bit set counts as on and is
not written.

**`RichRenderer.__init__`** in `sushicore/renderer.py` calls `enable_virtual_terminal()` before it builds the
Rich console, importing the function inside `__init__` like the file's other Rich imports, so `import
sushicore` still loads neither Rich nor `windows_console`. `PlainRenderer` and `JsonRenderer` are untouched.

**Tests** in `tests/test_windows_console.py`, with a fake `kernel32` object that records calls: both handles
turned on when `GetConsoleMode` succeeds and the bit is clear (the recorded modes are the old mode or `0x0004`);
a handle with the bit already set is not written to but counts as on; a handle whose `GetConsoleMode` fails is
skipped and gives `False` when both fail; a `SetConsoleMode` that fails counts as not turned on; an `OSError`
from the fake gives `False`; on a non-Windows `sys.platform` (monkeypatched) nothing is called and the result is
`False`. In `tests/test_renderer_components.py`: constructing a `RichRenderer` calls
`sushicore.windows_console.enable_virtual_terminal` once (monkeypatch it), and the existing subprocess test that
asserts `import sushicore` loads no Rich still passes. Do not run the real function against the real console in
any test.


### Task 23: print the help page through Rich, not through Click's `echo`

Source: a screenshot from the owner's VS Code terminal. The wordmark's `SYSTEMS` and the roll's amber came out
light grey, and the nori outline came out bright green. Typer 0.27 carries its own copy of Click under
`typer/_click/`, and that copy's `_compat.py` still wraps the output streams on Windows with
`colorama.AnsiToWin32`. `HelpGroup.format_help` wrote an ANSI string into Click's formatter, Click printed it
with `echo`, and colorama read the true-colour sequence `38;2;R;G;B` as separate parameters: the `0` of
`240;165;0` reset to the default colour and the `32` of `26;28;32` set a green foreground. Typer's own help
never shows this because it prints through Rich, straight to the console. The page now does the same.

**Acceptance criterion:** `HelpGroup` and the wrapped children print the page with the Rich console the
provider's `Console` carries, write nothing into Click's formatter, and fall back to Typer's own screen exactly
as before when building or rendering the page fails; `python -m pytest tests -q` passes.

**`sushicore/typer_help.py`.**

- `_write_page(command, ctx, formatter, console)` builds the model and the page as now, renders the page with
  `console.theme` into a renderable, and prints it with `console.console.print(renderable)`. The console decides
  width, colour system and colour setting; the `_draw` function and its `io` import go, together with anything
  else that only served it. The formatter is not written to.
- The logo gate `_logo_visible(raw)` and `_logo_for` are unchanged.
- The guard is unchanged in behaviour: an exception raised while the model or the page is built or rendered
  logs one warning and hands over to Typer's own screen. Rich renders a renderable in full before it writes
  anything, so a failure in `render` leaves no partial page; add a test that proves it with a component whose
  `render` raises after an earlier block rendered fine.
- `ctx.get_help()` now returns an empty string for a group that draws its page, because the page is printed
  while `get_help` runs. `hub`'s bare invocation calls `typer.echo(ctx.get_help())`, which prints the page and
  then one blank line; state that in the module docstring in one sentence.

**Tests** in `tests/test_typer_help.py`: the stand-ins already carry a Rich console; read the page from that
console's stream instead of from `CliRunner`'s `result.output`, and keep every existing assertion about
content, grouping, examples, the logo gate and the guard. Two additions: the page printed on the fake truecolour
terminal contains the real ANSI colour codes of the roll (`38;2;240;165;0` for amber and `38;2;26;28;32` for
nori), which the old route could not show a test; and `result.output` from `CliRunner` for a page-drawing group
does not contain the page (the formatter is untouched). `tests/help/` and `tests/ui/` are unaffected.

**Docs** (the orchestrator does them): the spec's "Help" paragraph about writing into Click's formatter, and
`docs/README.md`'s "Help screens".


### Task 24: breathing room around the logo, and headings that stand out

Source: the owner, after using `hub` in VS Code, `cmd` and PowerShell. Two requests: the logo needs some
padding above and below, and headings such as `Workspace` and `Modules` should be bold. Measured on the real
theme: a heading is already `\x1b[1;38;2;240;165;0m` (bold amber), but so is every command name under it,
because `theme.cmd` is `bold #f0a500` too, so nothing marks a heading as heavier than its rows.

**Acceptance criterion:** on a root page that shows a logo, one blank line comes before the logo and two blank
lines separate the logo from the title (the normal separator plus one); a definition list's heading stays bold
and its terms are the theme's command style without bold; `python -m pytest tests -q` passes.

**`sushicore/help/page.py`.** A module constant `K_LOGO_MARGIN = 1` names the extra blank lines. When the page
draws a logo (it is the first block), the rendered parts start with `K_LOGO_MARGIN` blank lines and the logo is
followed by `K_LOGO_MARGIN` blank lines beyond the one blank line that already separates two blocks. A page
without a logo is unchanged. The margin is the page's layout decision, not `Logo`'s, so `Logo` and
`choose_logo` do not change.

**`sushicore/ui/definition_list.py`.** The term style is the theme's command style with bold switched off
(`f"{theme.cmd} not bold"`, a Rich style string), so a term is amber and a heading, which keeps `theme.header`,
is bold amber. The heading style is unchanged. A theme whose `cmd` is not bold (`muted`) is unaffected.

**Tests.** `tests/help/test_page.py`: with a logo the output starts with one empty line and there are two empty
lines between the last logo row and the title; with no logo the first line is the title and nothing else
changed; on a leaf page (no logo) nothing changed. `tests/ui/test_definition_list.py`: through `capture_ansi`
with the default `Theme` (a Theme, not the sushiweb preset, so read `Theme().header` and `Theme().cmd` and
build the expected codes from them) the heading carries bold and the term does not; every existing text test
passes untouched. The `--help` tests in `tests/test_typer_help.py` that count lines may need their expected
line indexes updated for the blank lines around a logo: change only those, and say which.


### Task 25: make the help screen right on Typer 0.27, and stop importing `click`

Source: the first CI run on GitHub, which failed in all four jobs. CI installs the newest Typer (0.27.2). That
release carries its own copy of Click and no longer installs the `click` package, and it hands out its help
records differently from 0.20. Two defects follow, and the tests only ever ran on 0.20.

1. `sushicore/typer_help.py` imported `click` at module level (fixed by the orchestrator: the import now sits
   under `TYPE_CHECKING`, and `HelpWriter` names the classes as strings). The three test modules that
   `import click` failed to collect.
2. A real product defect, reproduced with Typer 0.27.2 and Click 8.5.0. Typer 0.20 hands the extras of a
   parameter over already escaped (`The module.  \[required]`, `Kind.  \[default: debug]`). Typer 0.27 does not
   (`The module.  [required]`, `Kind.  [default: debug]`). `DefinitionList` reads its text as Rich markup, so on
   0.27 the brackets are taken for style tags and dropped: the owner's `hub add --help` shows neither
   `[required]` nor `[default: ...]`. The same holds for a `Title` description. `Table` already keeps a bracket
   as text unless it names a style (Task 21); the list and the title never got that rule.

**Acceptance criterion:** `DefinitionList` and `Title` keep a bracket as text unless it names a style, so
`[required]` and `[default: debug]` show whether or not Typer escaped them, `[cyan]x[/cyan]` is still styled,
an already escaped `\[required]` shows `[required]` once; the whole suite passes both in the current
environment (Typer 0.20, Click 8.2.1) and in the isolated CI-like environment `ci_venv` (Typer 0.27.2, Click
8.5.0, no other change) described below.

**Change.**

- `sushicore/ui/definition_list.py`: entry text goes through `escape_unknown_tags(text, theme.as_rich_styles())`
  before `Text.from_markup`, as `Table._cell` does. `sushicore/ui/title.py`: the description likewise. Both
  already may import `sushicore.markup` (the architecture test allows it).
- The four tests that failed on 0.27 were written for 0.20's exact record format and built their contexts with
  the separate `click` package, which is the wrong `Context` class for Typer 0.27's own Click. Build the context
  the way Typer does, from the command: `command.make_context(name, [], parent=..., resilient_parsing=True)`,
  and assert what the screen shows instead of the raw record: the argument's name appears (case does not
  matter, `MODULE` on 0.20 and `module` on 0.27), the words `[required]` and `[default: a]` appear on the page,
  and no backslash sits in front of a bracket. `tests/test_typer_help.py` must not import `click` any more.
  `tests/help/test_from_click.py` and `tests/help/test_markup_safety.py` test the reader against plain Click
  commands and keep `import click`; the orchestrator adds `click` to the `test` extra.
- New tests: `DefinitionList` and `Title` on `[required]`, `[default: debug]`, `\[required]` and `[cyan]x[/cyan]`.

**Environment for the check.** `D:/Projects/sushistack`'s scratchpad holds `ci_venv`, a virtualenv with only
`rich`, `pytest`, `typer` 0.27.2 and `click` 8.5.0, made to reproduce CI. Its interpreter is
`C:/Users/sushi/AppData/Local/Temp/claude/D--Projects-sushistack/43335f2f-2bdd-481b-a169-5cc2c051201f/scratchpad/ci_venv/Scripts/python.exe`.
Run the suite with it from the repository root as `python -m pytest tests -q -p no:cacheprovider`, with
`PYTHONDONTWRITEBYTECODE=1`, and never install anything into it or into any other environment.
