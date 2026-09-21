# Task 2 — The `Component` protocol and the architecture test

Plan: `docs/agent/plans/2026-09-21-terminal-components.md`, Task 2.
Spec: `docs/agent/specs/2026-09-21-terminal-components-design.md`, "Component layer".

## Files written

| File | State |
| --- | --- |
| `sushicore/ui/__init__.py` | Created; the docstring only, as the plan gives it. |
| `sushicore/ui/component.py` | Created; the `Component` Protocol, as the plan gives it. |
| `tests/ui/__init__.py` | Created, empty. |
| `tests/ui/capture.py` | Created; `capture` and `capture_ansi`, with two determinism fixes (below). |
| `tests/ui/test_component.py` | Created. |
| `tests/test_ui_architecture.py` | Created, with three fixes (below). |
| `docs/agent/reports/2026-09-21-terminal-components-task-2.md` | This report. |

Nothing else was touched. `sushicore/theme.py`, `sushicore/console.py`, `tests/test_theme_muted.py`,
`sushicore/brand.py` and `tests/test_brand.py` belong to Tasks 1 and 3 and were only read, not edited.
No commit, no change to `pyproject.toml`, `README.md`, `docs/README.md` or `docs/reference/CHANGELOG.md`.

## What I changed in the plan's test code, and why

### 1. `capture` inherited Windows' legacy console (real defect, would have broken Task 5)

Rich decides `legacy_windows` by sniffing the host console. On this machine it comes out `True`
even when the output is a `StringIO`, and Rich then swaps the rounded box characters for square
ones:

```
$ python -X utf8 -c "... Console(file=io.StringIO(), width=30, color_system=None, legacy_windows=lw) ... c.print(Panel('body', title='t'))"
panel legacy True  '┌──────────── t ─────────────┐\n│ body                       │\n└────────────────────────────┘\n'
panel legacy False '╭──────────── t ─────────────╮\n│ body                       │\n╰────────────────────────────╯\n'
```

Task 5's `test_panel_puts_the_title_on_the_top_border_and_the_body_inside` asserts
`lines[0].startswith("╭")`, so with the plan's `capture` that test fails here and passes on Linux.
Both consoles in `capture.py` now pass `legacy_windows=False`.

### 2. `capture_ansi` obeyed `NO_COLOR`

Rich reads the `NO_COLOR` environment variable when `no_color` is left unset, so the golden-file
test in Task 4 would produce different bytes for a developer who exports it. Both consoles now pass
`no_color=False`. The plain `capture` does not need it, but the two functions keep the same shape.

### 3. `_imported_modules` could slice a tuple negatively

The plan computes `K_PACKAGE[: len(K_PACKAGE) - (node.level - 1)]`. At level 4 that is
`K_PACKAGE[:-1]`, which resolves `from ....theme import x` to the allowed `sushicore.theme`. I split
the resolution into `_absolute_name` and clamp the depth, so anything above the package root
resolves to a bare name and fails the allow-check.

### 4. Names and line width

`UI` and `FILES` became `K_UI` and `K_FILES` (`python-code-style`: module constants are
`K_UPPER_SNAKE`), and the list comprehension in the one-public-class test was 106 columns, so it is
wrapped. `K_PACKAGE` is a tuple rather than a list.

Also read, kept: the plan's `Console(file=..., width=...)` construction, the trailing-space strip,
and every assertion.

## What the architecture test does not check

Global Constraints require a component to be `@final` and `@dataclass(frozen=True, slots=True)`.
The test checks `frozen`; it checks neither `@final` nor `slots`. The spec's "Tests" section lists
only the three rules the test enforces, so I left the rule set as the plan approves it. Widening it
is an interface decision for the orchestrator.

## Commands and output

### Step 2 — the failing run

```
$ python -m pytest tests/ui/test_component.py tests/test_ui_architecture.py -v
============================= test session starts =============================
platform win32 -- Python 3.13.13, pytest-9.1.1, pluggy-1.6.0 -- C:\ProgramData\Miniconda\python.exe
cachedir: .pytest_cache
rootdir: D:\Projects\sushicore
configfile: pyproject.toml
plugins: anyio-4.12.1
collecting ... collected 4 items / 1 error

=================================== ERRORS ====================================
_________________ ERROR collecting tests/ui/test_component.py _________________
ImportError while importing test module 'D:\Projects\sushicore\tests\ui\test_component.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\ProgramData\Miniconda\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\ui\test_component.py:6: in <module>
    from sushicore.ui.component import Component
E   ModuleNotFoundError: No module named 'sushicore.ui'
=========================== short test summary info ===========================
ERROR tests/ui/test_component.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
============================== 1 error in 0.15s ===============================
```

### Step 4 — the passing run

```
$ python -m pytest tests/ui/test_component.py tests/test_ui_architecture.py -v
============================= test session starts =============================
platform win32 -- Python 3.13.13, pytest-9.1.1, pluggy-1.6.0 -- C:\ProgramData\Miniconda\python.exe
cachedir: .pytest_cache
rootdir: D:\Projects\sushicore
configfile: pyproject.toml
plugins: anyio-4.12.1
collecting ... collected 6 items

tests/ui/test_component.py::test_a_class_with_render_satisfies_the_protocol PASSED [ 16%]
tests/ui/test_component.py::test_a_class_without_render_does_not PASSED  [ 33%]
tests/test_ui_architecture.py::test_the_protocol_file_declares_render PASSED [ 50%]
tests/test_ui_architecture.py::test_file_defines_one_public_class_named_after_the_file[NOTSET] SKIPPED [ 66%]
tests/test_ui_architecture.py::test_component_is_a_frozen_dataclass_with_render[NOTSET] SKIPPED [ 83%]
tests/test_ui_architecture.py::test_file_imports_only_what_a_component_may[NOTSET] SKIPPED [100%]

======================== 3 passed, 3 skipped in 0.06s =========================
```

The three parametrised tests collect no case, so pytest reports them once each as skipped. The plan's
"3 passed" is the passing count.

### The probe — does the guard bite?

First probe, exactly as dispatched: `sushicore/ui/_probe.py` importing `sushicore.help` and defining
two public classes. `sushicore.help` does not exist until Task 7, so three of the four cases fail,
but only one of them on its own assertion:

```
$ python -m pytest tests/test_ui_architecture.py -v
>   import sushicore.help
E   ModuleNotFoundError: No module named 'sushicore.help'

sushicore\ui\_probe.py:7: ModuleNotFoundError
___________ test_file_imports_only_what_a_component_may[_probe.py] ____________
>           assert allowed, f"{path.name} imports {name}"
E           AssertionError: _probe.py imports sushicore.help
E           assert False

tests\test_ui_architecture.py:80: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_ui_architecture.py::test_file_defines_one_public_class_named_after_the_file[_probe.py]
FAILED tests/test_ui_architecture.py::test_component_is_a_frozen_dataclass_with_render[_probe.py]
FAILED tests/test_ui_architecture.py::test_file_imports_only_what_a_component_may[_probe.py]
========================= 3 failed, 1 passed in 0.10s =========================
```

The import error hides the class-count rule, so I ran a second probe that imports a module which
exists and is still forbidden, `from ..icons import IconSet`, with an unfrozen dataclass and a second
public class. Each rule then fails on its own assertion:

```
$ python -m pytest tests/test_ui_architecture.py -v
E           [
E               'Probe',
E         +     'Extra',
E           ]

tests\test_ui_architecture.py:58: AssertionError
_________ test_component_is_a_frozen_dataclass_with_render[_probe.py] _________
>       assert component.__dataclass_params__.frozen
E       AssertionError: assert False
E        +  where False = _DataclassParams(init=True,repr=True,eq=True,order=False,unsafe_hash=False,frozen=False,match_args=True,kw_only=False,slots=True,weakref_slot=False).frozen
E        +    where _DataclassParams(...) = <class 'sushicore.ui._probe.Probe'>.__dataclass_params__
___________ test_file_imports_only_what_a_component_may[_probe.py] ____________
>           assert allowed, f"{path.name} imports {name}"
E           AssertionError: _probe.py imports sushicore.icons
E           assert False

tests\test_ui_architecture.py:80: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_ui_architecture.py::test_file_defines_one_public_class_named_after_the_file[_probe.py]
FAILED tests/test_ui_architecture.py::test_component_is_a_frozen_dataclass_with_render[_probe.py]
FAILED tests/test_ui_architecture.py::test_file_imports_only_what_a_component_may[_probe.py]
========================= 3 failed, 1 passed in 0.09s =========================
```

The second probe also shows `_absolute_name` resolving `..icons` to `sushicore.icons` correctly.

### The probe is gone

```
$ rm -f sushicore/ui/_probe.py && rm -rf sushicore/ui/__pycache__ && ls -la sushicore/ui/
total 6
drwxr-xr-x 1 sushi 197121   0 Sep 21 21:52 .
drwxr-xr-x 1 sushi 197121   0 Sep 21 21:52 ..
-rw-r--r-- 1 sushi 197121  74 Sep 21 21:52 __init__.py
-rw-r--r-- 1 sushi 197121 472 Sep 21 21:52 component.py
```

### Syntax check

```
$ python -m py_compile sushicore/ui/__init__.py sushicore/ui/component.py tests/ui/__init__.py tests/ui/capture.py tests/ui/test_component.py tests/test_ui_architecture.py && echo "py_compile: exit 0, no output"
py_compile: exit 0, no output
```

### Line width

```
$ awk 'length>100 {print FILENAME": "FNR": "length}' sushicore/ui/__init__.py sushicore/ui/component.py tests/ui/capture.py tests/ui/test_component.py tests/test_ui_architecture.py
over-100 lines listed above (none if blank)
```

### The whole suite

```
$ python -m pytest tests -q
........................................................................ [ 56%]
..................................................sss..                  [100%]
124 passed, 3 skipped in 0.65s
```

Tasks 1 and 3 had already landed when I ran this: 110 baseline + 4 (Task 1) + 7 (Task 3) + 3 (mine)
= 124. Nothing from another worker fails.

## Not done

- The `@final` and `slots=True` constraints are unguarded; see above.
- `capture` and `capture_ansi` have no test of their own. They are test scaffolding, and Tasks 4, 5
  and 6 exercise them. The plan asks for none.
- Rich is 15.0.0 here, not the 13.x the plan's tech stack names. Every rule the components rely on
  held in the probes above, but nothing pins the version.

## Orchestrator note

The gap described under "Gap I did not close" was closed after this report was written: `tests/test_ui_architecture.py` now also checks `slots` and `@final` for every component file.
