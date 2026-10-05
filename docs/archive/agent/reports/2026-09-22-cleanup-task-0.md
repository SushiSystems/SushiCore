# Task 0: Reshape the sushicore writer before 0.2.0 ships

Executed against plan `docs/agent/plans/2026-09-22-cleanup-service-decomposition.md`, Task 0,
in repository `D:/Projects/sushicore`.

## What was done

- `sushicore/config_base.py`: extracted `write_toml_document(target, tables, header_lines)` as
  the brick that renders a whole document — `[tool]` and its `[tool.<platform>]` sub-tables
  first, then every other table sorted, exactly as before. `write_tool_section` keeps its
  signature and is now a thin caller: read the document, merge `updates` into `tool`, call
  `write_toml_document`. `_emit_table` is unchanged and stays the document writer's private
  helper.
- `tests/test_config_writer.py`: added `test_the_document_writer_renders_every_table_it_is_given`
  exactly as specified in the plan. The three existing tests were not touched.
- `docs/reference/CHANGELOG.md`: added one line recording the split.

## Departures from the plan

None.

## Verification

### Byte-identical output, before vs. after

A sample document with `[modules]`, `[tool]` (scalar + bool), `[tool.windows]`, and
`[workspace]` was written through `write_tool_section` with the code at `15e65d8`, then again
after the split, both times with the same `updates` and `header_lines`. Output:

```
'# header\n\n[tool]\nflag = false\ngenerator = "Ninja"\ntoolchain = "acpp"\nuse_vcpkg = true\n\n[tool.windows]\nninja_exe = "C:\tools\ninja.exe"\n\n[modules]\nsushiai = "D:/Projects/sushiai"\n\n[workspace]\nversion = "1"\n'
```

`diff before.txt after.txt` → no output, followed by `IDENTICAL`.

### Tests

```
$ python -m pytest tests -q
........................................................................ [ 74%]
.........................                                                [100%]
97 passed in 0.40s
```

96 pre-existing plus the 1 new test.

### Build and packaging

```
$ python -m build -q
...
Successfully built sushicore-0.2.0.tar.gz and sushicore-0.2.0-py3-none-any.whl

$ python -m twine check dist/*
Checking dist/sushicore-0.2.0-py3-none-any.whl: PASSED
Checking dist/sushicore-0.2.0.tar.gz: PASSED
```

`dist/` and `build/` deleted afterward.

### Git state

```
$ git status --porcelain
 M sushicore/config_base.py
 M tests/test_config_writer.py
 M docs/reference/CHANGELOG.md
?? docs/agent/reports/2026-09-22-cleanup-task-0.md
```

(captured before staging/committing; see commit below for the final state)

## What was not done

Nothing in Task 0's scope was skipped. Push and tag were not performed, per instruction — the
owner publishes 0.2.0.
