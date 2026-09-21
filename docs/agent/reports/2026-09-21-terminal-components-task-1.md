# Terminal components, Task 1: the `muted` token and `Console.theme`

## Files changed

- `sushicore/theme.py`: added the field `muted: str = "dim"` after `rule_line`, and `"muted": self.muted` in `as_rich_styles`.
- `sushicore/console.py`: added the read-only property `Console.theme`, beside `accent`.
- `tests/test_theme_muted.py`: new, the four tests from the plan.

## Commands

Step 2, before the implementation (`python -m pytest tests/test_theme_muted.py -v`), tail of the output:

```
E       AttributeError: 'Theme' object has no attribute 'muted'
E       TypeError: Theme.__init__() got an unexpected keyword argument 'muted'
E       AttributeError: 'Theme' object has no attribute 'muted'
E       TypeError: Theme.__init__() got an unexpected keyword argument 'muted'
FAILED tests/test_theme_muted.py::test_muted_defaults_to_dim - AttributeError...
FAILED tests/test_theme_muted.py::test_muted_reaches_the_rich_style_map - Typ...
FAILED tests/test_theme_muted.py::test_muted_is_overridable_like_every_other_token
FAILED tests/test_theme_muted.py::test_console_exposes_the_theme_it_was_built_with
============================== 4 failed in 0.10s ==============================
```

The fourth failure comes from `Theme(muted=...)` in the test's setup, not from the missing `Console.theme`. It still fails for the reason the task describes: the token does not exist yet.

Step 4, after the implementation:

```
$ python -m pytest tests/test_theme_muted.py -q
....                                                                     [100%]
4 passed in 0.02s
$ python -m pytest tests -q
........................................................................ [ 63%]
..........................................                               [100%]
114 passed in 0.50s
```

Syntax check:

```
$ python -m py_compile sushicore/theme.py sushicore/console.py tests/test_theme_muted.py
COMPILE_OK
```

## Decisions

- The plan's field comment spans two `#` lines. `source-comments` forbids two in a row, so the field carries one line: `# "dim" quiets text without fixing a colour for an unknown terminal background.` The existing multi-line `#` block above `rule_line` is untouched.
- The `_THEME_PRESETS` entries were not changed; they inherit `muted="dim"` from the default.

## Not done

- No commit, no changelog line, no edits to `pyproject.toml`, `README.md` or `docs/README.md`, as instructed.
- No other checker was run (`tools/documentation/check_source_comments.py` was not looked for or run).
