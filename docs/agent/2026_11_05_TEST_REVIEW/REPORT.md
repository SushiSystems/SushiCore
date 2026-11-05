# Test review: report

**Status:** Open — every test has a verdict; the plan's jobs are next

Every test in the repository has a verdict from `skills/testing/REVIEWING.md` of SushiSkills, reviewed
on 2026-11-05 as part of J15 (`docs/agent/2026_11_03_INDUSTRIAL_TESTING/` in SushiSkills). The review read
the code and ran nothing. Each record names the files it read. The tests of the shared checkers under
`tools/` are reviewed once, in SushiSkills; this report covers this repository's own tests and its own
checkers' tests.

## What the review found

sushicore matters beyond itself: it holds the shared test command, and the CLI tests of sushilog,
sushiprofiler, sushitrack, sushidsp and sushistack stub the same functions this repository's tests do.
The in-memory adapters it lacks are the ones every other repository's CLI tests need.

- **Stand-ins for its own ports.** No in-memory adapter exists for `proc.Runner`, the console,
  `ConfigModule`, `MachineEnvironment`, `ToolkitLocator`, `IDependencySource`, the git client or the
  file store. Tests write `_Recorder`, `recording_console` (copied into `tests/provision/conftest.py` and
  three toolchain files), `FakeGit`, `_OfflineGit`, `_FakeAptManager`, `sushi_fakes.py`, fake rigs,
  locks, inspectors and runners. `test_cmake_driver.py` alone has 31 such cases.
- **Logic reached through files.** The backlog and design logic runs only through the file store, and
  `test_home.py`, `test_closure.py` and 30 producer tests decide on values through real files.
- **Loops and conditionals around assertions**, which become rows.
- **Process-wide reaches from small tests:** `date.today`, `SUSHIRUNTIME_DIR`, module globals, the
  process random module, and an autouse fixture that takes `tmp_path` for every small test.
- `pyproject.toml` markers and `tests/conftest.py` `K_SIZE_TIMEOUTS` set 60 s, 300 s and 900 s; the skill
  sets 1 s, 10 s and 120 s. Every repository's test command inherits these.

The review of chunk 005 deleted both `TimingPolicy` contract tests as copies of the concrete suites. That
is wrong under the doctrine: the contract suite stays and the concrete copies merge into it. The plan
reverses those two records, and the delete of `test_producer.py::test_read_head_commit_reports_a_folder_that_is_no_checkout`,
the only test that crosses the real git boundary.

## Defects the review found

- `winget.is_installed` matches by substring: "Git.G" reads as installed.
- `read_toolchain_stamp` calls `read_text()` with no encoding; the invalid-UTF-8 test passes on Windows
  only through the JSON error.
- The Typer fallback fails on a stray close tag: a test asserts that `MarkupError` escapes.
- `tests/backlog/test_importer.py::_git` ignores exit codes.
- `test_toml_writer` holds invalid escapes such as `"D:\Projects"`.
- `test_a_bracket_after_an_even_run_of_backslashes_is_not_escaped`: the name and the body disagree.
- `stamp_check`, `path_check` and `fragment_check` have only their failing side tested; the
  reader-failure warning of `print_budget` has none.
- `PlainRenderer.prompt` reads `input()` with no stream seam, where `JsonRenderer` has one.
- `tools/testing/check_test_additions.py` and its test are a leftover: SushiSkills removed the checker in
  phase B, and the copier never removes a file upstream dropped. Both are deleted.
- `tools/tests/test_test_budget_settings.py` skips here, since the repository has no `skills/` folder, so
  its promise is checked nowhere; it also defines `read_budget` and `differences` in the test file.

## The owner's decisions waiting

1. The size timeouts of the shared test command: align them with the skill. Recommended: yes, since
   every repository inherits them.
2. A file-system port for the backlog and design store, and a seam that takes the logo grids and palette
   as values.
3. The Typer stray-close-tag behaviour: a defect to fix, or the documented fallback.

## Dispatches

dispatch: J15 review, 12 chunks — haiku high, 1 round each, passed, rung 1

## Totals

| Tests | Keep | Rewrite | Resize | Split | Merge | Delete | Characterize | Add |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1457 | 425 | 577 | 186 | 82 | 90 | 97 | 0 | 90 |

Kept as they stand: 425 of 1457 (29%).

## Verdicts by question

| Verdict | Question | What it means | Tests |
| --- | --- | --- | --- |
| rewrite | 1 | a forbidden kind | 518 |
| resize | 8 | wrong size | 186 |
| merge | 4 | a duplicate | 90 |
| split | 3 | no single promise | 82 |
| delete | 1 | a forbidden kind | 72 |
| rewrite | 7 | a long-test sign | 23 |
| rewrite | 5 | tied to the inside | 19 |
| delete | 4 | a duplicate | 16 |
| rewrite | 8 | wrong size | 12 |
| delete | 3 | no single promise | 6 |
| delete | 2 | cannot fail | 3 |
| rewrite | 6 | oracle is the code | 3 |

## Modules

| Module | Files | Tests | Keep | Rewrite | Resize | Split | Merge | Delete | Characterize |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `provision` | 40 | 322 | 75 | 154 | 62 | 10 | 8 | 13 | 0 |
| `(root)` | 38 | 336 | 113 | 133 | 33 | 17 | 19 | 21 | 0 |
| `provision/gpu` | 26 | 136 | 21 | 76 | 6 | 0 | 12 | 21 | 0 |
| `provision/sushi_packages` | 25 | 126 | 33 | 58 | 17 | 3 | 3 | 12 | 0 |
| `docs_bundle` | 13 | 71 | 15 | 11 | 30 | 6 | 6 | 3 | 0 |
| `provision/toolchains` | 4 | 52 | 6 | 38 | 0 | 0 | 6 | 2 | 0 |
| `backlog` | 9 | 60 | 21 | 9 | 10 | 19 | 0 | 1 | 0 |
| `ui` | 8 | 79 | 41 | 13 | 0 | 3 | 13 | 9 | 0 |
| `provision/test_steps` | 4 | 34 | 0 | 32 | 0 | 0 | 2 | 0 | 0 |
| `design` | 7 | 28 | 4 | 7 | 2 | 14 | 0 | 1 | 0 |
| `test_renderer` | 3 | 38 | 14 | 13 | 0 | 0 | 10 | 1 | 0 |
| `provision/test_fragments` | 3 | 18 | 0 | 16 | 0 | 0 | 0 | 2 | 0 |
| `testing` | 6 | 26 | 8 | 0 | 9 | 7 | 0 | 2 | 0 |
| `provision/test_download_verifier` | 2 | 23 | 6 | 13 | 3 | 0 | 0 | 1 | 0 |
| `tools` | 3 | 16 | 0 | 1 | 8 | 2 | 0 | 5 | 0 |
| `help` | 5 | 44 | 32 | 0 | 0 | 1 | 10 | 1 | 0 |
| `test_deps_fragment` | 2 | 30 | 20 | 3 | 6 | 0 | 0 | 1 | 0 |
| `test_workspace` | 3 | 18 | 16 | 0 | 0 | 0 | 1 | 1 | 0 |

## Records

One line per test: `file::test | verdict | question | reason | files read`.

### `tests/backlog/test_check.py`

```
test_a_store_the_tool_wrote_is_clean | rewrite | 7 | backlog.check #1: the name says every command leaves the store clean, the body covers add work and add issue only, name and body differ | tests/backlog/test_check.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/check.py; source/sushicore/backlog/editor.py
test_a_repository_without_a_store_is_clean_unless_it_holds_the_retired_files | keep | 9 | backlog.check #2, boundary: file presence on disk | tests/backlog/test_check.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/check.py; source/sushicore/backlog/store.py
test_a_hand_edit_that_changes_the_shape_is_a_fault | keep | 9 | backlog.check #3, boundary: bytes on disk against render_area | tests/backlog/test_check.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/check.py; source/sushicore/backlog/store.py
test_a_duplicate_id_and_an_id_past_the_counter_are_faults | split | 3 | two promises joined by and: backlog.check #4 duplicate ID and #4b ID at or past the counter or closed | tests/backlog/test_check.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/check.py; source/sushicore/backlog/store.py
test_a_missing_source_and_a_reference_to_no_entry_are_faults | split | 3 | two promises joined by and: backlog.check #5 missing Source path (medium, file boundary) and #6 reference to no open entry, which the body never makes fail, so #6 has no test (see Adds) | tests/backlog/test_check.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/check.py; source/sushicore/backlog/model.py
test_a_blocked_entry_whose_blocks_closed_must_be_opened | resize | 8 | backlog.check #7, logic on values reached only through the file store. Seam: rule_blocked_ready reads check.located and the IDs only, so a BacklogCheck built from Located values reaches it with no file; BacklogCheck.load is the file read | tests/backlog/test_check.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/check.py; source/sushicore/backlog/order.py; source/sushicore/backlog/store.py
test_a_pin_on_a_closed_entry_is_a_fault | resize | 8 | backlog.check #8, rule_pins reads check.config and check.work only. Seam: BacklogCheck built from values, the test writes backlog.toml through the store | tests/backlog/test_check.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/check.py; source/sushicore/backlog/store.py
test_a_stale_index_and_an_orphan_detail_are_faults | split | 3 | two promises joined by and: backlog.check #9 stale index and #9b detail whose entry is closed, both file-level | tests/backlog/test_check.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/check.py; source/sushicore/backlog/store.py
test_an_open_design_no_entry_cites_is_a_fault | resize | 8 | backlog.check #10, rule_design_coverage reads the injected open_designs and check.work. The topic file the test writes is never read. Seam: BacklogCheck built from values | tests/backlog/test_check.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/check.py
test_a_file_the_store_does_not_know_is_a_fault | keep | 9 | backlog.check #11, boundary: listing of docs/backlog | tests/backlog/test_check.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/check.py; source/sushicore/backlog/store.py
```

### `tests/backlog/test_commands.py`

```
test_an_agent_adds_work_and_reads_it_back_as_json | rewrite | 1 | backlog.commands #1. Spy: _invoke passes reported.append as the report sink, a recorder for a sink the repository owns. Rewrite needs an in-memory report sink beside the report parameter of register_backlog_commands. Three actions in one test | tests/backlog/test_commands.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/commands.py
test_list_filters_by_priority_range_and_kind | rewrite | 1 | backlog.commands #2. Spy: reported.append as the report sink. Rewrite needs the in-memory report sink named for test_an_agent_adds_work_and_reads_it_back_as_json | tests/backlog/test_commands.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/commands.py
test_close_prints_the_changelog_line_and_check_stays_clean | rewrite | 1 | backlog.commands #3. Spy: reported.append as the report sink. The check-stays-clean half repeats tests/backlog/test_check.py::test_a_store_the_tool_wrote_is_clean and is dropped in the rewrite | tests/backlog/test_commands.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/commands.py
test_check_exits_one_on_a_finding | rewrite | 1 | backlog.commands #4. Spy: reported.append as the report sink. The file and line output is not checked elsewhere, so this is the test that keeps the promise, and tests/backlog/test_main.py::test_main_returns_the_check_code is deleted as its duplicate | tests/backlog/test_commands.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/commands.py
test_a_refused_change_reaches_the_caller_as_the_backlog_error | rewrite | 1 | backlog.commands #5. Spy: the fixture _invoke writes the recorder. The docstring says the entry point prints the error, but the body shows the group re-raises it and the printing is tested in test_main, so the docstring is wrong | tests/backlog/test_commands.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/commands.py; source/sushicore/backlog/errors.py
```

### `tests/backlog/test_editor.py`

```
test_add_takes_the_next_id_and_blocked_by_makes_the_entry_blocked | split | 3 | two promises joined by and: backlog.editor #1 next ID per kind and #2 Blocked by at add makes the entry blocked | tests/backlog/test_editor.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/editor.py; source/sushicore/backlog/store.py; source/sushicore/backlog/model.py
test_add_refuses_a_broken_value_and_an_unknown_area_without_writing | rewrite | 7 | backlog.editor #3, one promise with two refusal causes joined by and, so rows: a broken title and an unknown area | tests/backlog/test_editor.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/editor.py; source/sushicore/backlog/store.py
test_add_puts_a_bare_source_in_backticks | resize | 8 | backlog.editor #4. The only door is add_work, which writes through the store. _source is private. Seam: an in-memory BacklogStore port beside store.py | tests/backlog/test_editor.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/editor.py; source/sushicore/backlog/store.py
test_promote_writes_the_new_work_into_the_issue_fix | resize | 8 | backlog.editor #5. Seam: in-memory BacklogStore port, promote reads and writes through store.find and store.read_area | tests/backlog/test_editor.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/editor.py; source/sushicore/backlog/store.py
test_set_changes_one_column_and_refuses_a_broken_value | split | 3 | two promises joined by and: backlog.editor #6 changes one column and #7 refuses a broken value | tests/backlog/test_editor.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/editor.py; source/sushicore/backlog/model.py
test_set_state_away_from_blocked_lets_go_of_the_blocker | resize | 8 | backlog.editor #8. Seam: in-memory BacklogStore port, set_value reads and writes through the store | tests/backlog/test_editor.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/editor.py; source/sushicore/backlog/store.py
test_close_refuses_a_cited_entry_and_records_the_id | split | 3 | two promises joined by and: backlog.editor #9 refuses a cited entry and #10 records the ID and returns the changelog line | tests/backlog/test_editor.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/editor.py; source/sushicore/backlog/store.py
test_close_deletes_the_detail_and_the_pin | split | 3 | two effects joined by and: backlog.editor #11 detail file deleted (file effect, medium) and #12 pin removed, which can break apart | tests/backlog/test_editor.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/editor.py; source/sushicore/backlog/store.py
test_pins_refuse_a_decision_and_keep_a_place | split | 3 | two promises joined by and: backlog.editor #13 refuses a decision and #13b keeps the place of a pin at a position | tests/backlog/test_editor.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/editor.py; source/sushicore/backlog/store.py
test_move_and_merge_areas | split | 3 | two operations joined by and: backlog.editor #14 move and #15 merge_areas | tests/backlog/test_editor.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/editor.py; source/sushicore/backlog/store.py
test_add_area_refuses_a_name_out_of_shape_and_a_taken_one | split | 3 | two promises joined by and: backlog.editor #16 refusals as rows (out of shape, taken) and #17 returns the areas sorted | tests/backlog/test_editor.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/editor.py; source/sushicore/backlog/store.py
```

### `tests/backlog/test_errors.py`

```
test_every_backlog_error_reaches_the_entry_point_as_a_sushicore_error | keep | 9 | backlog.errors #1, parametrised over three classes, one line. The oracle is the hierarchy the entry point relies on | tests/backlog/test_errors.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/errors.py; source/sushicore/errors.py
```

### `tests/backlog/test_importer.py`

```
test_area_key_drops_small_words | resize | 8 | backlog.importer #1, pure function area_key on values, so it is small, not medium. Door: area_key in source/sushicore/backlog/importer.py | tests/backlog/test_importer.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/importer.py
test_import_writes_a_clean_store_and_deletes_the_retired_files | split | 3 | several promises in one test: backlog.importer #2 rows and pins, #3 detail prose and links, #4 citations and deleted files, #5 ledger and clean check | tests/backlog/test_importer.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/importer.py; source/sushicore/backlog/store.py; source/sushicore/backlog/model.py; source/sushicore/backlog/check.py
test_import_runs_once | keep | 9 | backlog.importer #6, boundary: store folder existence on disk | tests/backlog/test_importer.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/importer.py; source/sushicore/backlog/store.py
test_renumber_keeps_the_target_branch_entry_and_moves_the_other | keep | 9 | backlog.importer #7, boundary: real git subprocess on a temporary repository, medium. Note for the owner: the _git helper uses check=False and never reads the return code, so a failed git step surfaces as a wrong assertion rather than a named failure | tests/backlog/test_importer.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/importer.py
```

### `tests/backlog/test_main.py`

```
test_main_runs_a_command_on_the_root_it_is_given | keep | 9 | backlog.main #1, boundary: console output on the given root | tests/backlog/test_main.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/__main__.py; source/sushicore/backlog/commands.py
test_main_prints_a_backlog_error_as_one_line | keep | 9 | backlog.main #2, boundary: stderr line and exit code | tests/backlog/test_main.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/__main__.py; source/sushicore/backlog/errors.py
test_main_returns_the_check_code | delete | 4 | backlog.main #3 is checked by tests/backlog/test_commands.py::test_check_exits_one_on_a_finding, which checks the same exit code and also the file and line, and that test is kept by its rewrite | tests/backlog/test_main.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/__main__.py; tests/backlog/test_commands.py
```

### `tests/backlog/test_model.py`

```
test_row_round_trip_keeps_a_pipe_inside_a_cell | keep | 9 | backlog.model #1 | tests/backlog/test_model.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/model.py
test_from_cells_rejects_a_row_with_a_cell_missing | keep | 9 | backlog.model #2 | tests/backlog/test_model.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/model.py
test_from_cells_rejects_a_date_that_is_not_iso | keep | 9 | backlog.model #3 | tests/backlog/test_model.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/model.py
test_valid_work_has_no_problem | keep | 9 | backlog.model #4 | tests/backlog/test_model.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/model.py
test_work_problems_name_the_broken_value | keep | 9 | backlog.model #5, parametrised over nine rows, one line | tests/backlog/test_model.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/model.py
test_blocked_by_a_sibling_and_an_external_reason_is_valid | split | 3 | two promises joined by and: backlog.model #6 sibling reference and #6b external reason, which can break apart | tests/backlog/test_model.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/model.py
test_with_value_refuses_the_id | keep | 9 | backlog.model #7 | tests/backlog/test_model.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/model.py
test_own_issue_needs_a_fix | keep | 9 | backlog.model #8, a boundary pair of one rule: empty fix refused, named fix accepted | tests/backlog/test_model.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/model.py
test_issue_of_the_toolchain_needs_no_fix | keep | 9 | backlog.model #9 | tests/backlog/test_model.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/model.py
test_scheduled_fix_without_workaround_is_work_alone | keep | 9 | backlog.model #10 | tests/backlog/test_model.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/model.py
test_sibling_origin_names_its_issue_and_is_cited | split | 3 | two promises joined by and: backlog.model #11 names and is cited, and #11b the refused origin | tests/backlog/test_model.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/model.py
```

### `tests/backlog/test_order.py`

```
test_an_entry_is_late_past_its_priority_limit | keep | 9 | backlog.order #1, parametrised over five rows, one line | tests/backlog/test_order.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/order.py
test_next_orders_by_priority_then_age_then_id | keep | 9 | backlog.order #2 | tests/backlog/test_order.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/order.py; source/sushicore/backlog/model.py
test_pins_come_first_in_their_order | keep | 9 | backlog.order #3 | tests/backlog/test_order.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/order.py
test_decisions_and_open_blocks_are_never_returned | split | 3 | two promises joined by and: backlog.order #4 decision not returned and #5 open block holds pinned work, which can break apart | tests/backlog/test_order.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/order.py
test_a_block_on_a_closed_entry_releases_the_work | keep | 9 | backlog.order #6. Not a duplicate of tests/backlog/test_check.py::test_a_blocked_entry_whose_blocks_closed_must_be_opened, which checks the fault, not the release | tests/backlog/test_order.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/order.py; tests/backlog/test_check.py
test_external_and_sibling_blocks_hold_the_work | rewrite | 7 | backlog.order #7, one promise over two inputs joined by and, a sign: rewrite as rows over the Blocked by values | tests/backlog/test_order.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/order.py; source/sushicore/backlog/model.py
test_count_cuts_the_list_and_decisions_lists_the_owners | split | 3 | two functions joined by and: backlog.order #8 count and #8b decisions | tests/backlog/test_order.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/order.py
```

### `tests/backlog/test_store.py`

```
test_an_area_file_round_trips_through_the_shape_the_tool_writes | resize | 8 | backlog.store #1. The round trip is on values: render_area and parse_area take an AreaFile and text, so the editor and the files are setup only. Small with AreaFile values | tests/backlog/test_store.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/store.py; source/sushicore/backlog/editor.py
test_a_row_out_of_shape_is_a_fault_and_the_store_refuses_to_read_it | split | 3 | two promises joined by and: backlog.store #2 parse_area reports the fault (small) and #2b read_area refuses it (medium) | tests/backlog/test_store.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/store.py
test_merge_conflict_markers_are_dropped_when_tolerated | resize | 8 | backlog.store #3. parse_area with tolerate_conflicts takes text, so the editor and the file are setup only. Small | tests/backlog/test_store.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/store.py
test_ledger_takes_numbers_in_order_and_remembers_closed_ones | split | 3 | two promises joined by and: backlog.store #4 take and close on IdLedger (small) and #4b round trip through ids.toml (medium) | tests/backlog/test_store.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/store.py
test_ranges_compress_and_expand | split | 3 | two functions joined by and: backlog.store #5 format_ranges and #5b parse_ranges, both small | tests/backlog/test_store.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/store.py
test_config_without_areas_is_an_error | resize | 8 | backlog.store #6. config reads the file and checks inside the same method, so no value door exists. Seam: move the areas check into a function that takes the parsed table | tests/backlog/test_store.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/store.py
test_index_counts_each_area | rewrite | 6 | backlog.store #7. The oracle includes index equal to store.render_index, which is the code under test. Keep the explicit row as the oracle and drop the equality | tests/backlog/test_store.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/store.py; source/sushicore/backlog/editor.py
test_find_names_the_area_and_raises_for_an_unknown_id | split | 3 | two outcomes joined by and: backlog.store #8 returns the area and #8b raises, asserting the base BacklogError rather than EntryNotFoundError | tests/backlog/test_store.py; tests/backlog/conftest.py; tests/conftest.py; source/sushicore/backlog/store.py
```

### `tests/design/test_check.py`

```
test_a_topic_the_tool_wrote_is_clean | delete | 4 | design.check #1 is checked by tests/design/test_commands.py::test_phase_commands_and_check, which asserts clean after new and a phase, and that test is kept by its rewrite | tests/design/test_check.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/check.py; source/sushicore/design/store.py; tests/design/test_commands.py
test_a_module_two_topics_name_is_a_finding | resize | 8 | design.check #2. Logic on owners read from topic files, through store.owners. Seam: a DesignStore port, or owners taken as values | tests/design/test_check.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/check.py; source/sushicore/design/store.py
test_a_missing_modules_line_and_a_missing_module_are_findings | split | 3 | two promises joined by and: design.check #3a missing Modules line and #3b module not in the repository | tests/design/test_check.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/check.py; source/sushicore/design/model.py
test_none_needs_an_about_line | resize | 8 | design.check #4. rule_modules_required reads topic.document only, so a DesignCheck built from parse_topic values reaches it. Small | tests/design/test_check.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/check.py; source/sushicore/design/model.py
test_sections_phases_hashes_and_dated_work_are_findings | split | 3 | four promises in one test: design.check #5 sections, #6 phase state, #7a commit hash, #7b dated record | tests/design/test_check.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/check.py; source/sushicore/design/model.py
test_a_loose_document_and_a_work_folder_naming_no_phase_are_findings | split | 3 | two promises joined by and: design.check #8 loose document and #9 work folder naming no phase or topic | tests/design/test_check.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/check.py; source/sushicore/design/store.py
```

### `tests/design/test_commands.py`

```
test_new_then_list_and_owner | rewrite | 1 | design.commands #1. Spy: _invoke passes reported.append as the report sink. Rewrite needs an in-memory report sink beside the report parameter of register_design_commands. Three actions in one test | tests/design/test_commands.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/commands.py
test_new_refuses_an_owned_module | rewrite | 1 | design.commands #2. Spy: reported.append as the report sink, same in-memory sink as above | tests/design/test_commands.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/commands.py; source/sushicore/design/store.py
test_phase_commands_and_check | rewrite | 1 | design.commands #3. Spy: reported.append as the report sink. Wall clock: line 63 reads datetime.date.today and the CLI store builds DesignStore with the real clock, so the test depends on the wall clock, a determinism defect. Seam: register_design_commands takes a clock as DesignStore does. Several promises, to be split in the rewrite | tests/design/test_commands.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/commands.py; source/sushicore/design/store.py
```

### `tests/design/test_errors.py`

```
test_every_design_error_reaches_the_entry_point_as_a_sushicore_error | keep | 9 | design.errors #1, parametrised over two classes, one line | tests/design/test_errors.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/errors.py; source/sushicore/errors.py
```

### `tests/design/test_main.py`

```
test_main_opens_a_topic_and_checks_it | split | 3 | two actions joined by and: design.main #1a new returns 0 and #1b check after it is clean | tests/design/test_main.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/__main__.py; source/sushicore/design/commands.py
test_main_prints_a_design_error_as_one_line | keep | 9 | design.main #2, boundary: stderr line and exit code | tests/design/test_main.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/__main__.py; source/sushicore/design/errors.py
```

### `tests/design/test_merge.py`

```
test_overlap_lists_shared_and_nested_modules_and_shared_words | split | 3 | three kinds joined by and: design.merge #1a shared modules, #1b nested, #1c shared words. The body asserts shared is empty, so the shared kind the name claims is not tested here | tests/design/test_merge.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/merge.py; source/sushicore/design/store.py
test_merge_makes_a_page_joins_phases_and_modules_and_rewrites_citations | split | 3 | several promises in one test: design.merge #2a page, #2b phases, #2c modules, #2d citations, #2e clean check | tests/design/test_merge.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/merge.py; source/sushicore/design/store.py; source/sushicore/design/model.py; source/sushicore/design/check.py
test_merge_refuses_itself_and_a_page_that_exists | rewrite | 7 | design.merge #3, one promise with two refusal causes joined by and, a sign: rewrite as rows | tests/design/test_merge.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/merge.py
test_merge_renames_a_page_whose_name_is_taken | keep | 9 | design.merge #4, boundary: file moves and renames on disk | tests/design/test_merge.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/merge.py; source/sushicore/design/store.py
```

### `tests/design/test_model.py`

```
test_parse_reads_the_status_the_metadata_the_sections_and_the_phases | split | 3 | four reads joined by and: design.model #1 title, status and metadata, #2 sections and fence, #3 phase rows | tests/design/test_model.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/model.py
test_modules_none_is_an_empty_list_and_a_missing_line_is_none | split | 3 | two outcomes joined by and: design.model #4 none gives an empty list and #4b a missing line gives None | tests/design/test_model.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/model.py
test_render_writes_the_five_sections_and_the_modules | split | 3 | two outputs joined by and: design.model #5 five sections and #5b Modules line | tests/design/test_model.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/model.py
test_replace_phases_keeps_the_generated_block_and_the_prose | rewrite | 2 | design.model #6. The prose is not asserted anywhere in the body, so a loss of prose would not fail it and its promise has no other test. Rewrite with a prose assertion | tests/design/test_model.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/model.py
test_replace_phases_fills_a_section_that_said_none | keep | 9 | design.model #7 | tests/design/test_model.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/model.py
test_replace_status_and_field | split | 3 | two operations joined by and: design.model #8 replace_status and #8b replace_field | tests/design/test_model.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/model.py
```

### `tests/design/test_store.py`

```
test_new_topic_owns_its_modules_and_refuses_a_second_owner | split | 3 | three promises in one test: design.store #1a owner and no owner, #1b second owner refused, #1c containing module refused | tests/design/test_store.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/store.py; source/sushicore/design/model.py
test_new_refuses_a_bad_name_a_taken_name_a_missing_module_and_no_about | rewrite | 7 | design.store #2. The body loops over four tuples, a sign: rewrite as rows | tests/design/test_store.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/store.py
test_deepest_named_module_owns_a_path | rewrite | 7 | design.store #3. The tmp_path fixture is named and not used, a sign: remove it. The owner lookup reads topic files, so a seam is needed later under question 8 | tests/design/test_store.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/store.py
test_page_and_phase_and_shipping | split | 3 | three promises in one test: design.store #4 page, #4b phase, #4c shipping | tests/design/test_store.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/store.py
test_open_documents_leave_out_topics_under_revision | split | 3 | two promises: design.store #5 open_documents leaves out revision topics and #5b topic_paths includes them | tests/design/test_store.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/store.py
test_a_topic_under_revision_owns_no_module | split | 3 | two promises: design.store #6a a revision topic owns no module and #6b a live topic may take that module | tests/design/test_store.py; tests/design/conftest.py; tests/conftest.py; source/sushicore/design/store.py
```

### `tests/docs_bundle/test_api_reference.py`

```
test_stage_builds_then_copies_what_the_index_names | rewrite | 1 | forbidden kind: a recorder lambda stands in for ApiSource.build, a source the repository owns; this is the only test of the multi-file copy, so the rewrite needs an in-memory ApiSource build adapter in api_reference.py | tests/docs_bundle/test_api_reference.py; source/sushicore/docs_bundle/api_reference.py; tests/docs_bundle/test_producer.py
test_stage_refuses_a_repository_with_no_api_source | resize | 8 | the decision is on None and stage_api raises before it touches a file, so small sees the promise with no seam; the tmp_path it asks for is never read | tests/docs_bundle/test_api_reference.py; source/sushicore/docs_bundle/api_reference.py
test_stage_reports_a_failed_build | resize | 8 | the decision is on the returned exit code, which stage_api checks before it reads the XML folder, so the XML written by _xml_dir is not needed and small sees it; "3" in the message is a weak oracle, assert the full message | tests/docs_bundle/test_api_reference.py; source/sushicore/docs_bundle/api_reference.py
test_stage_reports_a_build_that_wrote_no_xml | resize | 8 | the decision is index.is_file(), a file probe, so the seam is a file probe injected into stage_api, then small | tests/docs_bundle/test_api_reference.py; source/sushicore/docs_bundle/api_reference.py
test_stage_reports_an_index_that_names_a_missing_file | resize | 8 | the decision reads the index and probes the files it names; the seam is an index reader and a file probe injected into stage_api | tests/docs_bundle/test_api_reference.py; source/sushicore/docs_bundle/api_reference.py
test_stage_reports_an_index_that_is_not_xml | resize | 8 | the decision is the XML parse of the index; the seam is the index text handed in, then small | tests/docs_bundle/test_api_reference.py; source/sushicore/docs_bundle/api_reference.py
```

### `tests/docs_bundle/test_bundle_archive.py`

```
test_write_packs_every_file_under_its_posix_name | split | 3 | two promises: (a) each staged file is stored under its POSIX name, sorted, with no folder entries and its staged bytes; (b) every member has mtime 0, owner 0, group 0 and mode 0644 | tests/docs_bundle/test_bundle_archive.py; source/sushicore/docs_bundle/bundle_archive.py
test_write_returns_the_digest_and_writes_it_beside_the_archive | split | 3 | two results that can break apart: (a) the returned value is the SHA-256 of the archive; (b) the .sha256 file holds the digest line | tests/docs_bundle/test_bundle_archive.py; source/sushicore/docs_bundle/bundle_archive.py
test_write_is_reproducible | rewrite | 1 | forbidden kind: a for loop in the body (os.utime over rglob) builds the input; a builder with an mtime argument replaces it; no other test checks that mtimes do not change the bytes | tests/docs_bundle/test_bundle_archive.py; source/sushicore/docs_bundle/bundle_archive.py; tests/docs_bundle/test_producer.py
```

### `tests/docs_bundle/test_bundle_manifest.py`

```
test_build_matches_the_golden_document | resize | 8 | build_manifest already takes values; the file reads come from the sample repository used only to build its inputs, so construct PublishList and PageSet values and run small with no fixture | tests/docs_bundle/test_bundle_manifest.py; source/sushicore/docs_bundle/bundle_manifest.py; source/sushicore/docs_bundle/publish_list.py; source/sushicore/docs_bundle/page_set.py; tests/docs_bundle/sample_repository.py
test_build_names_the_api_root_when_the_bundle_carries_one | resize | 8 | same cause as the golden test: the promise is a value of build_manifest, so construct the inputs and run small | tests/docs_bundle/test_bundle_manifest.py; source/sushicore/docs_bundle/bundle_manifest.py
```

### `tests/docs_bundle/test_commands.py`

```
test_bare_docs_builds_the_api_and_returns_its_code | rewrite | 1 | forbidden kind: a recorder lambda stands in for ApiSource.build, a source the repository owns; the rewrite needs an in-memory ApiSource build adapter in api_reference.py | tests/docs_bundle/test_commands.py; source/sushicore/docs_bundle/commands.py; source/sushicore/docs_bundle/api_reference.py
test_the_group_works_where_click_is_not_installed | rewrite | 1 | forbidden kind: an ApiSource stand-in built by the test; the sys.modules patch is process-wide state, and the no-click promise is carried by the group, so the in-memory ApiSource adapter replaces the stand-in | tests/docs_bundle/test_commands.py; source/sushicore/docs_bundle/commands.py; source/sushicore/docs_bundle/api_reference.py
test_bare_docs_shows_help_when_the_cli_builds_no_api | resize | 8 | the help path reads no file; the repository fixture writes files the command never reads, so small sees the promise with a plain Path | tests/docs_bundle/test_commands.py; source/sushicore/docs_bundle/commands.py
test_bundle_writes_the_archive_and_reports_it | split | 3 | two results that can break apart: (a) the archive lands at build/docs/bundle/docs-bundle-<release>.tar.gz; (b) the two report lines, whose digest is checked only for its length | tests/docs_bundle/test_commands.py; source/sushicore/docs_bundle/commands.py; source/sushicore/docs_bundle/producer.py
test_bundle_writes_where_out_says | keep | 9 | promise: docs bundle --out writes the archive into the folder named; the observable is the file, so medium is the boundary size | tests/docs_bundle/test_commands.py; source/sushicore/docs_bundle/commands.py
test_bundle_requires_a_release | resize | 8 | the usage error comes from argument parsing before any file is read; small with a plain Path and no repository fixture | tests/docs_bundle/test_commands.py; source/sushicore/docs_bundle/commands.py
test_bundle_lets_a_bundle_error_reach_the_entry_point | resize | 8 | the missing publish.toml is probed by read_publish_list inside BundleProducer; the seam is a publish-list reader injected into BundleProducer beside read_commit, then small | tests/docs_bundle/test_commands.py; source/sushicore/docs_bundle/commands.py; source/sushicore/docs_bundle/producer.py; source/sushicore/docs_bundle/publish_list.py
test_the_catalogue_holds_docs_only_when_it_runs_bare | rewrite | 1 | forbidden kind: an ApiSource stand-in built by the test; the rewrite needs the in-memory ApiSource adapter in api_reference.py | tests/docs_bundle/test_commands.py; source/sushicore/docs_bundle/commands.py; source/sushicore/describe.py; source/sushicore/docs_bundle/api_reference.py
```

### `tests/docs_bundle/test_errors.py`

```
test_every_bundle_error_is_a_sushicore_error | keep | 9 | promise: every bundle error is a DocsBundleError and a SushiCoreError, so entry.run prints it; PageError is missing from the parametrised list, see Adds | tests/docs_bundle/test_errors.py; source/sushicore/docs_bundle/errors.py; source/sushicore/errors.py
test_a_page_error_puts_its_location_in_front | keep | 9 | promise: PageError message is path:line: message, with path and line kept | tests/docs_bundle/test_errors.py; source/sushicore/docs_bundle/errors.py
```

### `tests/docs_bundle/test_main.py`

```
test_main_writes_the_archive_and_prints_it | split | 3 | two results that can break apart: (a) the bundle of --root is written at --out; (b) the path and sha256 lines are printed | tests/docs_bundle/test_main.py; source/sushicore/docs_bundle/__main__.py; source/sushicore/docs_bundle/producer.py
test_main_reports_a_failure_as_one_line_and_exit_one | resize | 8 | the refusal happens on the release value before any file is read, so small sees the promise with a plain Path; the repository fixture is not needed | tests/docs_bundle/test_main.py; source/sushicore/docs_bundle/__main__.py; source/sushicore/docs_bundle/producer.py
```

### `tests/docs_bundle/test_markdown_scan.py`

```
test_iter_links_reports_each_target_with_its_line | keep | 9 | promise row: iter_links yields each inline link and image target with its line | tests/docs_bundle/test_markdown_scan.py; source/sushicore/docs_bundle/markdown_scan.py
test_iter_links_reads_titled_and_bracketed_targets | merge | 4 | same promise as test_iter_links_reads_a_bracketed_target_that_holds_a_space with other inputs; merge into one table of target forms | tests/docs_bundle/test_markdown_scan.py; source/sushicore/docs_bundle/markdown_scan.py
test_iter_links_skips_code | keep | 9 | promise row: iter_links skips links inside fenced blocks and code spans | tests/docs_bundle/test_markdown_scan.py; source/sushicore/docs_bundle/markdown_scan.py
test_first_heading_returns_the_first_level_one_heading | split | 3 | two promises: (a) the first level-one heading outside code is returned; (b) None when only deeper headings exist | tests/docs_bundle/test_markdown_scan.py; source/sushicore/docs_bundle/markdown_scan.py
test_local_path_drops_the_fragment_and_refuses_addresses | split | 3 | two promises: (a) the decoded file part without fragment or query is returned; (b) None for addresses, anchors and protocol-relative targets | tests/docs_bundle/test_markdown_scan.py; source/sushicore/docs_bundle/markdown_scan.py
test_iter_links_reads_a_bracketed_target_that_holds_a_space | merge | 4 | same promise as test_iter_links_reads_titled_and_bracketed_targets with other inputs; merge into one table of target forms | tests/docs_bundle/test_markdown_scan.py; source/sushicore/docs_bundle/markdown_scan.py
test_iter_links_reads_both_targets_of_a_linked_image | keep | 9 | promise row: iter_links yields the image and the page a linked image points to | tests/docs_bundle/test_markdown_scan.py; source/sushicore/docs_bundle/markdown_scan.py
test_iter_links_reads_a_link_whose_text_wraps | keep | 9 | promise row: iter_links finds a wrapped link on the line that holds its target | tests/docs_bundle/test_markdown_scan.py; source/sushicore/docs_bundle/markdown_scan.py
test_a_fence_closes_only_on_its_own_marker | keep | 9 | promise row: a fence closes only on the marker that opened it | tests/docs_bundle/test_markdown_scan.py; source/sushicore/docs_bundle/markdown_scan.py
```

### `tests/docs_bundle/test_page_order.py`

```
test_read_numbers_the_pages_in_link_order | resize | 8 | the promise is the link walk, a decision on page text values; the page reads go through read_page_text from files, so the seam is a page-text reader injected into read_page_order, then small | tests/docs_bundle/test_page_order.py; source/sushicore/docs_bundle/page_order.py; source/sushicore/docs_bundle/page_text.py; tests/docs_bundle/sample_repository.py
test_read_keeps_the_first_position_of_a_repeated_page | resize | 8 | the promise is the link walk's de-duplication on values; seam: page-text reader injected into read_page_order, then small | tests/docs_bundle/test_page_order.py; source/sushicore/docs_bundle/page_order.py; source/sushicore/docs_bundle/page_text.py
test_read_skips_what_is_not_a_page_below_docs | resize | 8 | the promise is the filter on link targets, a decision on values; seam: page-text reader injected, then small | tests/docs_bundle/test_page_order.py; source/sushicore/docs_bundle/page_order.py; source/sushicore/docs_bundle/markdown_scan.py
test_read_reports_a_missing_index | resize | 8 | the decision is index.is_file(), a file probe; seam: file probe injected into read_page_order, then small | tests/docs_bundle/test_page_order.py; source/sushicore/docs_bundle/page_order.py
test_read_follows_links_through_the_pages_of_the_manual | resize | 8 | the promise is the breadth-first walk on values; seam: page-text reader injected, then small | tests/docs_bundle/test_page_order.py; source/sushicore/docs_bundle/page_order.py; source/sushicore/docs_bundle/page_text.py
test_read_follows_links_through_a_document_outside_the_manual | resize | 8 | the promise is the walk through a document outside the sections, a decision on values; seam: page-text reader injected, then small | tests/docs_bundle/test_page_order.py; source/sushicore/docs_bundle/page_order.py
test_read_does_not_follow_links_out_of_a_record | resize | 8 | the promise is the record-folder rule on values; seam: page-text reader injected, then small | tests/docs_bundle/test_page_order.py; source/sushicore/docs_bundle/page_order.py
```

### `tests/docs_bundle/test_page_set.py`

```
test_collect_returns_the_pages_in_section_then_index_order | resize | 8 | the promise is the sort and the PageSet value on values; the file system is the seam to build (a listing and text reader injected into PageCollector), then small | tests/docs_bundle/test_page_set.py; source/sushicore/docs_bundle/page_set.py; source/sushicore/docs_bundle/page_order.py; source/sushicore/docs_bundle/page_text.py
test_collect_leaves_out_an_excluded_page | resize | 8 | the promise is the exclusion on values; file-system seam as above, then small | tests/docs_bundle/test_page_set.py; source/sushicore/docs_bundle/page_set.py
test_collect_refuses_an_exclusion_that_names_no_file | merge | 4 | same promise as test_collect_refuses_an_exclusion_spelt_in_another_case with other inputs; merge into one table of exclusion names | tests/docs_bundle/test_page_set.py; source/sushicore/docs_bundle/page_set.py
test_collect_refuses_an_exclusion_spelt_in_another_case | merge | 4 | same promise as test_collect_refuses_an_exclusion_that_names_no_file with other inputs; merge into one table of exclusion names | tests/docs_bundle/test_page_set.py; source/sushicore/docs_bundle/page_set.py
test_collect_accepts_a_link_that_leaves_the_bundle | delete | 1 | forbidden kind: control flow in the body (all() over a generator); its promise is already asserted exactly by test_collect_returns_the_pages_in_section_then_index_order, which pins the page and asset lists | tests/docs_bundle/test_page_set.py; tests/docs_bundle/test_page_set.py
test_collect_reports_a_link_to_a_missing_file | resize | 8 | the decision is the existence probe of the link target; file-system seam, then small | tests/docs_bundle/test_page_set.py; source/sushicore/docs_bundle/page_set.py
test_collect_reports_a_link_that_cannot_be_resolved | resize | 8 | the refusal of absolute and outside paths is decided on values, but collect reads the files first; file-system seam, then small | tests/docs_bundle/test_page_set.py; source/sushicore/docs_bundle/page_set.py
test_collect_reports_a_page_without_a_title | resize | 8 | the decision is first_heading on page text; file-system seam, then small | tests/docs_bundle/test_page_set.py; source/sushicore/docs_bundle/page_set.py; source/sushicore/docs_bundle/markdown_scan.py
test_collect_reports_a_page_the_index_does_not_link | resize | 8 | the decision is membership in the order map; file-system seam, then small | tests/docs_bundle/test_page_set.py; source/sushicore/docs_bundle/page_set.py; source/sushicore/docs_bundle/page_order.py
test_collect_refuses_a_list_that_publishes_nothing | resize | 8 | the decision is an empty source list after the listing; file-system seam, then small | tests/docs_bundle/test_page_set.py; source/sushicore/docs_bundle/page_set.py
test_collect_refuses_a_link_written_with_backslashes | resize | 8 | the refusal is a check on the link string before any file probe; file-system seam is still needed by collect, then small | tests/docs_bundle/test_page_set.py; source/sushicore/docs_bundle/page_set.py; source/sushicore/docs_bundle/markdown_scan.py
test_collect_never_carries_an_excluded_page_as_an_asset | rewrite | 1 | forbidden kind: control flow in the body (all() over a generator for the page check); the promise (an excluded .MD page is not an asset) is not tested elsewhere, so the rewrite states it as one exact assertion | tests/docs_bundle/test_page_set.py; source/sushicore/docs_bundle/page_set.py; source/sushicore/docs_bundle/page_text.py
test_collect_reports_a_page_that_is_not_utf_8 | delete | 4 | the same promise, a non-UTF-8 page is refused with its path, is asserted in tests/docs_bundle/test_page_text.py::test_read_reports_a_page_that_is_not_utf_8; collect only propagates read_page_text's PageError | tests/docs_bundle/test_page_set.py; tests/docs_bundle/test_page_text.py; source/sushicore/docs_bundle/page_text.py; source/sushicore/docs_bundle/page_set.py
```

### `tests/docs_bundle/test_page_text.py`

```
test_read_drops_a_byte_order_mark | keep | 9 | promise row: the byte order mark is dropped; the encoding of the file's bytes is the boundary under test, so the file is the right reach | tests/docs_bundle/test_page_text.py; source/sushicore/docs_bundle/page_text.py; source/sushicore/docs_bundle/markdown_scan.py
test_read_reports_a_page_that_is_not_utf_8 | keep | 9 | promise row: a page whose bytes are not UTF-8 is reported with its file; the decode of the file's bytes is the boundary under test | tests/docs_bundle/test_page_text.py; source/sushicore/docs_bundle/page_text.py
```

### `tests/docs_bundle/test_producer.py`

```
test_produce_writes_the_pages_the_assets_and_the_manifest | rewrite | 1 | forbidden kind: the _produce helper's lambda stands in for read_commit, a commit source the repository owns; the rewrite needs an in-memory commit reader in source_revision.py; the test also holds three promises (see split note in the reason of the rewrite) | tests/docs_bundle/test_producer.py; source/sushicore/docs_bundle/producer.py; source/sushicore/docs_bundle/source_revision.py; source/sushicore/docs_bundle/bundle_manifest.py
test_produce_is_reproducible_and_replaces_an_earlier_staging | rewrite | 1 | forbidden kind: the _produce helper's read_commit stand-in; the rewrite needs the in-memory commit reader in source_revision.py; the name holds two promises, reproducibility and stale staging | tests/docs_bundle/test_producer.py; source/sushicore/docs_bundle/producer.py; source/sushicore/docs_bundle/source_revision.py
test_produce_refuses_a_release_that_is_not_three_integers | rewrite | 1 | forbidden kind: the _produce helper's read_commit stand-in; the promise is decided before any file, so the rewrite also moves the five rows to small with the in-memory commit reader | tests/docs_bundle/test_producer.py; source/sushicore/docs_bundle/producer.py; source/sushicore/docs_bundle/source_revision.py
test_produce_carries_the_api_when_the_list_asks_for_it | rewrite | 1 | forbidden kind: the read_commit stand-in and an ApiSource stand-in; the packing of api/xml is tested nowhere else, so the rewrite needs the in-memory commit reader and the in-memory ApiSource adapter | tests/docs_bundle/test_producer.py; source/sushicore/docs_bundle/producer.py; source/sushicore/docs_bundle/api_reference.py; source/sushicore/docs_bundle/source_revision.py
test_produce_stops_when_the_list_asks_for_an_api_nobody_builds | rewrite | 1 | forbidden kind: the read_commit stand-in in _produce; the rewrite needs the in-memory commit reader in source_revision.py | tests/docs_bundle/test_producer.py; source/sushicore/docs_bundle/producer.py; source/sushicore/docs_bundle/source_revision.py
test_read_head_commit_returns_the_checked_out_hash | keep | 9 | promise row: read_head_commit returns the full hash of HEAD in a real checkout; the real git is the boundary under test | tests/docs_bundle/test_producer.py; tests/docs_bundle/sample_repository.py; source/sushicore/docs_bundle/source_revision.py
test_read_head_commit_reports_a_folder_that_is_no_checkout | delete | 4 | the same promise, a folder that is not a checkout is a ReleaseError, is asserted at small size with git stubbed in tests/docs_bundle/test_source_revision.py::test_a_folder_that_is_not_a_checkout_is_a_release_error; the real-git boundary is then covered by no other test, which the owner may overturn | tests/docs_bundle/test_producer.py; tests/docs_bundle/test_source_revision.py; source/sushicore/docs_bundle/source_revision.py
```

### `tests/docs_bundle/test_publish_list.py`

```
test_read_returns_every_field | resize | 8 | the promise is the whole PublishList value on values; the file read is incidental, and the seam is a parsed-document entry point beside read_toml, then small | tests/docs_bundle/test_publish_list.py; source/sushicore/docs_bundle/publish_list.py; source/sushicore/workspace.py
test_read_applies_the_defaults | merge | 4 | same promise as test_read_takes_exclude_and_api, defaults against set values; merge into one table of exclude and api | tests/docs_bundle/test_publish_list.py; source/sushicore/docs_bundle/publish_list.py
test_read_takes_exclude_and_api | merge | 4 | same promise as test_read_applies_the_defaults with other inputs; merge into one table of exclude and api | tests/docs_bundle/test_publish_list.py; source/sushicore/docs_bundle/publish_list.py
test_read_reports_a_missing_file | resize | 8 | the decision is path.is_file(), a file probe; seam: file probe injected, then small | tests/docs_bundle/test_publish_list.py; source/sushicore/docs_bundle/publish_list.py
test_read_refuses_a_section_that_cannot_be_published | resize | 8 | the refusal is a check on values in the sections list; seam: parsed document, then small | tests/docs_bundle/test_publish_list.py; source/sushicore/docs_bundle/publish_list.py
test_read_refuses_a_wrong_value | resize | 8 | the refusals are checks on values; seam: parsed document, then small; the oracle is weak, it checks only the exception type and not the key named | tests/docs_bundle/test_publish_list.py; source/sushicore/docs_bundle/publish_list.py
test_read_reports_malformed_toml_as_a_config_error | keep | 9 | promise row: malformed TOML reaches the caller as the shared ConfigError; the TOML file is the boundary under test, and a parsed-document seam would skip the path it checks | tests/docs_bundle/test_publish_list.py; source/sushicore/docs_bundle/publish_list.py; source/sushicore/workspace.py
```

### `tests/docs_bundle/test_source_revision.py`

```
test_returns_the_head_commit | keep | 9 | promise row: read_head_commit returns the stripped stdout; git is out of process and not owned by the repository, so the stand-in of subprocess.run is the allowed mock of the adapter | tests/docs_bundle/test_source_revision.py; source/sushicore/docs_bundle/source_revision.py
test_a_folder_that_is_not_a_checkout_is_a_release_error | keep | 9 | promise row: a non-zero git exit is a ReleaseError carrying git's stderr; its real-git twin is deleted in test_producer.py | tests/docs_bundle/test_source_revision.py; source/sushicore/docs_bundle/source_revision.py
test_a_missing_git_is_a_release_error | keep | 9 | promise row: a git that cannot be run is a ReleaseError | tests/docs_bundle/test_source_revision.py; source/sushicore/docs_bundle/source_revision.py
```

### `tests/help/test_from_click.py`

```
test_commands_are_grouped_by_panel_in_order_of_first_appearance | keep | 9 | promise row: commands are grouped by panel in first-appearance order and hidden commands are left out | tests/help/test_from_click.py; source/sushicore/help/from_click.py; source/sushicore/help/model.py
test_a_plain_click_group_lists_commands_alphabetically_so_panels_follow_that_order | merge | 4 | same promise as test_commands_are_grouped_by_panel_in_order_of_first_appearance with a plain Click group whose order is alphabetical; merge into that test as a row | tests/help/test_from_click.py; source/sushicore/help/from_click.py
test_a_command_with_no_panel_falls_into_commands | keep | 9 | promise row: a command with no panel falls into Commands | tests/help/test_from_click.py; source/sushicore/help/from_click.py
test_a_placeholder_panel_is_not_a_heading | keep | 9 | promise row: a placeholder panel is not a heading | tests/help/test_from_click.py; source/sushicore/help/from_click.py
test_hidden_commands_are_left_out | keep | 9 | promise row: hidden commands are left out | tests/help/test_from_click.py; source/sushicore/help/from_click.py
test_options_come_from_the_help_records | keep | 9 | promise row: options come from Click's help records, with --help included | tests/help/test_from_click.py; source/sushicore/help/from_click.py
test_an_argument_without_a_record_falls_back_to_its_metavar | keep | 9 | promise row: an argument with no record falls back to its metavar | tests/help/test_from_click.py; source/sushicore/help/from_click.py
test_usage_and_name_use_the_command_path | keep | 9 | promise row: usage and name use the command path | tests/help/test_from_click.py; source/sushicore/help/from_click.py
test_only_the_top_command_is_the_root | keep | 9 | promise row: only the top command is the root | tests/help/test_from_click.py; source/sushicore/help/from_click.py
test_a_leaf_has_no_command_sections | keep | 9 | promise row: a leaf has no command sections | tests/help/test_from_click.py; source/sushicore/help/from_click.py
test_examples_split_the_command_from_its_note_and_skip_blank_lines | keep | 9 | promise row: examples split at " # " and skip blank lines | tests/help/test_from_click.py; source/sushicore/help/from_click.py
test_the_description_joins_wrapped_lines_and_stops_at_a_form_feed | keep | 9 | promise row: the description joins wrapped lines and stops at a form feed | tests/help/test_from_click.py; source/sushicore/help/from_click.py
test_a_typer_app_groups_by_its_panels | keep | 9 | promise row: a Typer app is grouped by its panels | tests/help/test_from_click.py; source/sushicore/help/from_click.py
test_a_typer_leaf_keeps_the_help_records_typer_hands_out | split | 3 | two promises: (a) the argument and option records Typer hands out are kept; (b) the usage line begins with the command path and names the argument; the _unescaped helper makes the oracle accept escaped and plain text, so it does not pin what the page shows | tests/help/test_from_click.py; source/sushicore/help/from_click.py
test_a_plain_click_option_has_its_default_marker_escaped | keep | 9 | promise row: plain Click default markers are escaped in the model | tests/help/test_from_click.py; source/sushicore/help/from_click.py
test_a_plain_click_description_has_its_brackets_escaped | keep | 9 | promise row: plain Click description brackets are escaped in the model | tests/help/test_from_click.py; source/sushicore/help/from_click.py
test_a_plain_click_argument_help_and_sub_command_help_are_escaped | keep | 9 | promise row: plain Click help text is escaped in argument and sub-command entries; one promise, plain text escaped in help records | tests/help/test_from_click.py; source/sushicore/help/from_click.py
test_terms_and_examples_are_never_escaped | keep | 9 | promise row: terms and examples are not escaped | tests/help/test_from_click.py; source/sushicore/help/from_click.py
test_a_rich_mode_command_keeps_its_markup_in_the_description_and_parameters | keep | 9 | promise row: a rich-mode command keeps its markup in description and parameters | tests/help/test_from_click.py; source/sushicore/help/from_click.py
test_each_command_is_read_in_its_own_markup_mode | keep | 9 | promise row: each command is read in its own markup mode | tests/help/test_from_click.py; source/sushicore/help/from_click.py
```

### `tests/help/test_logo_choice.py`

```
test_a_console_as_wide_as_the_lockup_gets_the_mark_and_the_wordmark | merge | 4 | same promise as test_one_column_short_of_the_lockup_drops_the_wordmark, the two sides of one width boundary; merge into one boundary table. The oracle reads Logo.width, a dependency whose width is its own unit's promise | tests/help/test_logo_choice.py; source/sushicore/help/logo_choice.py; source/sushicore/ui/logo.py
test_one_column_short_of_the_lockup_drops_the_wordmark | merge | 4 | same boundary as test_a_console_as_wide_as_the_lockup_gets_the_mark_and_the_wordmark; merge into one boundary table | tests/help/test_logo_choice.py; source/sushicore/help/logo_choice.py; source/sushicore/ui/logo.py
test_a_console_as_wide_as_the_mark_gets_the_mark_alone | merge | 4 | same boundary as test_one_column_short_of_the_mark_gets_nothing; merge into one boundary table | tests/help/test_logo_choice.py; source/sushicore/help/logo_choice.py; source/sushicore/ui/logo.py
test_one_column_short_of_the_mark_gets_nothing | merge | 4 | same boundary as test_a_console_as_wide_as_the_mark_gets_the_mark_alone; merge into one boundary table | tests/help/test_logo_choice.py; source/sushicore/help/logo_choice.py; source/sushicore/ui/logo.py
test_the_glow_follows_the_background | keep | 9 | promise row: the glow of the chosen logo follows the background; no other test checks it | tests/help/test_logo_choice.py; source/sushicore/help/logo_choice.py; source/sushicore/ui/logo.py
test_a_console_of_no_width_gets_nothing | merge | 4 | same promise as test_one_column_short_of_the_mark_gets_nothing with a zero width; merge into that boundary table | tests/help/test_logo_choice.py; source/sushicore/help/logo_choice.py
```

### `tests/help/test_model.py`

```
test_a_help_model_is_frozen | delete | 1 | forbidden kind: a test of trivial code; it checks the frozen flag of a dataclass and a stored field, with no promise a defect could break | tests/help/test_model.py; source/sushicore/help/model.py
```

### `tests/help/test_page/test_markup_safety.py`

```
test_a_plain_click_option_shows_its_default_marker | keep | 9 | promise row: plain Click default markers print as written in the rendered page; the rendered page can fail where the model test passes (markup errors at render time), so it is not the same defect as from_click's model test | tests/help/test_page/test_markup_safety.py; tests/help/test_from_click.py; source/sushicore/help/from_click.py; source/sushicore/help/page.py; tests/ui/capture.py
test_a_description_with_a_closing_tag_renders_and_prints_it | keep | 9 | promise row: a stray closing tag in a description renders and prints as written, a render-time failure the model test cannot see | tests/help/test_page/test_markup_safety.py; source/sushicore/help/from_click.py; source/sushicore/help/page.py; tests/ui/capture.py
test_a_sub_command_short_help_with_a_bracket_prints_as_written | keep | 9 | promise row: sub-command short help with a bracket prints as written | tests/help/test_page/test_markup_safety.py; source/sushicore/help/from_click.py; source/sushicore/help/page.py; tests/ui/capture.py
test_a_typer_app_in_rich_mode_renders_its_markup_without_the_tags | keep | 9 | promise row: Typer rich-mode markup renders without its tags | tests/help/test_page/test_markup_safety.py; source/sushicore/help/from_click.py; source/sushicore/help/page.py; tests/ui/capture.py
test_a_typer_app_in_rich_mode_shows_its_required_and_default_extras_without_a_backslash | keep | 9 | promise row: Typer rich-mode extras print without a backslash | tests/help/test_page/test_markup_safety.py; source/sushicore/help/from_click.py; source/sushicore/help/page.py; tests/ui/capture.py
test_a_typer_app_with_no_mode_set_shows_its_extras_without_a_backslash | merge | 4 | same promise as test_a_typer_app_in_rich_mode_shows_its_required_and_default_extras_without_a_backslash with no markup mode; merge into that test as a row | tests/help/test_page/test_markup_safety.py; source/sushicore/help/from_click.py
```

### `tests/help/test_page/test_page.py`

```
test_a_leaf_page_lists_its_sections_in_order | keep | 9 | promise row: a leaf page draws its title, usage, arguments, options and examples in that order | tests/help/test_page/test_page.py; source/sushicore/help/page.py; source/sushicore/help/model.py; tests/ui/capture.py
test_a_root_page_lists_each_command_group_before_the_options | keep | 9 | promise row: a root page draws each command group before the options | tests/help/test_page/test_page.py; source/sushicore/help/page.py; tests/ui/capture.py
test_empty_sections_are_left_out | keep | 9 | promise row: empty sections are left out | tests/help/test_page/test_page.py; source/sushicore/help/page.py; tests/ui/capture.py
test_a_root_page_draws_the_logo_it_is_given | merge | 4 | same promise as test_a_page_without_a_logo_draws_none, the two sides of logo drawing; merge into one table of logo given or not | tests/help/test_page/test_page.py; source/sushicore/help/page.py; tests/ui/capture.py
test_the_logo_comes_before_the_title | keep | 9 | promise row: the logo comes before the title on a root page | tests/help/test_page/test_page.py; source/sushicore/help/page.py; tests/ui/capture.py
test_a_page_without_a_logo_draws_none | merge | 4 | same promise as test_a_root_page_draws_the_logo_it_is_given; merge into one table | tests/help/test_page/test_page.py; source/sushicore/help/page.py; tests/ui/capture.py
test_the_logo_never_shows_on_a_sub_command_page | keep | 9 | promise row: a sub-command page never draws the logo | tests/help/test_page/test_page.py; source/sushicore/help/page.py; tests/ui/capture.py
test_the_logo_has_one_blank_line_above_it | keep | 9 | promise row: the logo has one blank line above it on a root page | tests/help/test_page/test_page.py; source/sushicore/help/page.py; tests/ui/capture.py
test_two_blank_lines_separate_the_logo_from_the_title | keep | 9 | promise row: two blank lines separate the logo from the title | tests/help/test_page/test_page.py; source/sushicore/help/page.py; tests/ui/capture.py
test_a_root_page_without_a_logo_starts_at_its_title | merge | 4 | same promise as test_the_logo_has_one_blank_line_above_it, the layout with and without a logo; merge into one table | tests/help/test_page/test_page.py; source/sushicore/help/page.py; tests/ui/capture.py
test_a_leaf_page_given_a_logo_still_starts_at_its_title | keep | 9 | promise row: a leaf page given a logo still starts at its title | tests/help/test_page/test_page.py; source/sushicore/help/page.py; tests/ui/capture.py
```

### `tests/provision/gpu/test_adapter_builder.py`

```
test_a_full_build_records_the_expected_argv_and_installs_binaries | rewrite | 1 | Test-local _FakeRunner stands in for the repo-owned CommandRunner protocol and writes fake build output; no in-memory CommandRunner exists beside the protocol in adapter_builder.py; rewrite needs that adapter, one promise per test | tests/provision/gpu/test_adapter_builder.py; source/sushicore/provision/gpu/adapter_builder.py; tests/conftest.py; tests/provision/conftest.py
test_a_second_call_with_the_same_commit_is_skipped | rewrite | 1 | _FakeRunner stand-in of CommandRunner; only test of the skip promise; rewrite needs the in-memory CommandRunner in adapter_builder.py | tests/provision/gpu/test_adapter_builder.py; source/sushicore/provision/gpu/adapter_builder.py; tests/conftest.py; tests/provision/conftest.py
test_a_matching_stamp_with_a_missing_binary_rebuilds | rewrite | 1 | _FakeRunner stand-in of CommandRunner; only test of the rebuild promise; rewrite needs the in-memory CommandRunner | tests/provision/gpu/test_adapter_builder.py; source/sushicore/provision/gpu/adapter_builder.py; tests/conftest.py; tests/provision/conftest.py
test_a_dry_run_reports_and_runs_no_commands | rewrite | 1 | _FakeRunner stand-in of CommandRunner, and the recording console is requested but never asserted; rewrite needs the in-memory runner | tests/provision/gpu/test_adapter_builder.py; source/sushicore/provision/gpu/adapter_builder.py; tests/conftest.py; tests/provision/conftest.py
test_a_failing_configure_returns_false_and_leaves_bin_untouched | rewrite | 1 | _FakeRunner stand-in of CommandRunner; only test of the failing-configure promise; rewrite needs the in-memory runner | tests/provision/gpu/test_adapter_builder.py; source/sushicore/provision/gpu/adapter_builder.py; tests/conftest.py; tests/provision/conftest.py
test_a_missing_git_or_cmake_returns_false_without_raising | rewrite | 1 | _MissingExecutableRunner stand-in of CommandRunner that raises FileNotFoundError; rewrite needs an in-memory runner that can fail that way | tests/provision/gpu/test_adapter_builder.py; source/sushicore/provision/gpu/adapter_builder.py; tests/conftest.py; tests/provision/conftest.py
test_a_failing_install_rolls_back_every_binary_already_placed | rewrite | 1 | _FakeRunner stand-in of CommandRunner, and os.replace is replaced process-wide; rewrite needs the in-memory runner and a file-move seam in adapter_builder.py | tests/provision/gpu/test_adapter_builder.py; source/sushicore/provision/gpu/adapter_builder.py; tests/conftest.py; tests/provision/conftest.py
test_a_failing_install_restores_a_pre_existing_binary | rewrite | 1 | _FakeRunner stand-in and process-wide os.replace; rewrite needs the in-memory runner and the file-move seam | tests/provision/gpu/test_adapter_builder.py; source/sushicore/provision/gpu/adapter_builder.py; tests/conftest.py; tests/provision/conftest.py
test_an_existing_stamp_keeps_its_source_and_tag_across_a_build | delete | 1 | _FakeRunner stand-in; the stamp promise is tested at medium in tests/provision/toolchains/test_stamp.py::test_record_toolchain_adapter_keeps_the_existing_source_and_tag, the stamp module's own test | tests/provision/gpu/test_adapter_builder.py; tests/provision/toolchains/test_stamp.py; source/sushicore/provision/toolchains/stamp.py; tests/conftest.py; tests/provision/conftest.py
test_windows_maps_a_base_name_to_a_dll | rewrite | 1 | _FakeRunner stand-in of CommandRunner; rewrite merges it with the Linux mapping test into one table over the platform, on the in-memory runner | tests/provision/gpu/test_adapter_builder.py; source/sushicore/provision/gpu/adapter_builder.py; tests/conftest.py; tests/provision/conftest.py
test_linux_maps_a_base_name_to_a_versioned_shared_object | rewrite | 1 | _FakeRunner stand-in of CommandRunner; rewrite as one table with the Windows test, on the in-memory runner | tests/provision/gpu/test_adapter_builder.py; source/sushicore/provision/gpu/adapter_builder.py; tests/conftest.py; tests/provision/conftest.py
test_linux_configure_does_not_force_the_msvc_compiler | rewrite | 1 | _FakeRunner stand-in of CommandRunner; the argv promise is only tested here; rewrite needs the in-memory runner | tests/provision/gpu/test_adapter_builder.py; source/sushicore/provision/gpu/adapter_builder.py; tests/conftest.py; tests/provision/conftest.py
test_configure_passes_ninja_from_config_when_set | rewrite | 1 | _FakeRunner stand-in of CommandRunner; rewrite with the ninja-omitted test as one table, on the in-memory runner | tests/provision/gpu/test_adapter_builder.py; source/sushicore/provision/gpu/adapter_builder.py; tests/conftest.py; tests/provision/conftest.py
test_configure_omits_ninja_program_when_not_configured | rewrite | 1 | _FakeRunner stand-in of CommandRunner; rewrite with the ninja-passed test as one table, on the in-memory runner | tests/provision/gpu/test_adapter_builder.py; source/sushicore/provision/gpu/adapter_builder.py; tests/conftest.py; tests/provision/conftest.py
test_the_environment_provider_is_called_at_most_once_per_builder | rewrite | 1 | _FakeRunner stand-in of CommandRunner and a counting function for the environment seam; rewrite needs the in-memory runner | tests/provision/gpu/test_adapter_builder.py; source/sushicore/provision/gpu/adapter_builder.py; tests/conftest.py; tests/provision/conftest.py
test_a_long_work_root_is_refused_on_windows | rewrite | 1 | _FakeRunner stand-in of CommandRunner; the check runs before any command and touches no file, so the rewrite can be small on the in-memory runner | tests/provision/gpu/test_adapter_builder.py; source/sushicore/provision/gpu/adapter_builder.py; tests/conftest.py; tests/provision/conftest.py
test_default_work_root_follows_the_dependency_root | rewrite | 1 | Forbidden kind: a default-value check, with the process-wide dependency root bound by the provision_home fixture; the promise (where build trees go) is real and tested only here; rewrite asserts it through the root seam | tests/provision/gpu/test_adapter_builder.py; source/sushicore/provision/gpu/adapter_builder.py; tests/conftest.py; tests/provision/conftest.py
test_a_previous_binary_that_cannot_be_removed_is_recorded | rewrite | 1 | _FakeRunner stand-in of CommandRunner, Path.unlink replaced process-wide, and the process-wide logger read through caplog; rewrite needs the in-memory runner and a log sink seam in adapter_builder.py | tests/provision/gpu/test_adapter_builder.py; source/sushicore/provision/gpu/adapter_builder.py; source/sushicore/provision/_output.py; tests/conftest.py; tests/provision/conftest.py
```

### `tests/provision/gpu/test_amd_hardware.py`

```
test_target_name_spells_minor_and_stepping_in_hex | resize | 8 | Pure function of values, marked medium; the smallest size that sees it is small, no seam needed; change the mark | tests/provision/gpu/test_amd_hardware.py; source/sushicore/provision/gpu/amd_hardware.py; tests/conftest.py
test_parse_targets_skips_the_cpu_and_collapses_twins | resize | 8 | Pure function of values, marked medium; the smallest size that sees it is small | tests/provision/gpu/test_amd_hardware.py; source/sushicore/provision/gpu/amd_hardware.py; tests/conftest.py
test_parse_targets_without_a_card_is_none | resize | 8 | Pure function of values, marked medium; change the mark to small | tests/provision/gpu/test_amd_hardware.py; source/sushicore/provision/gpu/amd_hardware.py; tests/conftest.py
test_query_hardware_reads_the_node_files | keep | 9 | Promise row: query_hardware reads each node's properties; it reads files in a per-test folder, which is the boundary the medium size exists for | tests/provision/gpu/test_amd_hardware.py; source/sushicore/provision/gpu/amd_hardware.py; tests/conftest.py
test_query_hardware_without_the_driver_is_none | keep | 9 | Promise row: a missing topology folder gives no record; the missing file is the boundary | tests/provision/gpu/test_amd_hardware.py; source/sushicore/provision/gpu/amd_hardware.py; tests/conftest.py
test_fingerprint_changes_with_the_cards | resize | 8 | Pure values, marked medium; the smallest size is small | tests/provision/gpu/test_amd_hardware.py; source/sushicore/provision/gpu/amd_hardware.py; tests/conftest.py
```

### `tests/provision/gpu/test_backend.py`

```
test_every_backend_reports_not_provided_on_darwin | rewrite | 1 | Forbidden kinds: the recording console fixture (spy on a repo-owned console, no in-memory console exists in provision/_output.py), and the private _for of PlatformLocator; rewrite through locate and provision only, with the in-memory console | tests/provision/gpu/test_backend.py; source/sushicore/provision/gpu/backend.py; source/sushicore/provision/gpu/cuda.py; source/sushicore/provision/gpu/rocm.py; source/sushicore/provision/gpu/level_zero.py; source/sushicore/provision/_output.py; tests/conftest.py; tests/provision/conftest.py
```

### `tests/provision/gpu/test_chosen_toolkit_locator.py`

```
test_the_fake_answers_the_vendor_contract | delete | 1 | Tests the test's own fake, not the code; the conformance of the real vendors is checked by tests/provision/gpu/test_cuda_vendor.py, tests/provision/gpu/test_rocm_vendor.py and tests/provision/gpu/test_toolkit_vendor.py | tests/provision/gpu/test_chosen_toolkit_locator.py; source/sushicore/provision/gpu/toolkit_vendor.py; tests/conftest.py; tests/provision/conftest.py
test_provision_installs_the_chosen_release_and_names_its_root | rewrite | 1 | Forbidden kinds: _Vendor stand-in of the repo-owned ToolkitVendor and _Environment stand-in of UserEnvironment, with no in-memory adapter beside either; process environment written through os.environ; rewrite needs both in-memory adapters and one promise per test | tests/provision/gpu/test_chosen_toolkit_locator.py; source/sushicore/provision/gpu/chosen_toolkit_locator.py; source/sushicore/provision/gpu/toolkit_vendor.py; source/sushicore/provision/gpu/toolkit_choice_file.py; source/sushicore/provision/user_environment.py; tests/conftest.py; tests/provision/conftest.py
test_a_recorded_choice_is_reused_without_the_network | rewrite | 1 | _Vendor and _Environment stand-ins of repo-owned protocols; the only test of the reuse promise; rewrite needs the in-memory ToolkitVendor | tests/provision/gpu/test_chosen_toolkit_locator.py; source/sushicore/provision/gpu/chosen_toolkit_locator.py; source/sushicore/provision/gpu/toolkit_vendor.py; source/sushicore/provision/gpu/toolkit_choice_file.py; source/sushicore/provision/user_environment.py; tests/conftest.py; tests/provision/conftest.py
test_new_hardware_chooses_again | rewrite | 1 | _Vendor stand-in of ToolkitVendor; the only test of the changed-fingerprint promise; rewrite needs the in-memory ToolkitVendor | tests/provision/gpu/test_chosen_toolkit_locator.py; source/sushicore/provision/gpu/chosen_toolkit_locator.py; source/sushicore/provision/gpu/toolkit_vendor.py; source/sushicore/provision/gpu/toolkit_choice_file.py; source/sushicore/provision/user_environment.py; tests/conftest.py; tests/provision/conftest.py
test_the_override_wins_and_is_not_recorded | rewrite | 1 | _Vendor stand-in and process environment set through monkeypatch; rewrite needs the in-memory ToolkitVendor and an injected environment | tests/provision/gpu/test_chosen_toolkit_locator.py; source/sushicore/provision/gpu/chosen_toolkit_locator.py; source/sushicore/provision/gpu/toolkit_vendor.py; source/sushicore/provision/gpu/toolkit_choice_file.py; source/sushicore/provision/user_environment.py; tests/conftest.py; tests/provision/conftest.py
test_an_unknown_override_installs_nothing | rewrite | 1 | _Vendor stand-in; asserts only that some warning exists, so the rewrite asserts the message; rewrite needs the in-memory ToolkitVendor | tests/provision/gpu/test_chosen_toolkit_locator.py; source/sushicore/provision/gpu/chosen_toolkit_locator.py; source/sushicore/provision/gpu/toolkit_vendor.py; source/sushicore/provision/gpu/toolkit_choice_file.py; source/sushicore/provision/user_environment.py; tests/conftest.py; tests/provision/conftest.py
test_an_unreachable_index_keeps_the_toolkit_in_use | rewrite | 1 | _Vendor and _Environment stand-ins; writes a marker file and asserts only that a message contains the path; rewrite needs the in-memory ToolkitVendor and UserEnvironment | tests/provision/gpu/test_chosen_toolkit_locator.py; source/sushicore/provision/gpu/chosen_toolkit_locator.py; source/sushicore/provision/gpu/toolkit_vendor.py; source/sushicore/provision/user_environment.py; tests/conftest.py; tests/provision/conftest.py
test_no_driver_installs_nothing | rewrite | 1 | _Vendor stand-in; asserts only that some warning exists; rewrite needs the in-memory ToolkitVendor | tests/provision/gpu/test_chosen_toolkit_locator.py; source/sushicore/provision/gpu/chosen_toolkit_locator.py; source/sushicore/provision/gpu/toolkit_vendor.py; source/sushicore/provision/user_environment.py; tests/conftest.py; tests/provision/conftest.py
test_dry_run_installs_nothing | rewrite | 1 | _Vendor and _Environment stand-ins; rewrite needs the in-memory ToolkitVendor and UserEnvironment | tests/provision/gpu/test_chosen_toolkit_locator.py; source/sushicore/provision/gpu/chosen_toolkit_locator.py; source/sushicore/provision/gpu/toolkit_vendor.py; source/sushicore/provision/user_environment.py; tests/conftest.py; tests/provision/conftest.py
test_hardware_no_release_fits_falls_back_to_the_cpu | rewrite | 1 | _Vendor stand-in; asserts a message substring only; rewrite needs the in-memory ToolkitVendor | tests/provision/gpu/test_chosen_toolkit_locator.py; source/sushicore/provision/gpu/chosen_toolkit_locator.py; source/sushicore/provision/gpu/toolkit_vendor.py; source/sushicore/provision/user_environment.py; tests/conftest.py; tests/provision/conftest.py
```

### `tests/provision/gpu/test_compiler_identity.py`

```
test_reads_the_commit_from_the_dpcpp_version_line | merge | 4 | Same promise as test_reads_the_commit_from_the_development_build_version_line and test_reads_the_commit_when_the_remote_url_carries_a_dot_git_suffix, other version-line inputs; one row table over the three lines | tests/provision/gpu/test_compiler_identity.py; source/sushicore/provision/gpu/compiler_identity.py; tests/conftest.py
test_reads_the_commit_from_the_development_build_version_line | merge | 4 | Same promise as the dpcpp and dot-git tests in this file, other input; merge into the row table | tests/provision/gpu/test_compiler_identity.py; source/sushicore/provision/gpu/compiler_identity.py; tests/conftest.py
test_reads_the_commit_when_the_remote_url_carries_a_dot_git_suffix | merge | 4 | Same promise as the dpcpp and development-build tests, other input; merge into the row table | tests/provision/gpu/test_compiler_identity.py; source/sushicore/provision/gpu/compiler_identity.py; tests/conftest.py
test_a_non_intel_clang_reports_no_commit | keep | 9 | Promise row: a version line naming no intel/llvm commit gives None; the run stand-in mocks clang++, an out-of-process dependency, in the test of the function that reaches it | tests/provision/gpu/test_compiler_identity.py; source/sushicore/provision/gpu/compiler_identity.py; tests/conftest.py
test_a_raising_run_reports_no_commit | merge | 4 | Same promise as test_a_timing_out_run_reports_no_commit (a failing run gives None), other input; one row table | tests/provision/gpu/test_compiler_identity.py; source/sushicore/provision/gpu/compiler_identity.py; tests/conftest.py
test_a_timing_out_run_reports_no_commit | merge | 4 | Same promise as test_a_raising_run_reports_no_commit, other input; one row table | tests/provision/gpu/test_compiler_identity.py; source/sushicore/provision/gpu/compiler_identity.py; tests/conftest.py
```

### `tests/provision/gpu/test_cuda.py`

```
test_cuda_spec_declares_the_adapter_build_inputs | rewrite | 1 | Forbidden kind: constant checks on the spec fields; the one real promise, that the toolkit root reaches the build as CUDAToolkit_ROOT, is tested nowhere else; rewrite keeps that and drops the constants | tests/provision/gpu/test_cuda.py; source/sushicore/provision/gpu/cuda.py; source/sushicore/provision/gpu/backend.py; tests/conftest.py
test_cuda_locator_finds_the_toolkit_from_cuda_path | resize | 8 | CUDA is a module-level constant, a process-wide instance; the test sets the process environment and reads a real file. Seam to build first: the CUDA spec takes an injected vendor and locator, so a small test can pass one in | tests/provision/gpu/test_cuda.py; source/sushicore/provision/gpu/cuda.py; source/sushicore/provision/gpu/chosen_toolkit_locator.py; source/sushicore/provision/gpu/cuda_vendor.py; tests/conftest.py
```

### `tests/provision/gpu/test_cuda_hardware.py`

```
test_parse_hardware_collapses_identical_cards_and_sorts_numerically | keep | 9 | Promise row: distinct architectures sorted numerically with the driver ceiling; pure, small | tests/provision/gpu/test_cuda_hardware.py; source/sushicore/provision/gpu/cuda_hardware.py; tests/conftest.py
test_parse_hardware_without_a_ceiling_is_none | merge | 4 | Same promise as test_parse_hardware_without_a_card_is_none (a missing part gives None), other missing part; one row table | tests/provision/gpu/test_cuda_hardware.py; source/sushicore/provision/gpu/cuda_hardware.py; tests/conftest.py
test_parse_hardware_without_a_card_is_none | merge | 4 | Same promise as test_parse_hardware_without_a_ceiling_is_none, other missing part; one row table | tests/provision/gpu/test_cuda_hardware.py; source/sushicore/provision/gpu/cuda_hardware.py; tests/conftest.py
test_query_hardware_without_a_driver_is_none | merge | 4 | Same promise as test_query_hardware_with_a_failing_driver_is_none (a driver that cannot answer gives None), other input; one row table | tests/provision/gpu/test_cuda_hardware.py; source/sushicore/provision/gpu/cuda_hardware.py; tests/conftest.py
test_query_hardware_with_a_failing_driver_is_none | merge | 4 | Same promise as test_query_hardware_without_a_driver_is_none, other input; one row table | tests/provision/gpu/test_cuda_hardware.py; source/sushicore/provision/gpu/cuda_hardware.py; tests/conftest.py
test_query_hardware_reads_both_commands | keep | 9 | Promise row: the compute query and the banner combine into one record; the run stand-in mocks nvidia-smi, an out-of-process dependency, in the test of the function that reaches it | tests/provision/gpu/test_cuda_hardware.py; source/sushicore/provision/gpu/cuda_hardware.py; tests/conftest.py
test_fingerprint_changes_with_the_driver_ceiling | keep | 9 | Promise row: fingerprint changes with the driver ceiling; pure, small | tests/provision/gpu/test_cuda_hardware.py; source/sushicore/provision/gpu/cuda_hardware.py; tests/conftest.py
```

### `tests/provision/gpu/test_cuda_redist.py`

```
test_versions_lists_each_release_once_newest_first | keep | 9 | Promise row: versions lists each release once, newest first; the fetch fake mocks NVIDIA's index, an out-of-process dependency, in the test of the module that reaches it | tests/provision/gpu/test_cuda_redist.py; source/sushicore/provision/gpu/cuda_redist.py; source/sushicore/provision/gpu/cuda_release.py; tests/conftest.py
test_release_keeps_only_the_archives_of_the_platform | keep | 9 | Promise row: release keeps only the requested platform's archives; also asserts label and file_name | tests/provision/gpu/test_cuda_redist.py; source/sushicore/provision/gpu/cuda_redist.py; source/sushicore/provision/gpu/cuda_release.py; tests/conftest.py
test_release_with_a_malformed_manifest_raises | keep | 9 | Promise row: a malformed manifest raises RedistError | tests/provision/gpu/test_cuda_redist.py; source/sushicore/provision/gpu/cuda_redist.py; tests/conftest.py
test_an_unreachable_index_raises | keep | 9 | Promise row: an unreachable index raises RedistError | tests/provision/gpu/test_cuda_redist.py; source/sushicore/provision/gpu/cuda_redist.py; tests/conftest.py
```

### `tests/provision/gpu/test_cuda_release.py`

```
test_versions_round_trip_through_text | keep | 9 | Promise row: parse and format are inverse; round trip oracle | tests/provision/gpu/test_cuda_release.py; source/sushicore/provision/gpu/cuda_release.py; tests/conftest.py
test_a_version_that_is_not_digits_raises | keep | 9 | Promise row: text that is not digits raises ValueError | tests/provision/gpu/test_cuda_release.py; source/sushicore/provision/gpu/cuda_release.py; tests/conftest.py
test_a_release_is_labelled_and_an_archive_named_from_its_url | delete | 1 | Forbidden kind: trivial getters (label, file_name); the same two properties are asserted by tests/provision/gpu/test_cuda_redist.py::test_release_keeps_only_the_archives_of_the_platform | tests/provision/gpu/test_cuda_release.py; source/sushicore/provision/gpu/cuda_release.py; tests/provision/gpu/test_cuda_redist.py; tests/conftest.py
```

### `tests/provision/gpu/test_cuda_selection.py`

```
test_the_driver_ceiling_excludes_newer_releases | rewrite | 1 | Forbidden kind: _Probe is a recorder of the repo's ArchitectureProbe seam, and the test asserts the order of probe calls; this is the small copy of the ceiling promise, so it stays and is rewritten: a table-backed in-memory probe in cuda_selection.py, with rows over driver ceilings 13.1 and 12.6 | tests/provision/gpu/test_cuda_selection.py; source/sushicore/provision/gpu/cuda_selection.py; source/sushicore/provision/gpu/cuda_hardware.py; tests/conftest.py
test_a_pascal_card_walks_back_one_major | rewrite | 1 | Forbidden kind: _Probe recorder, asserting the order of probe calls; the walk-back promise is tested only here; rewrite with the in-memory probe in cuda_selection.py | tests/provision/gpu/test_cuda_selection.py; source/sushicore/provision/gpu/cuda_selection.py; source/sushicore/provision/gpu/cuda_hardware.py; tests/conftest.py
test_an_old_driver_gets_an_old_release | delete | 1 | Forbidden kind: _Probe recorder; same promise as test_the_driver_ceiling_excludes_newer_releases in this file (driver ceiling), whose rewrite takes this driver as an input row | tests/provision/gpu/test_cuda_selection.py; source/sushicore/provision/gpu/cuda_selection.py; tests/conftest.py
test_no_fitting_release_is_none | rewrite | 1 | _Probe stand-in; only test of the None result; rewrite with the in-memory probe | tests/provision/gpu/test_cuda_selection.py; source/sushicore/provision/gpu/cuda_selection.py; source/sushicore/provision/gpu/cuda_hardware.py; tests/conftest.py
```

### `tests/provision/gpu/test_cuda_toolkit_installer.py`

```
test_install_merges_every_component_into_one_root | rewrite | 1 | Forbidden kind: autouse recording_console spy on the repo's console; provision/_output.py has no in-memory console to use instead; rewrite needs that adapter (the download fake is an allowed network mock here) | tests/provision/gpu/test_cuda_toolkit_installer.py; source/sushicore/provision/gpu/cuda_toolkit_installer.py; source/sushicore/provision/_output.py; tests/conftest.py; tests/provision/conftest.py
test_install_of_an_installed_release_downloads_nothing | rewrite | 1 | Forbidden kind: autouse recording_console spy; rewrite needs the in-memory console in provision/_output.py | tests/provision/gpu/test_cuda_toolkit_installer.py; source/sushicore/provision/gpu/cuda_toolkit_installer.py; source/sushicore/provision/_output.py; tests/conftest.py; tests/provision/conftest.py
test_a_mismatching_archive_installs_nothing | rewrite | 1 | Forbidden kind: autouse recording_console spy; rewrite needs the in-memory console | tests/provision/gpu/test_cuda_toolkit_installer.py; source/sushicore/provision/gpu/cuda_toolkit_installer.py; source/sushicore/provision/_output.py; tests/conftest.py; tests/provision/conftest.py
test_a_missing_required_component_installs_nothing | rewrite | 1 | Forbidden kind: autouse recording_console spy; rewrite needs the in-memory console | tests/provision/gpu/test_cuda_toolkit_installer.py; source/sushicore/provision/gpu/cuda_toolkit_installer.py; source/sushicore/provision/_output.py; tests/conftest.py; tests/provision/conftest.py
test_an_archive_escaping_its_folder_is_refused | rewrite | 1 | Forbidden kind: autouse recording_console spy; rewrite needs the in-memory console | tests/provision/gpu/test_cuda_toolkit_installer.py; source/sushicore/provision/gpu/cuda_toolkit_installer.py; source/sushicore/provision/_output.py; tests/conftest.py; tests/provision/conftest.py
test_a_tar_xz_archive_unpacks | rewrite | 1 | Forbidden kind: autouse recording_console spy; rewrite needs the in-memory console | tests/provision/gpu/test_cuda_toolkit_installer.py; source/sushicore/provision/gpu/cuda_toolkit_installer.py; source/sushicore/provision/_output.py; tests/conftest.py; tests/provision/conftest.py
test_probe_unpacks_only_the_compiler_and_cleans_up | rewrite | 1 | Forbidden kind: autouse recording_console spy, and the module's own list_gpu_architectures is replaced; rewrite needs the in-memory console and a probe seam | tests/provision/gpu/test_cuda_toolkit_installer.py; source/sushicore/provision/gpu/cuda_toolkit_installer.py; source/sushicore/provision/_output.py; tests/conftest.py; tests/provision/conftest.py
test_list_gpu_architectures_reads_the_compute_lines | rewrite | 1 | Forbidden kind: autouse recording_console spy; also subprocess.run is replaced through the module (fails on any change inside the function, Q5); rewrite needs the in-memory console and an injected runner in list_gpu_architectures | tests/provision/gpu/test_cuda_toolkit_installer.py; source/sushicore/provision/gpu/cuda_toolkit_installer.py; source/sushicore/provision/_output.py; tests/conftest.py; tests/provision/conftest.py
test_list_gpu_architectures_of_a_broken_compiler_raises | rewrite | 1 | Forbidden kind: autouse recording_console spy; subprocess.run replaced through the module; rewrite needs the in-memory console and an injected runner | tests/provision/gpu/test_cuda_toolkit_installer.py; source/sushicore/provision/gpu/cuda_toolkit_installer.py; source/sushicore/provision/_output.py; tests/conftest.py; tests/provision/conftest.py
```

### `tests/provision/gpu/test_cuda_vendor.py`

```
test_the_vendor_answers_the_contract | delete | 1 | Forbidden kind: fixture stand-ins of RedistIndex and RedistToolkitInstaller, repo-owned types; the conformance is checked by tests/provision/gpu/test_toolkit_vendor.py::test_every_vendor_defines_every_member_of_the_protocol at small size | tests/provision/gpu/test_cuda_vendor.py; tests/provision/gpu/test_toolkit_vendor.py; source/sushicore/provision/gpu/cuda_vendor.py; source/sushicore/provision/gpu/toolkit_vendor.py; tests/conftest.py; tests/provision/conftest.py
test_the_driver_ceiling_excludes_newer_releases | delete | 1 | Forbidden kind: fixture stand-ins of RedistIndex and RedistToolkitInstaller; the same promise is checked at small size by tests/provision/gpu/test_cuda_selection.py::test_the_driver_ceiling_excludes_newer_releases, which is rewritten to stay | tests/provision/gpu/test_cuda_vendor.py; tests/provision/gpu/test_cuda_selection.py; source/sushicore/provision/gpu/cuda_vendor.py; source/sushicore/provision/gpu/cuda_selection.py; tests/conftest.py; tests/provision/conftest.py
test_a_pascal_card_gets_the_newest_12x | delete | 1 | Forbidden kind: fixture stand-ins; the same promise is checked at small size by tests/provision/gpu/test_cuda_selection.py::test_a_pascal_card_walks_back_one_major, which is rewritten to stay | tests/provision/gpu/test_cuda_vendor.py; tests/provision/gpu/test_cuda_selection.py; source/sushicore/provision/gpu/cuda_vendor.py; source/sushicore/provision/gpu/cuda_selection.py; tests/conftest.py; tests/provision/conftest.py
test_a_compiler_that_does_not_run_is_skipped | rewrite | 1 | Forbidden kind: _Installer stand-in of RedistToolkitInstaller with a broken-compiler set; the only test of the skip; rewrite needs an in-memory installer with a broken-compiler mode in cuda_toolkit_installer.py | tests/provision/gpu/test_cuda_vendor.py; source/sushicore/provision/gpu/cuda_vendor.py; source/sushicore/provision/gpu/cuda_toolkit_installer.py; tests/conftest.py; tests/provision/conftest.py
test_an_override_prefix_names_the_newest_match | rewrite | 1 | Forbidden kind: _Index and _Installer stand-ins of repo-owned types; only test of the prefix override; rewrite needs the in-memory index and installer | tests/provision/gpu/test_cuda_vendor.py; source/sushicore/provision/gpu/cuda_vendor.py; source/sushicore/provision/gpu/cuda_redist.py; source/sushicore/provision/gpu/cuda_toolkit_installer.py; tests/conftest.py; tests/provision/conftest.py
test_an_override_that_is_not_a_version_raises | rewrite | 1 | Forbidden kind: _Index and _Installer stand-ins; only test of the refusal; rewrite needs the in-memory index and installer | tests/provision/gpu/test_cuda_vendor.py; source/sushicore/provision/gpu/cuda_vendor.py; source/sushicore/provision/gpu/cuda_redist.py; source/sushicore/provision/gpu/cuda_toolkit_installer.py; tests/conftest.py; tests/provision/conftest.py
test_install_hands_the_release_of_the_label_to_the_installer | rewrite | 1 | Forbidden kind: _Index and _Installer stand-ins; the installer records the label; rewrite needs the in-memory index and installer | tests/provision/gpu/test_cuda_vendor.py; source/sushicore/provision/gpu/cuda_vendor.py; source/sushicore/provision/gpu/cuda_redist.py; source/sushicore/provision/gpu/cuda_toolkit_installer.py; tests/conftest.py; tests/provision/conftest.py
test_a_root_without_nvcc_is_not_a_toolkit | rewrite | 1 | Forbidden kind by its fixture: the vendor fixture builds stand-ins this test does not use; the promise needs only a real folder with no nvcc, so the rewrite drops the fixture and stays medium for the file check | tests/provision/gpu/test_cuda_vendor.py; source/sushicore/provision/gpu/cuda_vendor.py; source/sushicore/provision/gpu/cuda_toolkit_installer.py; tests/conftest.py; tests/provision/conftest.py
```

### `tests/provision/gpu/test_gpu_hardware.py`

```
test_an_object_with_both_methods_is_gpu_hardware | delete | 1 | Forbidden kind: stand-ins of the repo-owned GpuHardware protocol; no source code calls isinstance against GpuHardware (grep of source/sushicore/provision/gpu/), so the test states no promise the code relies on | tests/provision/gpu/test_gpu_hardware.py; source/sushicore/provision/gpu/gpu_hardware.py; source/sushicore/provision/gpu/chosen_toolkit_locator.py; tests/conftest.py
test_an_object_without_describe_is_not | delete | 1 | Forbidden kind: stand-ins of GpuHardware; no source code uses the runtime protocol check | tests/provision/gpu/test_gpu_hardware.py; source/sushicore/provision/gpu/gpu_hardware.py; tests/conftest.py
```

### `tests/provision/gpu/test_level_zero.py`

```
test_level_zero_spec_declares_the_adapter_build_inputs | delete | 1 | Forbidden kind: constant checks and an empty dict from adapter_definitions; no behaviour is tested | tests/provision/gpu/test_level_zero.py; source/sushicore/provision/gpu/level_zero.py; source/sushicore/provision/gpu/backend.py; tests/conftest.py
test_level_zero_linux_provision_command_matches_the_pinned_text | rewrite | 1 | Forbidden kinds: recording_console spy, and two functions imported into the module are replaced (ensure_intel_oneapi_repo, is_root); rewrite needs the in-memory console in provision/_output.py and a seam for the root check and repo setup | tests/provision/gpu/test_level_zero.py; source/sushicore/provision/gpu/level_zero.py; source/sushicore/provision/system.py; source/sushicore/provision/_output.py; tests/conftest.py; tests/provision/conftest.py
test_level_zero_locator_finds_the_loader_via_find_library | rewrite | 5 | ctypes.util.find_library is replaced process-wide; the test breaks on any change inside the locator that does not go through find_library (Q5); rewrite injects the library lookup and tests the directory choice on values | tests/provision/gpu/test_level_zero.py; source/sushicore/provision/gpu/level_zero.py; tests/conftest.py
test_level_zero_locator_falls_back_to_the_known_lib_dirs | rewrite | 5 | ctypes.util.find_library and the module constant _ZE_LOADER_LIB_DIRS are replaced; the test breaks if the constant is renamed (Q5); rewrite passes the directories in | tests/provision/gpu/test_level_zero.py; source/sushicore/provision/gpu/level_zero.py; tests/conftest.py
test_level_zero_locator_reports_nothing_when_the_loader_is_absent | rewrite | 5 | Same replacements as the fallback test; breaks on internal renames (Q5); rewrite passes the directories in | tests/provision/gpu/test_level_zero.py; source/sushicore/provision/gpu/level_zero.py; tests/conftest.py
```

### `tests/provision/gpu/test_provisioning.py`

```
test_a_missing_commit_builds_nothing | delete | 1 | Forbidden kind: _FakeBuilder, _FakeLocator and commit-reader stand-ins; the same promise, builder.built == [], is asserted by tests/provision/gpu/test_provisioning.py::test_a_missing_commit_warns, which is rewritten to stay | tests/provision/gpu/test_provisioning.py; source/sushicore/provision/gpu/provisioning.py; source/sushicore/provision/gpu/registry.py; source/sushicore/provision/gpu/backend.py; tests/conftest.py; tests/provision/conftest.py
test_a_backend_with_no_located_toolkit_is_skipped | rewrite | 1 | Forbidden kind: stand-ins of ToolkitLocator, AdapterBuilder and the commit reader; rewrite needs an in-memory ToolkitLocator and an in-memory builder | tests/provision/gpu/test_provisioning.py; source/sushicore/provision/gpu/provisioning.py; source/sushicore/provision/gpu/registry.py; source/sushicore/provision/gpu/backend.py; source/sushicore/provision/gpu/adapter_builder.py; tests/conftest.py; tests/provision/conftest.py
test_one_built_and_one_failed_are_both_called_and_neither_raises | rewrite | 1 | Forbidden kinds: _FakeBuilder stand-in and the recording console, asserted empty; rewrite needs the in-memory builder and console | tests/provision/gpu/test_provisioning.py; source/sushicore/provision/gpu/provisioning.py; source/sushicore/provision/_output.py; tests/conftest.py; tests/provision/conftest.py
test_a_locator_that_raises_is_swallowed_and_warned | rewrite | 1 | Forbidden kinds: a locator stand-in defined in the test and the recording console; rewrite needs the in-memory console | tests/provision/gpu/test_provisioning.py; source/sushicore/provision/gpu/provisioning.py; source/sushicore/provision/_output.py; tests/conftest.py; tests/provision/conftest.py
test_a_missing_commit_warns | rewrite | 1 | Forbidden kinds: commit-reader, builder and locator stand-ins and the recording console; the only test of the warning; rewrite merges it with the dry-run test into one table over dry_run, in-memory console | tests/provision/gpu/test_provisioning.py; source/sushicore/provision/gpu/provisioning.py; source/sushicore/provision/_output.py; tests/conftest.py; tests/provision/conftest.py
test_a_missing_commit_in_dry_run_prints_the_dry_run_line_instead_of_a_warning | rewrite | 1 | Forbidden kinds: stand-ins and the recording console; rewrite merges with test_a_missing_commit_warns into one table over dry_run | tests/provision/gpu/test_provisioning.py; source/sushicore/provision/gpu/provisioning.py; source/sushicore/provision/_output.py; tests/conftest.py; tests/provision/conftest.py
```

### `tests/provision/gpu/test_registry.py`

```
test_a_registered_spec_is_found_by_vendor_and_probe_key | rewrite | 1 | Forbidden kind: _FakeLocator stand-in of the repo-owned ToolkitLocator inside the spec the test builds; the lookups need no locator; rewrite without the stand-in | tests/provision/gpu/test_registry.py; source/sushicore/provision/gpu/registry.py; source/sushicore/provision/gpu/backend.py; tests/conftest.py; tests/provision/conftest.py
test_an_unknown_vendor_or_probe_key_returns_none | rewrite | 1 | Forbidden kind: _FakeLocator stand-in in the spec; rewrite without it | tests/provision/gpu/test_registry.py; source/sushicore/provision/gpu/registry.py; source/sushicore/provision/gpu/backend.py; tests/conftest.py; tests/provision/conftest.py
test_a_duplicate_vendor_name_is_refused | rewrite | 1 | Forbidden kind: _FakeLocator stand-in in the specs; rewrite merges with the duplicate-probe test into one table, without the stand-in | tests/provision/gpu/test_registry.py; source/sushicore/provision/gpu/registry.py; source/sushicore/provision/gpu/backend.py; tests/conftest.py; tests/provision/conftest.py
test_a_duplicate_probe_vendor_is_refused | rewrite | 1 | Forbidden kind: _FakeLocator stand-in; rewrite merges with the duplicate-vendor test into one table | tests/provision/gpu/test_registry.py; source/sushicore/provision/gpu/registry.py; source/sushicore/provision/gpu/backend.py; tests/conftest.py; tests/provision/conftest.py
test_platform_locator_dispatches_to_the_matching_platform | rewrite | 1 | Forbidden kind: _FakeLocator stand-in that records provision calls; rewrite needs an in-memory ToolkitLocator beside the protocol in backend.py | tests/provision/gpu/test_registry.py; source/sushicore/provision/gpu/backend.py; tests/conftest.py; tests/provision/conftest.py
test_platform_locator_falls_back_to_not_provided | rewrite | 1 | Forbidden kinds: _FakeLocator stand-in and the recording console; rewrite needs the in-memory ToolkitLocator and console | tests/provision/gpu/test_registry.py; source/sushicore/provision/gpu/backend.py; source/sushicore/provision/_output.py; tests/conftest.py; tests/provision/conftest.py
test_not_provided_always_locates_nothing_and_reports_success | rewrite | 1 | Forbidden kind: the recording console, which NotProvided.provision writes through; rewrite needs the in-memory console in provision/_output.py | tests/provision/gpu/test_registry.py; source/sushicore/provision/gpu/backend.py; source/sushicore/provision/_output.py; tests/conftest.py; tests/provision/conftest.py
test_platform_locator_works_with_a_plain_config_stand_in | delete | 1 | Forbidden kind: _FakeLocator stand-in; same promise as test_platform_locator_dispatches_to_the_matching_platform in this file, which survives as a rewrite | tests/provision/gpu/test_registry.py; source/sushicore/provision/gpu/backend.py; tests/conftest.py; tests/provision/conftest.py
```

### `tests/provision/gpu/test_rocm.py`

```
test_rocm_spec_declares_the_adapter_build_inputs | rewrite | 1 | Forbidden kind: constant checks; the one real promise, that the install directory reaches the build as UR_HIP_ROCM_DIR, is tested nowhere else; rewrite keeps that and drops the constants | tests/provision/gpu/test_rocm.py; source/sushicore/provision/gpu/rocm.py; source/sushicore/provision/gpu/backend.py; tests/conftest.py
test_rocm_locator_takes_the_root_rocm_path_names | resize | 8 | ROCM is a module-level process-wide instance; the test sets the process environment and reads a real header file. Seam to build first: the ROCm spec takes an injected vendor and locator | tests/provision/gpu/test_rocm.py; source/sushicore/provision/gpu/rocm.py; source/sushicore/provision/gpu/chosen_toolkit_locator.py; source/sushicore/provision/gpu/rocm_vendor.py; tests/conftest.py
```

### `tests/provision/gpu/test_rocm_package.py`

```
test_builds_for_reads_x_as_any_character | keep | 9 | Promise row: an x in the family pattern matches any digit, with the length rule (six rows); pure, small | tests/provision/gpu/test_rocm_package.py; source/sushicore/provision/gpu/rocm_package.py; tests/conftest.py
test_label_joins_release_and_family | delete | 1 | Forbidden kind: trivial getter; the install folder name is asserted by tests/provision/gpu/test_rocm_toolkit_installer.py::test_install_unpacks_the_tarball_as_the_root and tests/provision/gpu/test_rocm_selection.py::test_the_newest_release_of_the_covering_family_is_chosen | tests/provision/gpu/test_rocm_package.py; source/sushicore/provision/gpu/rocm_package.py; tests/provision/gpu/test_rocm_toolkit_installer.py; tests/provision/gpu/test_rocm_selection.py; tests/conftest.py
test_an_exact_family_is_more_specific_than_a_wildcard_one | delete | 1 | Forbidden kind: change detector on the internal ranking key specificity(); the behaviour is asserted by tests/provision/gpu/test_rocm_selection.py::test_an_exact_family_beats_a_wildcard_one | tests/provision/gpu/test_rocm_package.py; source/sushicore/provision/gpu/rocm_package.py; tests/provision/gpu/test_rocm_selection.py; tests/conftest.py
```

### `tests/provision/gpu/test_rocm_selection.py`

```
test_the_newest_release_of_the_covering_family_is_chosen | keep | 9 | Promise row: select_package returns the newest release with one family covering every card; pure, small | tests/provision/gpu/test_rocm_selection.py; source/sushicore/provision/gpu/rocm_selection.py; source/sushicore/provision/gpu/rocm_package.py; source/sushicore/provision/gpu/amd_hardware.py; tests/conftest.py
test_an_exact_family_beats_a_wildcard_one | keep | 9 | Promise row: an exact family beats a wildcard for one release; pure, small | tests/provision/gpu/test_rocm_selection.py; source/sushicore/provision/gpu/rocm_selection.py; source/sushicore/provision/gpu/rocm_package.py; source/sushicore/provision/gpu/amd_hardware.py; tests/conftest.py
test_cards_no_single_family_covers_get_nothing | keep | 9 | Promise row: no family covering every card gives None; pure, small | tests/provision/gpu/test_rocm_selection.py; source/sushicore/provision/gpu/rocm_selection.py; source/sushicore/provision/gpu/rocm_package.py; source/sushicore/provision/gpu/amd_hardware.py; tests/conftest.py
test_two_cards_of_one_family_share_its_tarball | keep | 9 | Promise row: two cards of one family share that family's tarball; pure, small | tests/provision/gpu/test_rocm_selection.py; source/sushicore/provision/gpu/rocm_selection.py; source/sushicore/provision/gpu/rocm_package.py; source/sushicore/provision/gpu/amd_hardware.py; tests/conftest.py
```

### `tests/provision/gpu/test_rocm_tarball_index.py`

```
test_packages_lists_one_platform_newest_first_without_duplicates | keep | 9 | Promise row: packages lists one platform newest first without duplicates; the fetch fake mocks AMD's listing, an out-of-process dependency, in the test of the module that reaches it | tests/provision/gpu/test_rocm_tarball_index.py; source/sushicore/provision/gpu/rocm_tarball_index.py; source/sushicore/provision/gpu/rocm_package.py; tests/conftest.py
test_an_unreachable_listing_raises | keep | 9 | Promise row: an unreachable listing raises RocmIndexError | tests/provision/gpu/test_rocm_tarball_index.py; source/sushicore/provision/gpu/rocm_tarball_index.py; tests/conftest.py
```

### `tests/provision/gpu/test_rocm_toolkit_installer.py`

```
test_install_unpacks_the_tarball_as_the_root | rewrite | 1 | Forbidden kind: autouse recording_console spy; provision/_output.py has no in-memory console; rewrite needs it | tests/provision/gpu/test_rocm_toolkit_installer.py; source/sushicore/provision/gpu/rocm_toolkit_installer.py; source/sushicore/provision/_output.py; tests/conftest.py; tests/provision/conftest.py
test_an_installed_release_is_not_downloaded_again | rewrite | 1 | Forbidden kind: autouse recording_console spy; rewrite needs the in-memory console | tests/provision/gpu/test_rocm_toolkit_installer.py; source/sushicore/provision/gpu/rocm_toolkit_installer.py; source/sushicore/provision/_output.py; tests/conftest.py; tests/provision/conftest.py
test_a_tarball_without_hip_headers_installs_nothing | rewrite | 1 | Forbidden kind: autouse recording_console spy; rewrite needs the in-memory console | tests/provision/gpu/test_rocm_toolkit_installer.py; source/sushicore/provision/gpu/rocm_toolkit_installer.py; source/sushicore/provision/_output.py; tests/conftest.py; tests/provision/conftest.py
test_a_corrupt_tarball_installs_nothing | rewrite | 1 | Forbidden kind: autouse recording_console spy; rewrite needs the in-memory console | tests/provision/gpu/test_rocm_toolkit_installer.py; source/sushicore/provision/gpu/rocm_toolkit_installer.py; source/sushicore/provision/_output.py; tests/conftest.py; tests/provision/conftest.py
test_a_failed_download_installs_nothing | rewrite | 1 | Forbidden kind: autouse recording_console spy; rewrite needs the in-memory console; its final check lists the downloads folder, which exists only because install created it first | tests/provision/gpu/test_rocm_toolkit_installer.py; source/sushicore/provision/gpu/rocm_toolkit_installer.py; source/sushicore/provision/_output.py; tests/conftest.py; tests/provision/conftest.py
```

### `tests/provision/gpu/test_rocm_vendor.py`

```
test_the_vendor_answers_the_contract | delete | 1 | Forbidden kind: fixture stand-ins of RocmTarballIndex and RocmTarballInstaller; the conformance is checked by tests/provision/gpu/test_toolkit_vendor.py::test_every_vendor_defines_every_member_of_the_protocol at small size | tests/provision/gpu/test_rocm_vendor.py; tests/provision/gpu/test_toolkit_vendor.py; source/sushicore/provision/gpu/rocm_vendor.py; source/sushicore/provision/gpu/toolkit_vendor.py; tests/conftest.py; tests/provision/conftest.py
test_choose_takes_the_newest_covering_family | delete | 1 | Forbidden kind: fixture stand-ins; the same promise at small size is in tests/provision/gpu/test_rocm_selection.py::test_the_newest_release_of_the_covering_family_is_chosen | tests/provision/gpu/test_rocm_vendor.py; tests/provision/gpu/test_rocm_selection.py; source/sushicore/provision/gpu/rocm_vendor.py; source/sushicore/provision/gpu/rocm_selection.py; tests/conftest.py; tests/provision/conftest.py
test_an_override_release_keeps_the_family_the_cards_need | rewrite | 1 | Forbidden kind: _Index and _Installer stand-ins of repo-owned types; only test of the prefix override that keeps the family; rewrite needs the in-memory index and installer | tests/provision/gpu/test_rocm_vendor.py; source/sushicore/provision/gpu/rocm_vendor.py; source/sushicore/provision/gpu/rocm_tarball_index.py; source/sushicore/provision/gpu/rocm_toolkit_installer.py; tests/conftest.py; tests/provision/conftest.py
test_an_override_with_a_family_names_it_exactly | rewrite | 1 | Forbidden kind: _Index and _Installer stand-ins; rewrite needs the in-memory index and installer | tests/provision/gpu/test_rocm_vendor.py; source/sushicore/provision/gpu/rocm_vendor.py; source/sushicore/provision/gpu/rocm_tarball_index.py; source/sushicore/provision/gpu/rocm_toolkit_installer.py; tests/conftest.py; tests/provision/conftest.py
test_an_override_that_is_not_a_release_raises | rewrite | 1 | Forbidden kind: _Index and _Installer stand-ins; rewrite needs the in-memory index and installer | tests/provision/gpu/test_rocm_vendor.py; source/sushicore/provision/gpu/rocm_vendor.py; source/sushicore/provision/gpu/rocm_tarball_index.py; source/sushicore/provision/gpu/rocm_toolkit_installer.py; tests/conftest.py; tests/provision/conftest.py
test_install_hands_the_listed_tarball_to_the_installer | rewrite | 1 | Forbidden kind: _Index and _Installer stand-ins; rewrite needs the in-memory index and installer | tests/provision/gpu/test_rocm_vendor.py; source/sushicore/provision/gpu/rocm_vendor.py; source/sushicore/provision/gpu/rocm_tarball_index.py; source/sushicore/provision/gpu/rocm_toolkit_installer.py; tests/conftest.py; tests/provision/conftest.py
test_a_label_no_longer_listed_raises | rewrite | 1 | Forbidden kind: _Index stand-in; rewrite needs the in-memory index | tests/provision/gpu/test_rocm_vendor.py; source/sushicore/provision/gpu/rocm_vendor.py; source/sushicore/provision/gpu/rocm_tarball_index.py; tests/conftest.py; tests/provision/conftest.py
```

### `tests/provision/gpu/test_toolkit_choice.py`

```
test_a_choice_is_frozen_and_compares_by_value | delete | 1 | Forbidden kind: trivial; tests generated dataclass behaviour (frozen, equality); equality on read-back is asserted by tests/provision/gpu/test_toolkit_choice_file.py::test_a_written_choice_reads_back | tests/provision/gpu/test_toolkit_choice.py; source/sushicore/provision/gpu/toolkit_choice.py; tests/provision/gpu/test_toolkit_choice_file.py; tests/conftest.py
```

### `tests/provision/gpu/test_toolkit_choice_file.py`

```
test_a_written_choice_reads_back | keep | 9 | Promise row: a written choice reads back equal; round-trip oracle, and the file is the boundary medium exists for | tests/provision/gpu/test_toolkit_choice_file.py; source/sushicore/provision/gpu/toolkit_choice_file.py; source/sushicore/provision/gpu/toolkit_choice.py; tests/conftest.py
test_a_missing_file_reads_as_none | merge | 4 | Same promise as test_another_format_reads_as_none and test_a_corrupt_file_reads_as_none (an unusable file reads as None), other inputs; one row table over the unusable inputs | tests/provision/gpu/test_toolkit_choice_file.py; source/sushicore/provision/gpu/toolkit_choice_file.py; tests/conftest.py
test_another_format_reads_as_none | merge | 4 | Same promise as the missing-file and corrupt-file tests in this file, other input; one row table | tests/provision/gpu/test_toolkit_choice_file.py; source/sushicore/provision/gpu/toolkit_choice_file.py; tests/conftest.py
test_a_corrupt_file_reads_as_none | merge | 4 | Same promise as the missing-file and other-format tests in this file, other input; one row table | tests/provision/gpu/test_toolkit_choice_file.py; source/sushicore/provision/gpu/toolkit_choice_file.py; tests/conftest.py
```

### `tests/provision/gpu/test_toolkit_vendor.py`

```
test_the_protocol_names_every_member_a_vendor_needs | keep | 9 | toolkit_vendor: the protocol names name, choose, install and is_toolkit_root | tests/provision/gpu/test_toolkit_vendor.py; source/sushicore/provision/gpu/toolkit_vendor.py
test_every_vendor_defines_every_member_of_the_protocol | rewrite | 7 | toolkit_vendor: every vendor defines every member. This is the contract copy, so it stays at question 4; the per-vendor copies in test_cuda_vendor.py, test_rocm_vendor.py and test_chosen_toolkit_locator.py merge into it. The loop over members in the body becomes rows over vendor and member | tests/provision/gpu/test_toolkit_vendor.py; source/sushicore/provision/gpu/toolkit_vendor.py; source/sushicore/provision/gpu/cuda_vendor.py; source/sushicore/provision/gpu/rocm_vendor.py; tests/provision/gpu/test_cuda_vendor.py; tests/provision/gpu/test_rocm_vendor.py; tests/provision/gpu/test_chosen_toolkit_locator.py
test_a_source_error_is_an_exception | delete | 1 | trivial code: the base class of an exception. The promise callers rely on is the catch at source/sushicore/provision/gpu/chosen_toolkit_locator.py:79, which test_an_unreachable_index_keeps_the_toolkit_in_use exercises (its fake raises ToolkitSourceError at line 112) | tests/provision/gpu/test_toolkit_vendor.py; source/sushicore/provision/gpu/toolkit_vendor.py; source/sushicore/provision/gpu/chosen_toolkit_locator.py; tests/provision/gpu/test_chosen_toolkit_locator.py
```

### `tests/provision/gpu/test_windows_installer.py`

```
test_ps_quote_escapes_a_single_quote_and_keeps_spaces_and_backslashes | rewrite | 1 | forbidden kind: imports the _private name _ps_quote. Its promise (a single quote is doubled inside the literal) is reached by no public name in the file. Rewrite through PowerShellElevatedRunner.command with an apostrophe in the executable path | source/sushicore/provision/gpu/windows_installer.py; tests/provision/gpu/test_windows_installer.py
test_powershell_elevated_runner_command_builds_the_expected_argv | rewrite | 5 | the expected value is the whole script text copied from the code, so rewording the script fails it while the argv promise still holds. Rewrite against the argv contract: argv head, executable and arguments inside the script, ELEVATION_DECLINED and LAUNCH_FAILED exit codes | source/sushicore/provision/gpu/windows_installer.py; tests/provision/gpu/test_windows_installer.py
test_prepend_machine_path_adds_only_the_entries_not_already_on_path | rewrite | 1 | forbidden stand-in: _FakeEnvironment stands in for the MachineEnvironment port that windows_installer.py owns, and os.environ is set in a small test. Rewrite as one rows test over the four inputs (adds, case-insensitive dedupe, nothing fresh, empty PATH), with an InMemoryMachineEnvironment living in windows_installer.py. Seam for question 8: a value function (process PATH, machine PATH) to PATH | source/sushicore/provision/gpu/windows_installer.py; tests/provision/gpu/test_windows_installer.py
test_prepend_machine_path_dedupes_case_insensitively | delete | 1 | same forbidden stand-in and os.environ reach; its promise is the case-dedupe row of the rewrite on the line above | tests/provision/gpu/test_windows_installer.py; source/sushicore/provision/gpu/windows_installer.py
test_prepend_machine_path_leaves_path_untouched_when_nothing_is_fresh | delete | 1 | same forbidden stand-in and os.environ reach; its promise is the nothing-fresh row of the rewrite above | tests/provision/gpu/test_windows_installer.py; source/sushicore/provision/gpu/windows_installer.py
test_prepend_machine_path_handles_an_empty_process_path | delete | 1 | same forbidden stand-in and os.environ reach; its promise is the empty-PATH row of the rewrite above | tests/provision/gpu/test_windows_installer.py; source/sushicore/provision/gpu/windows_installer.py
```

### `tests/provision/packages/test_base.py`

```
test_a_refused_registry_read_is_recorded_and_leaves_path_alone | resize | 8 | base: refresh_windows_path. Question 4 found test_a_defect_in_the_registry_read_is_not_swallowed on the same catch boundary; that test merges into this one as a row, so this is the host. Small reach: the process-wide logger (caplog), os.environ and sys.modules. The decision on the error is seen small once the registry reader and the PATH value are parameters of refresh_windows_path, with an in-memory reader beside the real one | tests/provision/packages/test_base.py; source/sushicore/provision/packages/base.py; source/sushicore/provision/gpu/windows_installer.py; tests/provision/conftest.py
test_a_defect_in_the_registry_read_is_not_swallowed | merge | 4 | base: refresh_windows_path. Same promise as the test above (only OSError is caught); the TypeError row joins that test's rows | tests/provision/packages/test_base.py; source/sushicore/provision/packages/base.py
```

### `tests/provision/packages/test_direct_download.py`

```
test_cmake_direct_install_only_removes_paths_under_the_bound_root | rewrite | 1 | forbidden stubs: gh_latest_asset, download, _cmake_on_system and _add_to_user_path_windows are functions the repository owns; shutil.rmtree is spied on, and the spy asserts an internal call (change detector). The name claims a bound-root rule the body never tests. Rewrite: stub urllib.request.urlopen and winreg (both outside the repository), then assert the outcome: the stale file is gone and cmake.exe is in place. Doxygen case joins it as a row (line below) | source/sushicore/provision/packages/direct_download.py; tests/provision/packages/test_direct_download.py; tests/provision/conftest.py; tests/provision/test_download_verifier/test_downloads_are_verified.py
test_doxygen_direct_install_only_removes_paths_under_the_bound_root | delete | 1 | same forbidden stubs; its promise (the install replaces the previous folder) is the doxygen row of the cmake rewrite above | tests/provision/packages/test_direct_download.py; source/sushicore/provision/packages/direct_download.py
test_a_refused_user_path_write_is_recorded_and_reported | split | 3 | two promises in one test: a refused write returns False and logs one warning naming the directory; this process still gets the directory on its PATH. Split into one test per promise, each then answered at question 8 for the registry seam | tests/provision/packages/test_direct_download.py; source/sushicore/provision/packages/direct_download.py
test_a_user_path_write_that_lands_reports_success | resize | 8 | the fake winreg reaches sys.modules (process-wide) from a medium test, and the decision (store the value, return True) is made on values. Seam: _add_to_user_path_windows takes its registry key store as a parameter, with an in-memory store beside it; the test then runs small | tests/provision/packages/test_direct_download.py; source/sushicore/provision/packages/direct_download.py
test_a_defect_in_the_user_path_write_is_not_swallowed | resize | 8 | same sys.modules reach. The promise (only OSError is caught) is a decision on values, so it runs small once the key store is a parameter. Not a question 4 match: the catch in base.py belongs to another unit | tests/provision/packages/test_direct_download.py; source/sushicore/provision/packages/direct_download.py; source/sushicore/provision/packages/base.py
test_direct_install_warns_when_the_user_path_write_is_refused | rewrite | 1 | forbidden kinds: stubs of owned functions (_add_to_user_path_windows, gh_latest_asset, download, _cmake_on_system) and the recording_console fixture, a recorder for the console port. source/sushicore/provision/_output.py has no in-memory console adapter, so the rewrite needs one there. The only test of the warning promise. Rewrite as rows over path_written in {False, True}, which also carries the next test | tests/provision/packages/test_direct_download.py; source/sushicore/provision/packages/direct_download.py; source/sushicore/provision/_output.py; tests/provision/conftest.py
test_direct_install_stays_quiet_when_the_user_path_write_lands | delete | 1 | same forbidden stubs and console recorder; its promise (no warning when the write lands) is the path_written True row of the rewrite above | tests/provision/packages/test_direct_download.py; source/sushicore/provision/packages/direct_download.py; tests/provision/conftest.py
```

### `tests/provision/packages/test_github_release.py`

```
test_every_package_request_sends_the_sushicore_agent | rewrite | 1 | forbidden kind: the recording_console fixture, a recorder for the console port with no in-memory adapter in _output.py. download() prints through the console, so the fixture is needed, but the promise is the header only. Rewrite: bind the in-memory console adapter the rewrite needs (in _output.py) and check the header alone | source/sushicore/provision/packages/github_release.py; source/sushicore/provision/packages/direct_download.py; source/sushicore/provision/system.py; source/sushicore/provision/_output.py; tests/provision/conftest.py; tests/provision/packages/test_github_release.py
test_no_module_spells_its_own_agent | rewrite | 7 | the body loops over every .py file under the package, and the oracle is a text pattern that also matches any unrelated "-installer" string. Question 7 sign: a loop in the body. Rewrite the promise (one definition, system.USER_AGENT) as rows over the request modules, or as a checker under tools/ | source/sushicore/provision/packages/github_release.py; source/sushicore/provision/system.py; tests/provision/packages/test_github_release.py
```

### `tests/provision/packages/test_gpu_stack.py`

```
test_install_gpu_stack_dispatches_through_the_registry | rewrite | 1 | forbidden kinds: DEFAULT_REGISTRY (a process-wide instance) is replaced, and _RecordingLocator stands in for the ToolkitLocator port in gpu/backend.py. Rewrite needs an InMemoryToolkitLocator in gpu/backend.py, and install_gpu_stack taking its registry as a parameter (seam for question 8) | source/sushicore/provision/packages/gpu_stack.py; source/sushicore/provision/gpu/registry.py; source/sushicore/provision/gpu/backend.py; tests/provision/packages/test_gpu_stack.py; tests/provision/test_steps/test_install_deps.py
test_install_gpu_stack_reports_no_gpu_for_an_unregistered_vendor | rewrite | 1 | forbidden kinds: DEFAULT_REGISTRY replaced and recording_console used. Only test of the return-True and exact-message promise. Rewrite as rows over the vendor key (unregistered and registered), using the registry parameter and in-memory console named above | source/sushicore/provision/packages/gpu_stack.py; source/sushicore/provision/gpu/registry.py; tests/provision/packages/test_gpu_stack.py; tests/provision/conftest.py
test_no_discrete_gpu_prints_only_without_a_known_vendor | delete | 1 | forbidden kinds: sys.platform set process-wide, the private _windows_display_adapters stubbed, shutil.which stubbed, recording_console used. The detection promise belongs to probe.py, which tests/provision/test_probe.py covers for classify_display_adapters (lines 25 and 30). The dispatch promise is the rewrite above | tests/provision/packages/test_gpu_stack.py; source/sushicore/provision/probe.py; source/sushicore/provision/packages/gpu_stack.py; tests/provision/test_probe.py
```

### `tests/provision/packages/test_linux.py`

```
test_every_manager_is_exported | rewrite | 7 | the body loops over a literal tuple of names. Rewrite as rows over the names. Overlaps only partly with the __all__ check: a manager removed from both __all__ and the module fails here alone | source/sushicore/provision/packages/__init__.py; source/sushicore/provision/packages/linux.py; tests/provision/packages/test_linux.py
test_the_exported_names_are_public_and_resolve | rewrite | 6 | the oracle is packages.__all__, the list under test. The comprehension and loop in the body also break the straight line. Rewrite against a named list of public names, with the private-name check as its own row | source/sushicore/provision/packages/__init__.py; tests/provision/packages/test_linux.py
test_the_shared_helpers_are_exported_under_public_names | rewrite | 7 | the body loops over literal helper names that the module docstring says hub uses. Rewrite as rows over those names | source/sushicore/provision/packages/__init__.py; source/sushicore/provision/packages/github_release.py; source/sushicore/provision/packages/direct_download.py; source/sushicore/provision/packages/base.py; tests/provision/packages/test_linux.py
test_dnf_translates_apt_names_and_keeps_unknown_ones | rewrite | 7 | the name joins two results (mapping, keeping unknown names) and the body is a table of inputs. Rewrite as rows, input to expected: build-essential to gcc, gcc-c++, make; ocl-icd-libopencl1 to nothing; cmake to cmake | source/sushicore/provision/packages/linux.py; tests/provision/packages/test_linux.py
test_apt_keeps_its_own_names | keep | 9 | AptManager.translate_apt is the identity: apt names are the common form | source/sushicore/provision/packages/linux.py; tests/provision/packages/test_linux.py
test_apt_is_installed_reads_the_dpkg_status | keep | 9 | the stub replaces subprocess.run, which the repository does not own, in the test of the adapter that reaches it (AptManager). Name and promise agree | source/sushicore/provision/packages/linux.py; tests/provision/packages/test_linux.py
test_apt_install_updates_then_installs_without_sudo_as_root | rewrite | 1 | forbidden stubs: linux.is_root (system.py) and linux.run (base.py) are functions the repository owns, and the recording lambda is a stand-in for the command runner. Rewrite at the process boundary: stub base.subprocess.Popen and os.geteuid; the console must be bound, and no in-memory console adapter exists in _output.py yet, so the rewrite needs one there. The empty-list test below joins it as a row | source/sushicore/provision/packages/linux.py; source/sushicore/provision/packages/base.py; source/sushicore/provision/system.py; source/sushicore/provision/_output.py; tests/provision/packages/test_linux.py
test_apt_install_of_nothing_runs_nothing | rewrite | 1 | forbidden stub: linux.run replaced by a fail-on-call function the repository owns. Its promise (an empty list runs nothing and succeeds) is tested nowhere else, so it becomes the empty-list row of the rewrite above | source/sushicore/provision/packages/linux.py; tests/provision/packages/test_linux.py
```

### `tests/provision/packages/test_vcpkg.py`

```
test_a_port_with_features_is_seen_as_installed | rewrite | 1 | forbidden kinds: the fixture replaces VcpkgManager.available, a method the repository owns, and stands in a SimpleNamespace for ProvisionConfig (config.py). Only test of the is_installed promise, so it becomes rows over the three inputs (feature list, bare name, not listed). Rewrite: a real vcpkg file under tmp_path and ProvisionSettings; only subprocess.run is stubbed, since it is outside the repository | source/sushicore/provision/packages/vcpkg.py; source/sushicore/provision/config.py; tests/provision/packages/test_vcpkg.py
test_a_bare_port_name_still_matches | delete | 1 | same forbidden fixture; its promise is the bare-name row of the rewrite above | tests/provision/packages/test_vcpkg.py; source/sushicore/provision/packages/vcpkg.py
test_a_port_that_is_not_listed_is_not_installed | delete | 1 | same forbidden fixture; its promise is the not-listed row of the rewrite above | tests/provision/packages/test_vcpkg.py; source/sushicore/provision/packages/vcpkg.py
```

### `tests/provision/packages/test_winget.py`

```
test_available_follows_the_path | keep | 9 | the stub replaces shutil.which, which the repository does not own, in the test of the adapter that reaches it. It checks the False answer only; the True answer has no test, recorded as an add | source/sushicore/provision/packages/winget.py; tests/provision/packages/test_winget.py
test_is_installed_needs_the_id_in_the_listing | rewrite | 7 | the body asserts the results of two calls with different inputs (question 7 sign). Rewrite as rows over the id and the listing. The match is a substring test, so under the current code "Git.G" reads as installed; a row for it would expose that. Reported only, no fix made | source/sushicore/provision/packages/winget.py; tests/provision/packages/test_winget.py
test_is_installed_is_false_when_winget_cannot_run | keep | 9 | the stub raises OSError from subprocess.run, which the repository does not own, in the test of the adapter that reaches it | source/sushicore/provision/packages/winget.py; tests/provision/packages/test_winget.py
test_install_runs_one_silent_command_per_package_and_reports_failure | rewrite | 1 | forbidden stand-in: winget.run (base.run, a repository function) replaced by _recorder. Two promises in one body (one command per package; failure reported). Rewrite at the Popen boundary with the in-memory console, then split | source/sushicore/provision/packages/winget.py; source/sushicore/provision/packages/base.py; source/sushicore/provision/_output.py; tests/provision/packages/test_winget.py
test_remove_uninstalls_each_package | rewrite | 1 | forbidden stand-in: winget.run replaced by _recorder. dry_run=True means base.run never executes, so the recorded list is the stub's own record, not evidence of a command. Only test of remove. Rewrite at the Popen boundary with dry_run False | source/sushicore/provision/packages/winget.py; source/sushicore/provision/packages/base.py; tests/provision/packages/test_winget.py
```

### `tests/provision/sushi_packages/test_build_tree.py`

```
test_the_name_is_stable_for_equal_input | keep | 9 | BuildTree: the name is stable for equal configurations | tests/provision/sushi_packages/test_build_tree.py; source/sushicore/provision/sushi_packages/build_tree.py
test_each_part_gives_another_folder | keep | 9 | BuildTree: a changed build type, option set or toolchain gives another folder (3 rows) | tests/provision/sushi_packages/test_build_tree.py; source/sushicore/provision/sushi_packages/build_tree.py
test_the_folder_is_pkg_and_twelve_hex_digits | rewrite | 2 | the name promises twelve hex digits; the body checks the prefix and the length only, so a non-hex tail passes; rewrite to check the digits | tests/provision/sushi_packages/test_build_tree.py; source/sushicore/provision/sushi_packages/build_tree.py
```

### `tests/provision/sushi_packages/test_closure_walk.py`

```
test_the_diamond_lists_the_runtime_once_before_blas | resize | 8 | ClosureWalk order is a decision on values, reached through files: the default read_fragment and SushiSourceLocator; the seams are the read_fragment argument (exists) and an in-memory ISourceLocator (missing); resize to small | tests/provision/sushi_packages/test_closure_walk.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/closure_walk.py; source/sushicore/provision/sushi_packages/source_locator.py
test_a_node_carries_its_cli_and_dependencies | resize | 8 | node fields come from fragments read off disk; same seams as the diamond test; small | tests/provision/sushi_packages/test_closure_walk.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/closure_walk.py; source/sushicore/provision/sushi_packages/source_locator.py
test_a_cycle_raises_naming_the_trail | resize | 8 | the cycle is decided on values; reached through files; same seams; small; the copy in test_package_resolver.py is deleted | tests/provision/sushi_packages/test_closure_walk.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/closure_walk.py; source/sushicore/provision/sushi_packages/source_locator.py
test_a_malformed_fragment_raises_a_package_error | resize | 8 | the wrapping of a reader ValueError is a decision on values; read_fragment already exists as a seam, so inject a reader that raises ValueError; small | tests/provision/sushi_packages/test_closure_walk.py; source/sushicore/provision/sushi_packages/closure_walk.py
test_the_pin_of_the_consumer_decides_the_version | rewrite | 1 | _Locator is a recorder written by the test for ISourceLocator, which the repository owns; rewrite on an in-memory locator in source_locator.py that records the version asked for | tests/provision/sushi_packages/test_closure_walk.py; source/sushicore/provision/sushi_packages/closure_walk.py; source/sushicore/provision/sushi_packages/source_locator.py
```

### `tests/provision/sushi_packages/test_compiler_check.py`

```
test_a_tree_of_the_expected_compiler_passes | rewrite | 1 | _probe is a stand-in for the Probe port; the expected identity comes from compiler_identity, the code family under test, so the oracle is not independent; rewrite with literal identities and an in-memory probe in toolchain_identity.py | tests/provision/sushi_packages/test_compiler_check.py; source/sushicore/provision/sushi_packages/compiler_check.py; source/sushicore/provision/sushi_packages/toolchain_identity.py
test_a_tree_of_another_compiler_raises_naming_both | rewrite | 1 | same stand-in probe; the expected identity is computed by compiler_identity, not a literal; rewrite with literal identities and the in-memory probe | tests/provision/sushi_packages/test_compiler_check.py; source/sushicore/provision/sushi_packages/compiler_check.py; source/sushicore/provision/sushi_packages/toolchain_identity.py
test_a_tree_with_no_cache_passes_with_one_warning | rewrite | 1 | warnings list is a recorder of the warn sink, and _probe is a stand-in; rewrite on an in-memory warn sink in compiler_check.py | tests/provision/sushi_packages/test_compiler_check.py; source/sushicore/provision/sushi_packages/compiler_check.py
```

### `tests/provision/sushi_packages/test_configure_inputs.py`

```
test_a_missing_file_hashes_as_absent | rewrite | 1 | the lambdas passed as probes stand in for the CMakeVersion and VcpkgHead ports; rewrite on in-memory probes in configure_inputs.py; the assertion is truthiness only, so absent is not checked | tests/provision/sushi_packages/test_configure_inputs.py; source/sushicore/provision/sushi_packages/configure_inputs.py
test_each_input_file_changes_the_hash | rewrite | 1 | same probe stand-ins; the file promise holds (3 rows) | tests/provision/sushi_packages/test_configure_inputs.py; source/sushicore/provision/sushi_packages/configure_inputs.py
test_the_vcpkg_head_and_the_triplet_change_the_hash | rewrite | 1 | same probe stand-in for the vcpkg head; rewrite on an in-memory vcpkg probe | tests/provision/sushi_packages/test_configure_inputs.py; source/sushicore/provision/sushi_packages/configure_inputs.py
test_only_the_minor_version_of_cmake_counts | rewrite | 1 | same probe stand-in for the CMake version; the promise holds; rewrite on an in-memory CMake probe | tests/provision/sushi_packages/test_configure_inputs.py; source/sushicore/provision/sushi_packages/configure_inputs.py
```

### `tests/provision/sushi_packages/test_consumer_build.py`

```
test_the_configure_arguments_join_the_pins_and_the_package_folders | rewrite | 1 | _Config records each request: a stand-in for the consumer config port; the package set is empty, so the package folders the name promises are never in the output; rewrite with an in-memory config adapter and a non-empty PackageSet | tests/provision/sushi_packages/test_consumer_build.py; source/sushicore/provision/sushi_packages/consumer_build.py; source/sushicore/provision/sushi_packages/package_set.py
test_the_search_path_variable_follows_the_platform | keep | 9 | search_path_variable: PATH on Windows, LD_LIBRARY_PATH elsewhere | tests/provision/sushi_packages/test_consumer_build.py; source/sushicore/provision/sushi_packages/consumer_build.py
test_saved_folders_are_read_back_and_the_tree_is_made | resize | 8 | a file write and read is a boundary, so the test belongs in medium, not small; no seam needed | tests/provision/sushi_packages/test_consumer_build.py; source/sushicore/provision/sushi_packages/consumer_build.py
test_a_file_that_is_not_a_list_of_texts_reads_as_far_as_it_can | rewrite | 1 | forbidden kind: control flow in the body, a conditional inside the expected value; the only test of this promise; rewrite as a row table with the expected value in each row, at medium | tests/provision/sushi_packages/test_consumer_build.py; source/sushicore/provision/sushi_packages/consumer_build.py
test_a_tree_without_the_file_has_no_folders | resize | 8 | reads a missing file in a small test; a file read is a boundary, so medium | tests/provision/sushi_packages/test_consumer_build.py; source/sushicore/provision/sushi_packages/consumer_build.py
test_the_folders_lead_the_path_of_the_platform | keep | 9 | RunDirs.prepend: the folders lead, the old value follows, per platform | tests/provision/sushi_packages/test_consumer_build.py; source/sushicore/provision/sushi_packages/consumer_build.py
```

### `tests/provision/sushi_packages/test_default_resolver.py`

```
test_the_public_surface_is_exactly_the_documented_names | resize | 8 | an import and a list comparison reach nothing; the file is medium but the promise is small; resize to small | tests/provision/sushi_packages/test_default_resolver.py; source/sushicore/provision/sushi_packages/__init__.py
test_default_resolver_starts_no_process | resize | 8 | patches the process-wide subprocess module; default_resolver builds GitSourceInspector, the cmake probe and the home root inside itself, so no seam exists; add the collaborators as parameters at the shell, then the test runs small with a refusing runner | tests/provision/sushi_packages/test_default_resolver.py; tests/conftest.py (provision_home, read in part); source/sushicore/provision/sushi_packages/default_resolver.py; source/sushicore/provision/sushi_packages/source_state.py; source/sushicore/provision/sushi_packages/configure_inputs.py
test_the_keep_count_is_three_by_default_and_the_environment_overrides_it | split | 3 | three promises: an unset count gives three; the variable overrides a configured count; split into two small tests | tests/provision/sushi_packages/test_default_resolver.py; source/sushicore/provision/sushi_packages/default_resolver.py
test_a_bad_keep_variable_is_refused | resize | 8 | a value check with no reach, in a medium file; small (3 rows) | tests/provision/sushi_packages/test_default_resolver.py; source/sushicore/provision/sushi_packages/default_resolver.py
```

### `tests/provision/sushi_packages/test_forced_packages.py`

```
test_without_the_marker_a_variable_is_ignored_with_one_warning | rewrite | 1 | warnings list is a recorder of the warn sink; rewrite on an in-memory sink in forced_packages.py; the store stays on disk, medium | tests/provision/sushi_packages/test_forced_packages.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/forced_packages.py; source/sushicore/provision/sushi_packages/package_store.py
test_with_the_marker_the_package_is_taken | rewrite | 1 | passes a list as the warn sink, a dummy recorder; drop it so the module's null default is used | tests/provision/sushi_packages/test_forced_packages.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/forced_packages.py
test_a_library_without_a_variable_is_not_forced | rewrite | 1 | dummy list passed as the warn sink; the only test of this promise; drop the list | tests/provision/sushi_packages/test_forced_packages.py; source/sushicore/provision/sushi_packages/forced_packages.py
test_another_toolchain_or_build_type_is_refused | rewrite | 1 | dummy list passed as the warn sink (2 rows); drop the list | tests/provision/sushi_packages/test_forced_packages.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/forced_packages.py; source/sushicore/provision/sushi_packages/package_store.py
test_a_digest_that_is_not_in_the_store_is_refused | rewrite | 1 | dummy list passed as the warn sink; drop the list | tests/provision/sushi_packages/test_forced_packages.py; source/sushicore/provision/sushi_packages/forced_packages.py
```

### `tests/provision/sushi_packages/test_key_factory.py`

```
test_the_key_composes_every_part | rewrite | 1 | identify and ListInspector are stand-ins for the compiler identity and the source inspector ports; the name ("every part") states no single promise; rewrite on in-memory adapters in toolchain_identity.py and source_state.py, one promise named | tests/provision/sushi_packages/test_key_factory.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/key_factory.py; source/sushicore/provision/sushi_packages/configure_inputs.py
test_the_sushicore_version_is_part_of_the_recipe | rewrite | 1 | same identify and ListInspector stand-ins; the promise holds; rewrite on the in-memory adapters | tests/provision/sushi_packages/test_key_factory.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/key_factory.py
test_the_compiler_is_probed_once | rewrite | 1 | calls list records each probe of the identity port: a spy of an owned port; rewrite on an in-memory identity adapter that counts its calls | tests/provision/sushi_packages/test_key_factory.py; source/sushicore/provision/sushi_packages/key_factory.py; source/sushicore/provision/sushi_packages/toolchain_identity.py
test_a_docs_only_difference_leaves_the_digest | delete | 1 | ListInspector stand-in, and the promise (a page does not change the source hash) is tested by tests/provision/sushi_packages/test_source_state.py::test_a_change_under_docs_or_in_a_page_does_not_change_the_hash, in the unit's own test file | tests/provision/sushi_packages/test_key_factory.py; tests/provision/sushi_packages/test_source_state.py; source/sushicore/provision/sushi_packages/source_state.py
```

### `tests/provision/sushi_packages/test_library_node.py`

```
test_a_node_keeps_what_the_walk_gave_it | delete | 1 | getter test of a frozen dataclass; the fields are checked through the walk in tests/provision/sushi_packages/test_closure_walk.py::test_a_node_carries_its_cli_and_dependencies | tests/provision/sushi_packages/test_library_node.py; tests/provision/sushi_packages/test_closure_walk.py; source/sushicore/provision/sushi_packages/library_node.py
test_a_node_cannot_change | keep | 9 | LibraryNode: a node cannot change after it is made | tests/provision/sushi_packages/test_library_node.py; source/sushicore/provision/sushi_packages/library_node.py
```

### `tests/provision/sushi_packages/test_link_publisher.py`

```
test_publish_points_the_link_at_the_package | rewrite | 1 | _no_lock is a stand-in for the lock factory port; rewrite on an in-memory lock adapter in package_locks.py | tests/provision/sushi_packages/test_link_publisher.py; source/sushicore/provision/sushi_packages/link_publisher.py; source/sushicore/provision/sushi_packages/package_locks.py; source/sushicore/provision/sushi_packages/stable_link.py
test_links_of_two_consumers_protect_two_digests | delete | 1 | _no_lock stand-in; protected() delegates to StableLink.targets, whose promise is tested in tests/provision/sushi_packages/test_stable_link.py::test_targets_lists_every_digest_a_link_names; the name's "one link moves" is never asserted | tests/provision/sushi_packages/test_link_publisher.py; tests/provision/sushi_packages/test_stable_link.py; source/sushicore/provision/sushi_packages/link_publisher.py; source/sushicore/provision/sushi_packages/stable_link.py
```

### `tests/provision/sushi_packages/test_package.py`

```
test_the_config_folder_keeps_the_spelling_of_the_library | keep | 9 | Package.config_folder: the folder keeps the library's own spelling; a boundary on the install tree, so medium | tests/provision/sushi_packages/test_package.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/package.py
test_an_install_without_a_config_raises | keep | 9 | Package.config_folder: a prefix with no config raises PackageError; boundary on the install tree | tests/provision/sushi_packages/test_package.py; source/sushicore/provision/sushi_packages/package.py; source/sushicore/provision/sushi_packages/package_store.py
test_run_dirs_are_bin_on_windows | keep | 9 | Package.run_dirs: Windows selects bin | tests/provision/sushi_packages/test_package.py; source/sushicore/provision/sushi_packages/package.py
test_run_dirs_are_the_existing_lib_folders_elsewhere | keep | 9 | Package.run_dirs: other platforms select the existing lib and lib64 | tests/provision/sushi_packages/test_package.py; source/sushicore/provision/sushi_packages/package.py
test_below_lists_the_packages_the_stamp_records | keep | 9 | Package.below: the stamp's below entries come back as pairs | tests/provision/sushi_packages/test_package.py; source/sushicore/provision/sushi_packages/package.py
test_the_toolchain_and_build_type_come_from_the_stamp | delete | 1 | getter test of two stamp fields; the values are checked through the refusal in tests/provision/sushi_packages/test_forced_packages.py::test_another_toolchain_or_build_type_is_refused | tests/provision/sushi_packages/test_package.py; tests/provision/sushi_packages/test_forced_packages.py; source/sushicore/provision/sushi_packages/package.py
```

### `tests/provision/sushi_packages/test_package_builder.py`

```
test_the_two_commands_run_in_order_in_the_checkout | rewrite | 1 | _Runner is a recorder of the Run port, which the module owns; rewrite on an in-memory Run adapter in package_builder.py that records and answers codes; one promise per test (order, arguments, folder) | tests/provision/sushi_packages/test_package_builder.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/package_builder.py; source/sushicore/provision/sushi_packages/build_tree.py; source/sushicore/provision/sushi_packages/compiler_check.py; source/sushicore/provision/sushi_packages/package_environment.py
test_the_environment_carries_the_compiler_and_the_packages_below | rewrite | 1 | _Runner recorder; the environment rule itself is tested in test_package_environment.py; the wiring promise is kept on the in-memory Run | tests/provision/sushi_packages/test_package_builder.py; source/sushicore/provision/sushi_packages/package_builder.py; source/sushicore/provision/sushi_packages/package_environment.py
test_a_failed_build_does_not_run_the_package_command | rewrite | 1 | _Runner recorder counts calls; rewrite on the in-memory Run that answers a code of 2 | tests/provision/sushi_packages/test_package_builder.py; source/sushicore/provision/sushi_packages/package_builder.py
test_a_failed_install_raises_with_the_command | rewrite | 1 | _Runner recorder with codes (0, 1); rewrite on the in-memory Run | tests/provision/sushi_packages/test_package_builder.py; source/sushicore/provision/sushi_packages/package_builder.py
test_the_compiler_is_checked_before_the_build_and_before_the_install | rewrite | 1 | _Runner recorder and _probe stand-in; the name says the check runs before the install, the body checks only before the build; rewrite on the in-memory Run and probe, and check both points | tests/provision/sushi_packages/test_package_builder.py; source/sushicore/provision/sushi_packages/package_builder.py; source/sushicore/provision/sushi_packages/compiler_check.py
```

### `tests/provision/sushi_packages/test_package_choices.py`

```
test_the_same_digest_twice_is_not_a_conflict | keep | 9 | PackageChoices.add: one digest chosen twice is not a conflict | tests/provision/sushi_packages/test_package_choices.py; source/sushicore/provision/sushi_packages/package_choices.py
test_two_digests_for_one_library_raise_naming_both_and_both_choosers | keep | 9 | PackageChoices.add: two digests raise, naming both digests and both choosers | tests/provision/sushi_packages/test_package_choices.py; source/sushicore/provision/sushi_packages/package_choices.py; source/sushicore/provision/sushi_packages/package_error.py
test_two_libraries_may_hold_different_digests | keep | 9 | PackageChoices.add: digests are kept per library | tests/provision/sushi_packages/test_package_choices.py; source/sushicore/provision/sushi_packages/package_choices.py
```

### `tests/provision/sushi_packages/test_package_environment.py`

```
test_the_variable_is_the_upper_case_name_with_package | merge | 4 | the same spelling promise as the test below, with other inputs; merge into rows with tests/provision/sushi_packages/test_package_environment.py::test_the_environment_carries_compiler_marker_and_prefixes | tests/provision/sushi_packages/test_package_environment.py; source/sushicore/provision/sushi_packages/package_environment.py
test_the_environment_carries_compiler_marker_and_prefixes | split | 3 | several promises that can break apart: the compiler variable, the nested marker, one variable per package, the base variables kept; split into four small tests | tests/provision/sushi_packages/test_package_environment.py; source/sushicore/provision/sushi_packages/package_environment.py
test_no_dir_variable_is_set | keep | 9 | PackageEnvironment.assemble: no _DIR variable is set | tests/provision/sushi_packages/test_package_environment.py; source/sushicore/provision/sushi_packages/package_environment.py
test_a_package_variable_of_the_parent_is_replaced | keep | 9 | PackageEnvironment.assemble: a parent's package variable for a library not below is dropped; the name says replaced, the body also checks the drop, so the name is loose | tests/provision/sushi_packages/test_package_environment.py; source/sushicore/provision/sushi_packages/package_environment.py
```

### `tests/provision/sushi_packages/test_package_error.py`

```
test_a_package_error_is_a_sushicore_error | delete | 1 | a class declaration check: trivial code, no behaviour runs, and no promise row; the same kind appears in tests/backlog/test_errors.py | tests/provision/sushi_packages/test_package_error.py; source/sushicore/provision/sushi_packages/package_error.py
test_a_conflict_is_a_package_error | delete | 1 | a class declaration check, as above | tests/provision/sushi_packages/test_package_error.py; source/sushicore/provision/sushi_packages/package_error.py
```

### `tests/provision/sushi_packages/test_package_key.py`

```
test_equal_parts_give_one_digest | keep | 9 | PackageKey.digest: equal parts give one digest | tests/provision/sushi_packages/test_package_key.py; source/sushicore/provision/sushi_packages/package_key.py
test_each_part_changes_the_digest | keep | 9 | PackageKey.digest: each part changes the digest (8 rows) | tests/provision/sushi_packages/test_package_key.py; source/sushicore/provision/sushi_packages/package_key.py
test_the_order_of_below_does_not_matter | keep | 9 | PackageKey.digest: the order of below does not matter | tests/provision/sushi_packages/test_package_key.py; source/sushicore/provision/sushi_packages/package_key.py
test_the_short_form_is_the_head_of_the_digest | rewrite | 1 | trivial code: the expected value is the body of short() written again, so the oracle is the code under test; rewrite with a literal prefix of a fixed key's digest | tests/provision/sushi_packages/test_package_key.py; source/sushicore/provision/sushi_packages/package_key.py
```

### `tests/provision/sushi_packages/test_package_locks.py`

```
test_the_lock_files_have_the_documented_names | rewrite | 1 | the taken fixture records each path asked of the LockFactory port: a recorder; rewrite on an in-memory lock adapter in package_locks.py; the checkout name is checked by prefix only | tests/provision/sushi_packages/test_package_locks.py; source/sushicore/provision/sushi_packages/package_locks.py
test_the_order_checkout_key_link_is_allowed | rewrite | 1 | same recorder; the assertion counts factory calls, which is how the code works, not what it promises; rewrite on the in-memory lock adapter | tests/provision/sushi_packages/test_package_locks.py; source/sushicore/provision/sushi_packages/package_locks.py
test_a_lock_of_a_lower_rank_after_a_higher_one_raises | rewrite | 1 | a no-op factory stand-in for the LockFactory port (3 rows); rewrite on the in-memory lock adapter | tests/provision/sushi_packages/test_package_locks.py; source/sushicore/provision/sushi_packages/package_locks.py
test_the_held_state_is_cleared_after_a_lock | rewrite | 1 | counts factory calls; the promise (a released rank can be taken again) holds without the recorder; rewrite on the in-memory lock adapter | tests/provision/sushi_packages/test_package_locks.py; source/sushicore/provision/sushi_packages/package_locks.py
```

### `tests/provision/sushi_packages/test_package_request.py`

```
test_a_request_defaults_to_the_standard_fragment_and_no_choices | delete | 1 | default-value test, a forbidden kind; the default fragment is used by tests/provision/sushi_packages/test_closure_walk.py and by the resolver tests | tests/provision/sushi_packages/test_package_request.py; tests/provision/sushi_packages/test_closure_walk.py; source/sushicore/provision/sushi_packages/package_request.py
test_two_requests_do_not_share_their_default_mappings | keep | 9 | PackageRequest: two requests do not share their default mappings (a shared mutable default would fail it) | tests/provision/sushi_packages/test_package_request.py; source/sushicore/provision/sushi_packages/package_request.py
test_a_request_resolves_every_library_unless_it_names_some | delete | 1 | default-value test, a forbidden kind; the whole-closure promise is checked by tests/provision/sushi_packages/test_package_resolver.py tests that build requests without libraries | tests/provision/sushi_packages/test_package_request.py; tests/provision/sushi_packages/test_package_resolver.py; source/sushicore/provision/sushi_packages/package_request.py
```

### `tests/provision/sushi_packages/test_package_resolver.py`

```
test_the_diamond_resolves_one_runtime_package | rewrite | 1 | Rig stand-ins: FakeBuilder records requests for the IPackageBuilder port, no_lock stands in for the lock port, ListInspector for the source inspector, lambda probes, list sinks; rewrite on in-memory builder, lock and inspector adapters in their port modules | tests/provision/sushi_packages/test_package_resolver.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/package_resolver.py; source/sushicore/provision/sushi_packages/package_builder.py; source/sushicore/provision/sushi_packages/package_locks.py; source/sushicore/provision/sushi_packages/source_state.py
test_a_changed_runtime_source_gives_blas_a_new_key | rewrite | 1 | the same Rig stand-ins; the promise holds; rewrite on the in-memory adapters | tests/provision/sushi_packages/test_package_resolver.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/package_resolver.py; source/sushicore/provision/sushi_packages/source_state.py
test_a_docs_only_difference_gives_no_new_key | rewrite | 1 | the same Rig stand-ins; counts builds on the recorder; the digest part duplicates test_source_state.py, the no-build part is resolver-level and kept; rewrite on the in-memory adapters | tests/provision/sushi_packages/test_package_resolver.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/package_resolver.py; source/sushicore/provision/sushi_packages/source_state.py
test_a_second_run_reuses_every_package_and_reports_it | rewrite | 1 | Rig stand-ins and the lines list sink, which is a recorder; rewrite on the in-memory adapters and a sink that the test reads through its own port | tests/provision/sushi_packages/test_package_resolver.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/package_resolver.py; source/sushicore/provision/sushi_packages/package_set.py
test_the_first_run_reports_built_with_seconds | rewrite | 1 | Rig stand-ins and the lines list sink; rewrite on the in-memory adapters | tests/provision/sushi_packages/test_package_resolver.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/package_resolver.py; source/sushicore/provision/sushi_packages/package_set.py
test_another_build_type_is_another_package | rewrite | 1 | Rig stand-ins; rewrite on the in-memory adapters | tests/provision/sushi_packages/test_package_resolver.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/package_resolver.py
test_the_consumer_gets_its_own_stable_link | rewrite | 1 | Rig stand-ins; the link is checked through a string search of the definitions; rewrite on the in-memory adapters | tests/provision/sushi_packages/test_package_resolver.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/package_resolver.py; source/sushicore/provision/sushi_packages/package_set.py
test_a_library_without_a_cli_and_without_a_package_is_refused | rewrite | 1 | Rig stand-ins; the refusal naming the fragment is resolver-level and not tested elsewhere; rewrite on the in-memory adapters | tests/provision/sushi_packages/test_package_resolver.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/package_resolver.py
test_a_failed_build_leaves_no_partial_folder | rewrite | 1 | FakeBuilder(fail=True) stands in for the builder port; rewrite on an in-memory builder with a failure mode in package_builder.py | tests/provision/sushi_packages/test_package_resolver.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/package_resolver.py; source/sushicore/provision/sushi_packages/package_builder.py
test_a_stale_forced_variable_is_ignored_with_a_warning | delete | 1 | Rig stand-ins; the promise (a variable without the marker is ignored with one warning) is tested by tests/provision/sushi_packages/test_forced_packages.py::test_without_the_marker_a_variable_is_ignored_with_one_warning | tests/provision/sushi_packages/test_package_resolver.py; tests/provision/sushi_packages/test_forced_packages.py; source/sushicore/provision/sushi_packages/forced_packages.py
test_one_library_at_two_keys_is_refused_naming_both | rewrite | 1 | Rig stand-ins; the forced BLAS and the source-tree runtime are wired through the resolver, which the choices test does not cover; rewrite on the in-memory adapters | tests/provision/sushi_packages/test_package_resolver.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/package_resolver.py; source/sushicore/provision/sushi_packages/package_choices.py
test_a_forced_package_of_another_build_type_is_refused | delete | 1 | Rig stand-ins; the promise (a forced package of another build type is refused) is tested by tests/provision/sushi_packages/test_forced_packages.py::test_another_toolchain_or_build_type_is_refused | tests/provision/sushi_packages/test_package_resolver.py; tests/provision/sushi_packages/test_forced_packages.py; source/sushicore/provision/sushi_packages/forced_packages.py
test_a_forced_package_is_taken_without_building | rewrite | 1 | Rig stand-ins and a recorder that counts builds; the no-build promise is resolver-level; rewrite on the in-memory builder | tests/provision/sushi_packages/test_package_resolver.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/package_resolver.py; source/sushicore/provision/sushi_packages/package_builder.py
test_a_forced_package_is_named_through_the_nested_build_link | rewrite | 1 | Rig stand-ins; rewrite on the in-memory adapters | tests/provision/sushi_packages/test_package_resolver.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/package_resolver.py; source/sushicore/provision/sushi_packages/link_publisher.py
test_a_cycle_is_refused | delete | 1 | Rig stand-ins; the promise (a cycle is refused naming the trail) is tested by tests/provision/sushi_packages/test_closure_walk.py::test_a_cycle_raises_naming_the_trail, which checks the trail this test does not | tests/provision/sushi_packages/test_package_resolver.py; tests/provision/sushi_packages/test_closure_walk.py; source/sushicore/provision/sushi_packages/closure_walk.py
test_a_filter_to_one_leaf_resolves_only_that_library | rewrite | 1 | Rig stand-ins and a recorder of the builder requests; rewrite on the in-memory adapters | tests/provision/sushi_packages/test_package_resolver.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/package_resolver.py
test_a_filter_to_a_library_with_a_dependency_resolves_both_in_order | rewrite | 1 | Rig stand-ins; rewrite on the in-memory adapters | tests/provision/sushi_packages/test_package_resolver.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/package_resolver.py
test_a_filter_name_outside_the_closure_is_refused | rewrite | 1 | Rig stand-ins; rewrite on the in-memory adapters | tests/provision/sushi_packages/test_package_resolver.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/package_resolver.py
test_no_filter_equals_the_whole_closure | rewrite | 1 | Rig stand-ins; the name says "the full list of names" but the body passes ["sushiblas"], so the claim is not tested; rewrite with the full list | tests/provision/sushi_packages/test_package_resolver.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/package_resolver.py
test_the_key_of_a_library_is_the_same_with_and_without_the_filter | rewrite | 1 | Rig stand-ins and a builder request count; rewrite on the in-memory adapters | tests/provision/sushi_packages/test_package_resolver.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/package_resolver.py
```

### `tests/provision/sushi_packages/test_package_set.py`

```
test_a_line_says_reused_or_built_with_the_short_digest | resize | 8 | ResolvedPackage.line is a function of values; the fixture installs packages on disk it does not need; build the Package values in the test, small | tests/provision/sushi_packages/test_package_set.py; source/sushicore/provision/sushi_packages/package_set.py; source/sushicore/provision/sushi_packages/package.py
test_lines_follow_the_dependency_order | resize | 8 | the order is a value check; the fixture writes to disk for no reason; small; the test also checks only the first line | tests/provision/sushi_packages/test_package_set.py; source/sushicore/provision/sushi_packages/package_set.py
test_definitions_use_the_spelling_of_each_package_and_the_closure | keep | 9 | PackageSet.definitions: one -D<Package>_DIR per package, with the library's spelling; config folders on disk make it a boundary | tests/provision/sushi_packages/test_package_set.py; source/sushicore/provision/sushi_packages/package_set.py; source/sushicore/provision/sushi_packages/package.py
test_run_dirs_list_every_package_last_first | keep | 9 | PackageSet.run_dirs: the last-resolved library first; the extraction of names by splitting path strings is brittle, but the typed names fail when the order is wrong | tests/provision/sushi_packages/test_package_set.py; source/sushicore/provision/sushi_packages/package_set.py; source/sushicore/provision/sushi_packages/package.py
test_get_and_names | delete | 1 | getter and lookup; the get() lookup is exercised on every resolution in tests/provision/sushi_packages/test_package_resolver.py | tests/provision/sushi_packages/test_package_set.py; tests/provision/sushi_packages/test_package_resolver.py; source/sushicore/provision/sushi_packages/package_set.py
```

### `tests/provision/sushi_packages/test_package_store.py`

```
test_a_folder_without_a_stamp_is_not_found | keep | 9 | PackageStore.find: a folder without a stamp is not a package; boundary on the store folder | tests/provision/sushi_packages/test_package_store.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/package_store.py
test_a_committed_package_is_found | keep | 9 | PackageStore.find: a committed package is found by its key | tests/provision/sushi_packages/test_package_store.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/package_store.py
test_a_commit_without_an_install_raises | keep | 9 | PackageStore.commit: committing an empty stage is refused | tests/provision/sushi_packages/test_package_store.py; source/sushicore/provision/sushi_packages/package_store.py
test_the_rename_is_tried_again | resize | 8 | monkeypatches the process-wide os.replace; _replace calls it directly, so no seam exists; add a rename callable to PackageStore, then the test runs small | tests/provision/sushi_packages/test_package_store.py; source/sushicore/provision/sushi_packages/package_store.py
test_prune_keeps_the_most_recently_chosen | keep | 9 | PackageStore.prune: keeps the most recently chosen packages; the last-used file is a boundary, so medium | tests/provision/sushi_packages/test_package_store.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/package_store.py
test_touching_a_package_saves_it_from_prune | keep | 9 | PackageStore.touch: a touched package is kept by prune | tests/provision/sushi_packages/test_package_store.py; source/sushicore/provision/sushi_packages/package_store.py
test_prune_never_removes_a_protected_digest | keep | 9 | PackageStore.prune: never removes a protected digest | tests/provision/sushi_packages/test_package_store.py; source/sushicore/provision/sushi_packages/package_store.py
test_prune_never_removes_a_digest_a_package_below_lists | keep | 9 | PackageStore.prune: never removes a digest that a package below lists | tests/provision/sushi_packages/test_package_store.py; tests/provision/sushi_packages/package_fakes.py; source/sushicore/provision/sushi_packages/package_store.py
test_a_deletion_goes_through_trash | resize | 8 | a spy on the process-wide os.replace; the same missing rename seam as the rename retry test; small once the seam exists | tests/provision/sushi_packages/test_package_store.py; source/sushicore/provision/sushi_packages/package_store.py
test_a_rename_that_fails_is_skipped_with_a_warning | rewrite | 1 | warnings list is a recorder of the warn sink, and os.replace is patched process-wide; rewrite on an in-memory sink and the rename seam in package_store.py | tests/provision/sushi_packages/test_package_store.py; source/sushicore/provision/sushi_packages/package_store.py
test_a_fresh_partial_of_another_process_is_left_and_a_stale_one_goes | keep | 9 | PackageStore.prune: a fresh partial of another process stays, a day-old one goes; file ages are a boundary | tests/provision/sushi_packages/test_package_store.py; source/sushicore/provision/sushi_packages/package_store.py
test_a_keep_below_one_raises | resize | 8 | the constructor raises before any file is touched; small | tests/provision/sushi_packages/test_package_store.py; source/sushicore/provision/sushi_packages/package_store.py
```

### `tests/provision/sushi_packages/test_source_locator.py`

```
test_the_configured_directory_wins_over_the_sibling | keep | 9 | SushiSourceLocator.locate: a configured directory wins over the sibling; directory lookup is a boundary | tests/provision/sushi_packages/test_source_locator.py; tests/conftest.py (provision_home, read in part); source/sushicore/provision/sushi_packages/source_locator.py
test_the_sibling_is_found | keep | 9 | SushiSourceLocator.locate: the sibling is found when nothing is configured | tests/provision/sushi_packages/test_source_locator.py; tests/conftest.py (provision_home, read in part); source/sushicore/provision/sushi_packages/source_locator.py
test_no_checkout_raises_naming_the_directory_variable | keep | 9 | SushiSourceLocator.locate: no checkout raises, naming the directory variable | tests/provision/sushi_packages/test_source_locator.py; tests/conftest.py (provision_home, read in part); source/sushicore/provision/sushi_packages/source_locator.py
```

### `tests/provision/sushi_packages/test_source_state.py`

```
test_a_change_under_docs_or_in_a_page_does_not_change_the_hash | rewrite | 1 | _Files is a stand-in lister for the ISourceInspector port, which the repository owns; rewrite on an in-memory inspector in source_state.py | tests/provision/sushi_packages/test_source_state.py; source/sushicore/provision/sushi_packages/source_state.py
test_a_changed_source_file_changes_the_hash | rewrite | 1 | _Files stand-in; rewrite on the in-memory inspector | tests/provision/sushi_packages/test_source_state.py; source/sushicore/provision/sushi_packages/source_state.py
test_a_new_source_file_changes_the_hash | rewrite | 1 | _Files stand-in; rewrite on the in-memory inspector | tests/provision/sushi_packages/test_source_state.py; source/sushicore/provision/sushi_packages/source_state.py
test_a_deleted_file_changes_the_hash | rewrite | 1 | _Files lists from disk, so a deleted file is absent from the listing and the is-file skip in describe_source never runs; rewrite with an inspector that lists the deleted path, as git does | tests/provision/sushi_packages/test_source_state.py; source/sushicore/provision/sushi_packages/source_state.py
test_the_build_folders_never_enter_the_hash | rewrite | 1 | _Files stand-in; rewrite on the in-memory inspector | tests/provision/sushi_packages/test_source_state.py; source/sushicore/provision/sushi_packages/source_state.py
test_a_package_exclude_entry_is_left_out | rewrite | 1 | _Files stand-in; rewrite on the in-memory inspector | tests/provision/sushi_packages/test_source_state.py; source/sushicore/provision/sushi_packages/source_state.py
test_a_folder_that_is_not_a_repository_raises | rewrite | 1 | _NotARepository is a stand-in that raises for the ISourceInspector port; rewrite on an in-memory inspector that can fail | tests/provision/sushi_packages/test_source_state.py; source/sushicore/provision/sushi_packages/source_state.py
test_the_built_in_exclusions | resize | 8 | is_excluded is a function of paths, with no reach; the file is medium, the promise is small | tests/provision/sushi_packages/test_source_state.py; source/sushicore/provision/sushi_packages/source_state.py
```

### `tests/provision/sushi_packages/test_stable_link.py`

```
test_the_windows_link_follows_the_newest_package | split | 3 | split: StableLink.point on Windows leaves the link on the second package; and keeps every package folder given (an "and" joining two results that can break apart) | tests/provision/sushi_packages/test_stable_link.py; source/sushicore/provision/sushi_packages/stable_link.py; source/sushicore/provision/links.py
test_the_posix_link_is_replaced_beside_the_old_one | rewrite | 1 | control flow in the body (if not _symlinks_work(...) then pytest.skip); the second result (no .new file) joins the first; rewrite with a capability marker and split by promise | tests/provision/sushi_packages/test_stable_link.py; source/sushicore/provision/sushi_packages/stable_link.py
test_the_name_has_config_and_consumer | rewrite | 7 | fixture field not used: folders supplies first and second, the test reads root only; rewrite on a plain root, after which the test is small | tests/provision/sushi_packages/test_stable_link.py; source/sushicore/provision/sushi_packages/stable_link.py
test_targets_lists_every_digest_a_link_names | keep | 9 | StableLink.targets lists the digest folder of every link of the library | tests/provision/sushi_packages/test_stable_link.py; source/sushicore/provision/sushi_packages/stable_link.py; source/sushicore/provision/links.py
test_targets_of_an_unknown_library_is_empty | rewrite | 7 | fixture fields first and second unused; rewrite with an empty root, the library folder absent; the file read keeps it medium | tests/provision/sushi_packages/test_stable_link.py; source/sushicore/provision/sushi_packages/stable_link.py
```

### `tests/provision/sushi_packages/test_toolchain_identity.py`

```
test_the_same_version_text_gives_one_identity | merge | 4 | merge with test_another_version_text_gives_another_identity into rows over version text: compiler_identity gives the same identity to the same text, and another identity to other text | tests/provision/sushi_packages/test_toolchain_identity.py; source/sushicore/provision/sushi_packages/toolchain_identity.py; source/sushicore/provision/toolchains/stamp.py
test_another_version_text_gives_another_identity | merge | 4 | merge with test_the_same_version_text_gives_one_identity into the same rows | tests/provision/sushi_packages/test_toolchain_identity.py; source/sushicore/provision/sushi_packages/toolchain_identity.py; source/sushicore/provision/toolchains/stamp.py
test_the_stamp_tag_is_joined | resize | 8 | compiler_identity: the install stamp's tag ends the identity; the tag is read from disk inside the function, so a tag or stamp-reader argument is the seam to build first, then the test runs small | tests/provision/sushi_packages/test_toolchain_identity.py; source/sushicore/provision/sushi_packages/toolchain_identity.py; source/sushicore/provision/toolchains/stamp.py
test_a_compiler_that_gives_no_identity_raises | resize | 8 | compiler_identity: a compiler that exits non-zero or prints nothing raises PackageError; the raise comes before any stamp read, tmp_path only builds a path string, so it runs small with a literal path | tests/provision/sushi_packages/test_toolchain_identity.py; source/sushicore/provision/sushi_packages/toolchain_identity.py
```

### `tests/provision/test_checks.py`

```
test_python_check_passes_on_this_interpreter | resize | 8 | checks: python_check OK on interpreter; reads sys.version_info and sys.executable of the running process; seam: version and executable passed in, small | tests/provision/test_checks.py; source/sushicore/provision/checks.py
test_tool_check_fails_with_the_fix_for_a_missing_tool | resize | 8 | checks: tool_check FAIL with fix; reaches PATH lookup of the process; seam: executable lookup passed in | tests/provision/test_checks.py; source/sushicore/provision/checks.py
test_python_module_check_finds_the_stdlib | resize | 8 | checks: python_module_check OK; reaches the process import machinery; seam: module finder passed in | tests/provision/test_checks.py; source/sushicore/provision/checks.py
test_missing_python_module_fails | resize | 8 | checks: python_module_check FAIL; reaches the process import machinery; seam: module finder passed in | tests/provision/test_checks.py; source/sushicore/provision/checks.py
test_path_check_reports_the_missing_path | resize | 8 | checks: path_check FAIL names the path; reads the file system through Path.exists; seam: existence predicate passed in | tests/provision/test_checks.py; source/sushicore/provision/checks.py
test_stamp_check_warns_on_an_unstamped_toolchain | resize | 8 | checks: stamp_check WARN; reads a directory tree on disk; seam: directory listing passed in | tests/provision/test_checks.py; source/sushicore/provision/checks.py
test_fragment_check_fails_a_dependency_whose_check_cmd_hangs | rewrite | 1 | checks: fragment_check FAIL on a hanging check_cmd; _FixedSource stands in for IDependencySource, which the repository owns and has no in-memory adapter in provision/fragments.py (rewrite needs that adapter); the test also runs a real 5 s sleep in a child process and patches the module's own _VERSION_TIMEOUT | tests/provision/test_checks.py; source/sushicore/provision/checks.py; source/sushicore/provision/fragments.py
test_fragment_check_fails_a_malformed_check_cmd | rewrite | 1 | checks: fragment_check FAIL on a malformed check_cmd; _FixedSource stand-in for IDependencySource with no in-memory adapter in provision/fragments.py | tests/provision/test_checks.py; source/sushicore/provision/checks.py; source/sushicore/provision/fragments.py
test_modules_check_passes_with_nothing_missing | resize | 8 | checks: modules_check OK on empty input; pure value logic in a medium file, so small; no seam needed | tests/provision/test_checks.py; source/sushicore/provision/checks.py
test_modules_check_fails_and_names_each_missing_module | resize | 8 | checks: modules_check FAIL names module and wanter; pure value logic, small; no seam needed | tests/provision/test_checks.py; source/sushicore/provision/checks.py
test_capability_check_fails_for_an_unsatisfied_group | rewrite | 1 | checks: capability_check FAIL for an unsatisfied group; _FixedSource stand-in for IDependencySource, no in-memory adapter in provision/fragments.py | tests/provision/test_checks.py; source/sushicore/provision/checks.py; source/sushicore/provision/fragments.py
test_capability_check_passes_when_one_member_is_present | rewrite | 1 | checks: capability_check OK with one member; _FixedSource stand-in, no in-memory adapter in provision/fragments.py | tests/provision/test_checks.py; source/sushicore/provision/checks.py; source/sushicore/provision/fragments.py
test_capability_check_passes_when_nothing_is_required | rewrite | 1 | checks: capability_check OK with no toolchain required; _FixedSource stand-in, no in-memory adapter in provision/fragments.py | tests/provision/test_checks.py; source/sushicore/provision/checks.py; source/sushicore/provision/fragments.py
test_capability_check_names_a_lone_toolchain_once | rewrite | 1 | checks: capability_check detail for a lone toolchain, two calls in one body (also a split candidate); _FixedSource stand-in, no in-memory adapter in provision/fragments.py | tests/provision/test_checks.py; source/sushicore/provision/checks.py; source/sushicore/provision/fragments.py
test_capability_check_ignores_an_optional_toolchain | rewrite | 1 | checks: capability_check ignores an optional toolchain; _FixedSource stand-in, no in-memory adapter in provision/fragments.py | tests/provision/test_checks.py; source/sushicore/provision/checks.py; source/sushicore/provision/fragments.py
test_fragment_check_passes_a_dependency_the_package_manager_reports | rewrite | 1 | checks: fragment_check OK when the package manager reports the package; _FixedSource stand-in, no in-memory adapter in provision/fragments.py | tests/provision/test_checks.py; source/sushicore/provision/checks.py; source/sushicore/provision/fragments.py
test_fragment_check_fails_a_dependency_no_package_manager_reports | rewrite | 1 | checks: fragment_check FAIL when no package manager reports it; _FixedSource stand-in, no in-memory adapter in provision/fragments.py | tests/provision/test_checks.py; source/sushicore/provision/checks.py; source/sushicore/provision/fragments.py
test_digest_check_warns_and_lists_every_unpinned_download | rewrite | 1 | checks: digest_check WARN lists unpinned downloads (also a split candidate: name list, oneapi absence, fix, required flag); _FixedSource stand-in, no in-memory adapter in provision/fragments.py | tests/provision/test_checks.py; source/sushicore/provision/checks.py; source/sushicore/provision/fragments.py
test_digest_check_passes_when_every_download_is_pinned | rewrite | 1 | checks: digest_check OK when every download is pinned; _FixedSource stand-in, no in-memory adapter in provision/fragments.py | tests/provision/test_checks.py; source/sushicore/provision/checks.py; source/sushicore/provision/fragments.py
test_digest_check_passes_where_nothing_is_downloaded | rewrite | 1 | checks: digest_check OK where nothing is downloaded; _FixedSource stand-in, no in-memory adapter in provision/fragments.py | tests/provision/test_checks.py; source/sushicore/provision/checks.py; source/sushicore/provision/fragments.py
```

### `tests/provision/test_closure.py`

```
test_a_module_with_no_dependencies_is_its_own_closure | resize | 8 | closure: resolve returns the module alone; reads fragment files and directories on disk; seam: fragment reader and locator passed in | tests/provision/test_closure.py; source/sushicore/provision/closure.py
test_a_chain_is_ordered_dependencies_first | resize | 8 | closure: resolve orders dependencies first; reads fragment files on disk; seam: fragment reader passed in | tests/provision/test_closure.py; source/sushicore/provision/closure.py
test_shared_fragments_come_first | resize | 8 | closure: shared fragments precede the module; reads fragment files on disk; seam: fragment reader passed in | tests/provision/test_closure.py; source/sushicore/provision/closure.py
test_a_missing_checkout_is_reported_with_who_wanted_it | resize | 8 | closure: missing checkout reported with its wanter; reads directories on disk; seam: locator passed in as a value table | tests/provision/test_closure.py; source/sushicore/provision/closure.py
test_a_missing_middle_module_hides_nothing_above_it | resize | 8 | closure: a missing middle module does not hide the modules above it; reads disk; seam: locator passed in | tests/provision/test_closure.py; source/sushicore/provision/closure.py
test_a_checkout_without_a_fragment_is_present_and_empty | resize | 8 | closure: a checkout with no fragment is present and contributes no pins; reads disk; seam: fragment reader passed in | tests/provision/test_closure.py; source/sushicore/provision/closure.py
test_a_cycle_raises | resize | 8 | closure: resolve raises ValueError on a cycle; reads fragment files on disk; seam: fragment reader passed in | tests/provision/test_closure.py; source/sushicore/provision/closure.py
test_a_module_without_its_own_fragment_resolves_to_shared_only | resize | 8 | closure: no own fragment resolves to shared sources only; reads disk; seam: fragment reader passed in | tests/provision/test_closure.py; source/sushicore/provision/closure.py
```

### `tests/provision/test_commands.py`

```
test_link_and_unlink_without_hub | rewrite | 1 | commands: link then unlink through the CLI registers and clears the workspace entry; recording_console spy, no in-memory adapter in provision/_output.py | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py; source/sushicore/provision/_output.py
test_link_outside_a_workspace_exits_two | rewrite | 1 | commands: link outside a workspace exits 2; recording_console spy, no in-memory adapter in provision/_output.py | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py; source/sushicore/provision/_output.py
test_doctor_filters_by_group | rewrite | 1 | commands: doctor --for exits 0; _OfflineGit stand-in for IGitClient (no in-memory adapter in provision/git_client.py); recording_console spy; the assertion (exit 0) would hold with the filter ignored, so Q2 would also fail | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py; source/sushicore/provision/git_client.py
test_doctor_rejects_an_unknown_group | rewrite | 1 | commands: unknown group exits 2 and names the groups; recording_console spy, no in-memory adapter in provision/_output.py | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py; source/sushicore/provision/_output.py
test_doctor_reports_the_module_fragment_and_toolchain_stamps | rewrite | 1 | commands: doctor rows for dependencies and toolchain stamps; patches the module's own standard_checks; recording_console spy | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py; source/sushicore/provision/module_checks.py
test_setup_dry_run_detects_the_module_fragment_and_writes_nothing | rewrite | 1 | commands: setup dry run lists the module's component and writes nothing; patches own managers_for and standard_checks; recording_console spy; _OfflineGit stand-in | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py; source/sushicore/provision/module_plan.py
test_setup_writes_the_module_sink_without_dry_run | rewrite | 1 | commands: setup writes the module config file; patches own managers_for, standard_checks and probe.resolve_local_config; _FakeAptManager stand-in for LinuxPackageManager; recording_console spy | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py; source/sushicore/provision/probe.py
test_setup_dry_run_prints_the_probed_config_and_writes_nothing | rewrite | 1 | commands: setup dry run prints the probed config; patches own functions; recording_console spy | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py; source/sushicore/provision/probe.py
test_setup_creates_a_missing_dependency_root | rewrite | 1 | commands: setup creates the missing dependency root; patches own functions; recording_console spy | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py
test_setup_exits_one_when_the_lock_is_held | rewrite | 1 | commands: setup exits 1 when the lock is held and names the pid; patches own K_LOCK_TIMEOUT; recording_console spy | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/setup_command.py
test_setup_exits_one_when_a_step_fails | rewrite | 1 | commands: setup exits 1 when a step fails; recording_console spy and own managers_for patch | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py
test_setup_builds_the_package_managers_once | rewrite | 1 | commands: managers built once; patches own managers_for and counts calls (inside of the unit); recording_console spy | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/module_plan.py
test_link_records_the_lower_cased_key | rewrite | 1 | commands: link records the lower-cased key; recording_console spy, no in-memory adapter in provision/_output.py | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py
test_unlink_removes_an_entry_written_under_the_display_name | rewrite | 1 | commands: unlink removes an entry written under the display name; recording_console spy | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py
test_setup_fails_and_installs_nothing_when_a_pinned_module_cannot_be_fetched | rewrite | 1 | commands: a pinned module that cannot be fetched fails setup and installs nothing; _Recording and _OfflineGit stand-ins; recording_console spy | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py; source/sushicore/provision/git_client.py
test_setup_fetches_a_pinned_module_and_reads_its_fragment | rewrite | 1 | commands: setup fetches a pinned module and reads its fragment; _FetchingGit stand-in for IGitClient; recording_console spy | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py; source/sushicore/provision/git_client.py
test_setup_reads_the_fragment_of_a_located_dependency | rewrite | 1 | commands: a located dependency's fragment is read; patches own managers_for; recording_console spy | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py
test_setup_rejects_an_unknown_toolchain_before_the_lock | rewrite | 1 | commands: unknown toolchain exits 2 before the lock; recording_console spy | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py
test_setup_selects_the_first_declared_toolchain_when_none_is_present | rewrite | 1 | commands: first declared toolchain selected; patches InstallPipeline.run and probe.toolchain_status (own); recording_console spy | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/pipeline.py; source/sushicore/provision/probe.py
test_setup_selects_nothing_when_a_toolchain_is_present | rewrite | 1 | commands: nothing selected when a toolchain is present; patches InstallPipeline.run and probe.toolchain_status (own); recording_console spy | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/pipeline.py; source/sushicore/provision/probe.py
test_uses_base_adds_the_shared_fragment | rewrite | 1 | commands: uses_base adds the shared fragment's rows; patches own managers_for; recording_console spy | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py
test_doctor_reports_a_missing_module_and_keeps_running | rewrite | 1 | commands: missing module reported and doctor keeps running; patches own standard_checks; recording_console spy | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py; source/sushicore/provision/module_checks.py
test_a_binary_install_registers_doctor_alone | rewrite | 1 | commands: a binary install registers doctor alone; recording_console requested and the _OfflineGit stand-in constructed; the registration is worth keeping, rewrite without the spy | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py
test_the_panel_is_set_on_every_command | rewrite | 1 | commands: every command carries the panel; recording_console requested; rewrite without the spy | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py
test_doctor_agrees_with_the_inventory_on_a_package_the_manager_holds | rewrite | 1 | commands: doctor passes a dependency whose package the manager holds; patches own standard_checks and managers_for; recording_console spy | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py; source/sushicore/provision/module_plan.py
test_every_command_help_carries_examples | rewrite | 1 | commands: each command's help ends with examples naming the program; recording_console requested; rewrite without the spy | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py
test_doctor_lists_the_downloads_with_no_pinned_digest | rewrite | 1 | commands: download digest row lists unpinned downloads; patches own standard_checks; recording_console spy | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py; source/sushicore/provision/module_checks.py
test_setup_stops_before_fetching_when_two_pins_conflict | rewrite | 1 | commands: a pin conflict stops setup before any clone; _Recording git stand-in; recording_console spy; own managers_for patch | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py; source/sushicore/provision/git_client.py
test_setup_exits_two_and_installs_nothing_when_an_unpinned_module_is_missing | rewrite | 1 | commands: unpinned missing module exits 2 and installs nothing; _NoCloneGit and _Recording stand-ins; recording_console spy | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py; source/sushicore/provision/git_client.py
test_doctor_warns_on_an_unpinned_module | rewrite | 1 | commands: unpinned module warning row; patches own standard_checks; recording_console spy | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py
test_link_and_unlink_each_end_with_one_result_event | rewrite | 1 | commands: link and unlink each end with one result event; recording_console spy; overlaps the result-event tests below, merge candidate | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py
test_a_failed_link_still_ends_with_a_failing_result_event | rewrite | 1 | commands: failed link ends with a failing result event; recording_console spy; merge candidate with the result-event tests | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py
test_setup_that_stops_early_ends_with_a_failing_result_event | rewrite | 1 | commands: early setup stop ends with a failing result event; recording_console spy; merge candidate | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py
test_doctor_ends_with_exactly_one_result_event_carrying_its_checks | rewrite | 1 | commands: doctor ends with exactly one result carrying checks; patches own standard_checks; recording_console spy | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py; source/sushicore/provision/module_checks.py
test_the_doctor_help_lists_the_check_groups | rewrite | 1 | commands: doctor help lists the groups; recording_console requested; rewrite without the spy | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py
test_a_group_a_module_contributes_is_accepted_and_listed | rewrite | 1 | commands: a module's group is accepted and listed; patches own standard_checks; recording_console spy | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py; source/sushicore/provision/module_checks.py
test_setup_accepts_the_short_form_of_yes | rewrite | 1 | commands: setup accepts -y; recording_console requested; rewrite without the spy | tests/provision/test_commands.py; tests/provision/conftest.py; source/sushicore/provision/commands.py
```

### `tests/provision/test_config.py`

```
test_every_config_attribute_provision_reads_is_declared | rewrite | 1 | config: undeclared cfg attribute read by provision; a small test reads every source file of the package (forbidden for small); a static scan belongs in a tools/ checker with its own test; rewrite as that checker | tests/provision/test_config.py; source/sushicore/provision/config.py
test_the_package_keep_count_defaults_to_three | rewrite | 1 | config: package_keep defaults to 3; default-value test (forbidden); no other test checks the default, and the store prune reads it (source/sushicore/provision/sushi_packages/package_store.py); rewrite to test prune keeps the default count | tests/provision/test_config.py; source/sushicore/provision/config.py; source/sushicore/provision/sushi_packages/package_store.py; tests/test_stack_config.py
```

### `tests/provision/test_doctor.py`

```
test_required_failure_sets_exit_code_one | keep | 9 | doctor: required failure exits 1 | tests/provision/test_doctor.py; source/sushicore/provision/doctor.py
test_optional_failure_only_warns | keep | 9 | doctor: optional failure exits 0 | tests/provision/test_doctor.py; source/sushicore/provision/doctor.py
test_group_filter_runs_only_that_group | keep | 9 | doctor: group filter runs only its group; a mutant that ignores the filter exits 1 | tests/provision/test_doctor.py; source/sushicore/provision/doctor.py
test_a_raising_check_is_a_failure_and_the_rest_still_run | split | 3 | doctor: a raising check is a failure; the rest still run; the name joins two results that break apart, so two tests | tests/provision/test_doctor.py; source/sushicore/provision/doctor.py
test_render_prints_a_table_and_a_result | rewrite | 1 | doctor: render prints table then result; recording_console is a spy written by tests/provision/conftest.py for the repository's console port, no in-memory adapter in provision/_output.py; rewrite with that adapter | tests/provision/test_doctor.py; tests/provision/conftest.py; source/sushicore/provision/doctor.py; source/sushicore/provision/_output.py
test_json_state_matches_the_table_for_a_non_required_failure | rewrite | 1 | doctor: table row and payload agree for an optional failure; recording_console spy, no in-memory adapter in provision/_output.py; overlaps the plain-run test below, merge candidate | tests/provision/test_doctor.py; tests/provision/conftest.py; source/sushicore/provision/doctor.py; source/sushicore/provision/_output.py
test_optional_failure_in_a_plain_run_warns_and_exits_zero | rewrite | 1 | doctor: optional failure warns in a plain run; recording_console spy, no in-memory adapter in provision/_output.py; overlaps the json-state test, merge candidate | tests/provision/test_doctor.py; tests/provision/conftest.py; source/sushicore/provision/doctor.py; source/sushicore/provision/_output.py
test_optional_failure_in_a_named_group_fails_and_exits_one | rewrite | 1 | doctor: optional failure fails when its group is named; recording_console spy, no in-memory adapter in provision/_output.py; also several promises in one body, split after the rewrite | tests/provision/test_doctor.py; tests/provision/conftest.py; source/sushicore/provision/doctor.py; source/sushicore/provision/_output.py
test_required_failure_is_unaffected_by_the_group_filter | keep | 9 | doctor: a required failure exits 1 under any group filter | tests/provision/test_doctor.py; source/sushicore/provision/doctor.py
```

### `tests/provision/test_doctor_command.py`

```
test_a_binary_install_runs_the_python_check_and_reports_its_payload | rewrite | 1 | doctor_command: binary install runs the python check and reports the payload; local _Console stands in for the repository's console, no in-memory adapter in provision/_output.py; the python check reads the running interpreter | tests/provision/test_doctor_command.py; source/sushicore/provision/module_provision.py
test_the_run_draws_the_table_once_and_leaves_the_result_to_the_caller | rewrite | 1 | doctor_command: one table per run; local _Console stand-in, no in-memory adapter in provision/_output.py | tests/provision/test_doctor_command.py; source/sushicore/provision/module_provision.py
```

### `tests/provision/test_download_verifier/test_downloads_are_verified.py`

```
test_a_tool_archive_with_the_wrong_digest_is_not_extracted | rewrite | 1 | stubs of repository functions (dd.download, dd.gh_latest_asset, dd._cmake_on_system, dd._add_to_user_path_windows, dd._install_* by name) and a recording_console spy; rewrite through an injected download transport, carries: a mismatching archive is not extracted | tests/provision/test_download_verifier/test_downloads_are_verified.py; tests/provision/conftest.py; tests/conftest.py; source/sushicore/provision/packages/direct_download.py (def list); source/sushicore/provision/download_verifier.py
test_a_tool_archive_with_the_pinned_digest_installs | rewrite | 1 | same stubs and spy; rewrite through the transport seam, carries: a matching archive installs and is not unverified | (same files)
test_a_tool_archive_with_no_digest_installs_and_is_named | rewrite | 1 | same stubs and spy; rewrite, carries: an unpinned archive installs and is named | (same files)
test_a_git_installer_with_the_wrong_digest_is_not_run | rewrite | 1 | stubs dd.gh_latest_asset, dd.download, dd.subprocess.run and a recording_console spy; rewrite, carries: a mismatching Git installer is not launched | (same files)
test_a_git_installer_with_the_pinned_digest_is_run | rewrite | 1 | same stubs and spy; rewrite, carries: a matching Git installer is launched once | (same files)
test_an_intel_llvm_bundle_with_the_wrong_digest_is_not_extracted | rewrite | 1 | stubs intel_llvm.gh_latest_release_asset, intel_llvm.download, intel_llvm._extract_tar_gz (private) and a recording_console spy; rewrite, carries: a mismatching bundle is not extracted | (same files)
test_an_intel_llvm_bundle_with_the_pinned_digest_is_extracted | rewrite | 1 | same stubs and spy; rewrite, carries: a matching bundle is extracted once | (same files)
test_an_llvm_installer_with_the_wrong_digest_is_not_run | rewrite | 1 | stubs adaptivecpp.gh_tagged_asset, adaptivecpp.download, adaptivecpp.subprocess.run, calls private adaptivecpp._vendor_llvm_windows, and a recording_console spy; rewrite, carries: a mismatching LLVM installer is not launched | (same files)
test_an_llvm_installer_with_the_pinned_digest_is_run | rewrite | 1 | same stubs and spy; rewrite, carries: a matching LLVM installer is launched once | (same files)
test_a_oneapi_installer_with_the_wrong_digest_is_not_returned | rewrite | 1 | stubs oneapi.Path.home (process-wide) and oneapi.subprocess.run, plus a recording_console spy; rewrite, carries: a mismatching oneAPI installer is removed and refused | (same files)
test_a_oneapi_installer_left_by_an_earlier_run_is_verified_too | rewrite | 1 | same stubs and spy; rewrite, carries: a leftover installer is verified before reuse | (same files)
test_a_oneapi_installer_with_the_pinned_digest_is_returned | rewrite | 1 | same stubs and spy; rewrite, carries: a matching oneAPI installer is returned | (same files)
```

### `tests/provision/test_download_verifier/test_verifier.py`

```
test_a_pinned_download_that_matches_passes_and_is_not_reported | keep | 9 | DownloadVerifier.verify: a matching pin passes and reports nothing | tests/provision/test_download_verifier/test_verifier.py; tests/conftest.py; source/sushicore/provision/download_verifier.py
test_a_pinned_download_that_differs_raises_and_is_deleted | keep | 9 | DownloadVerifier.verify: a file whose digest differs from its pin raises DigestMismatchError and is deleted (refusal and removal are one outcome) | (same files)
test_an_unpinned_download_passes_and_is_warned_about_by_name | keep | 9 | DownloadVerifier.verify: an unpinned name passes, is named in one warning, and is listed once per run | (same files)
test_an_unpinned_download_is_reported_once_per_run | keep | 9 | DownloadVerifier.verify: an unpinned name passes, is named in one warning, and is listed once per run | (same files)
test_verify_download_goes_through_the_bound_verifier | keep | 9 | verify_download: checks against the verifier the run bound | (same files)
test_unbinding_leaves_a_verifier_that_pins_nothing | keep | 9 | verify_download: with no run bound a download passes and is reported | (same files)
test_unpinned_downloads_lists_the_tools_windows_always_fetches | rewrite | 1 | constant oracle: the expected list is the K_TOOL_DOWNLOADS table read back, a test of a constant; rewrite with the four tool names as the named oracle, merged with the leaves-out rows | (same files)
test_unpinned_downloads_lists_a_declared_toolchain_with_no_digest | resize | 8 | unpinned_downloads: a declared toolchain with no digest is listed and an undeclared one is not; pure function on values, so small | tests/provision/test_download_verifier/test_verifier.py; source/sushicore/provision/download_verifier.py
test_unpinned_downloads_leaves_out_what_is_pinned | resize | 8 | unpinned_downloads: leaves out a download pinned for the platform; pure function on values, so small | (same files)
test_unpinned_downloads_on_linux_names_only_the_declared_bundle | resize | 8 | unpinned_downloads: on Linux names only the declared bundle; pure function on values, so small | (same files)
test_every_download_name_is_listed_for_some_platform | delete | 1 | test of constants: a hard-coded set of seven names compared with the two tables; the names are exercised by name in test_downloads_are_verified.py | tests/provision/test_download_verifier/test_verifier.py; source/sushicore/provision/download_verifier.py; tests/provision/test_download_verifier/test_downloads_are_verified.py
```

### `tests/provision/test_fragments/test_merge.py`

```
test_a_feature_set_survives_a_plainer_declaration | delete | 1 | private name _merge; the feature survival is tested through the public path in test_the_aggregation_keeps_the_feature_across_two_fragments in the same file | tests/provision/test_fragments/test_merge.py; source/sushicore/provision/fragments.py
test_the_order_of_the_two_does_not_decide | rewrite | 1 | private name _merge; the order promise is only here; rewrite through TomlDependencySource with the two files in both orders | tests/provision/test_fragments/test_merge.py; tests/conftest.py; tests/provision/conftest.py; source/sushicore/provision/fragments.py
test_required_by_one_is_required | delete | 1 | private name _merge; the required-OR promise is tested through the public path in test_the_aggregation_keeps_the_feature_across_two_fragments (asserts required True) | (same files)
test_the_module_that_requires_it_owns_it | rewrite | 1 | private name _merge; the optional-first order is only here; rewrite through the public path with the required declarer second | (same files)
test_gpu_only_holds_only_when_both_say_so | rewrite | 1 | private name _merge; only test of the gpu_only AND; rewrite through TomlDependencySource | (same files)
test_two_different_check_commands_are_reported | rewrite | 1 | private name _merge; warning is routed to the console, so the rewrite needs the console's in-memory adapter (absent in source/sushicore/provision/_output.py); carries: a differing check_cmd is named | (same files)
test_ports_of_different_names_both_survive | rewrite | 1 | private name _merge_ports; carries: the union per port across names; rewrite through TomlDependencySource | (same files)
test_features_from_both_sides_are_collected | rewrite | 1 | private name _merge_ports; carries: features from both sides are collected; rewrite through TomlDependencySource | (same files)
test_the_aggregation_keeps_the_feature_across_two_fragments | rewrite | 1 | recording_console spy bound but unused here (no warning is raised); the promise is the only public-path test of feature union; rewrite with the fixture dropped | (same files)
test_a_digest_declared_by_one_module_survives | rewrite | 1 | private name _merge; carries: a digest pinned by one module survives | (same files)
test_digests_for_different_platforms_are_both_kept | rewrite | 1 | private name _merge; carries: digests for two platforms are both kept | (same files)
test_two_different_digests_for_one_platform_are_reported | rewrite | 1 | private name _merge; warning routed to the console (no in-memory console adapter in _output.py); carries: two digests for one platform are named | (same files)
```

### `tests/provision/test_fragments/test_owner_order.py`

```
test_shared_comes_first_then_dependency_order | rewrite | 1 | stand-in MemorySource for the repository's IDependencySource interface; rewrite with TomlDependencySource over tmp files, or an in-memory source added to source/sushicore/provision/fragments.py | tests/provision/test_fragments/test_owner_order.py; source/sushicore/provision/fragments.py
test_ties_keep_input_order | rewrite | 1 | stand-in MemorySource for IDependencySource; same rewrite | (same files)
test_a_cycle_is_refused | rewrite | 1 | stand-in MemorySource for IDependencySource; same rewrite | (same files)
```

### `tests/provision/test_fragments/test_toml_source.py`

```
test_source_reads_only_the_files_it_is_given | rewrite | 1 | recording_console bound by the fixture and never read; the path prints nothing, so the fixture is dropped; carries: reads only the files given and owns each dependency by its owner | tests/provision/test_fragments/test_toml_source.py; tests/provision/conftest.py; source/sushicore/provision/fragments.py; source/sushicore/provision/_output.py
test_same_named_deps_merge_across_files | rewrite | 1 | recording_console fixture the path does not use; carries: same-named dependencies merge across files | (same files)
test_digests_returns_the_pins_for_one_platform | rewrite | 1 | recording_console fixture the path does not use; carries: digests names only the pins of the platform | (same files)
```

### `tests/provision/test_git_client.py`

```
test_clone_tag_runs_a_shallow_single_tag_clone | rewrite | 1 | git_client: clone argv is shallow, single tag; patches the module's own run function; GitClient takes no injected runner, so rewrite needs that seam | tests/provision/test_git_client.py; source/sushicore/provision/git_client.py
test_clone_tag_reports_a_failed_clone | rewrite | 1 | git_client: nonzero exit is a failed clone; patches the module's own run function; needs the same runner seam | tests/provision/test_git_client.py; source/sushicore/provision/git_client.py
test_head_returns_the_lower_case_commit | rewrite | 5 | git_client: head returns lower-cased rev-parse output; patches subprocess.run, so a change of how head runs git breaks it; rewrite against a real git repository in a temporary folder | tests/provision/test_git_client.py; source/sushicore/provision/git_client.py
test_head_is_empty_when_git_fails_or_is_missing | rewrite | 5 | git_client: head is '' on failure or missing git; patches subprocess.run (inside of the unit); rewrite against a real repository and a missing executable | tests/provision/test_git_client.py; source/sushicore/provision/git_client.py
```

### `tests/provision/test_home.py`

```
test_default_root_is_in_the_user_home | resize | 8 | home: default root is under the user home; reads the process environment and Path.home; seam: environment mapping and home directory passed in | tests/provision/test_home.py; source/sushicore/provision/home.py
test_env_var_wins_and_is_expanded_and_absolute | resize | 8 | home: env var wins, expanded and absolute; reads environment and working directory; seam: environment and cwd passed in | tests/provision/test_home.py; source/sushicore/provision/home.py
test_bound_root_wins_over_env | resize | 8 | home: bound provider wins over env; reads module-level bound state and environment; seam: explicit root argument | tests/provision/test_home.py; source/sushicore/provision/home.py; tests/provision/conftest.py
test_subdirectories_hang_off_the_root | resize | 8 | home: subdirectories are under the root; reads environment through root(); seam: root passed in | tests/provision/test_home.py; source/sushicore/provision/home.py; tests/provision/conftest.py
test_no_legacy_root_outside_a_workspace | resize | 8 | home: no legacy root outside a workspace; reads working directory and environment; seam: workspace probe passed in | tests/provision/test_home.py; source/sushicore/provision/home.py; tests/provision/conftest.py
test_workspace_dependencies_is_a_legacy_root | resize | 8 | home: workspace dependencies folder is a legacy root; reads disk and cwd; seam: workspace probe passed in | tests/provision/test_home.py; source/sushicore/provision/home.py; tests/provision/conftest.py
test_legacy_env_override_is_a_legacy_root | resize | 8 | home: legacy env override is a legacy root; reads environment and disk; seam: environment mapping passed in | tests/provision/test_home.py; source/sushicore/provision/home.py; tests/provision/conftest.py
test_the_bound_root_is_never_its_own_legacy_root | resize | 8 | home: bound root is never its own legacy root; reads module state, cwd and disk; seam: explicit root and workspace passed in | tests/provision/test_home.py; source/sushicore/provision/home.py; tests/provision/conftest.py
test_an_ordinary_directory_is_removable | resize | 8 | home: ordinary directory is removable; reads disk markers; seam: marker probe passed in | tests/provision/test_home.py; source/sushicore/provision/home.py
test_the_users_home_directory_is_refused | resize | 8 | home: user home refused; reads Path.home of the process; seam: home directory passed in | tests/provision/test_home.py; source/sushicore/provision/home.py
test_a_filesystem_anchor_is_refused | resize | 8 | home: filesystem anchor refused; pure on the path value; seam: none needed beyond the value, small | tests/provision/test_home.py; source/sushicore/provision/home.py
test_the_current_directory_is_refused | resize | 8 | home: current directory refused; reads cwd; seam: cwd passed in | tests/provision/test_home.py; source/sushicore/provision/home.py
test_an_ancestor_of_the_current_directory_is_refused | resize | 8 | home: ancestor of cwd refused; reads cwd; seam: cwd passed in | tests/provision/test_home.py; source/sushicore/provision/home.py
test_a_directory_holding_a_git_marker_is_refused | resize | 8 | home: directory holding a git marker refused; reads disk marker; seam: marker probe passed in | tests/provision/test_home.py; source/sushicore/provision/home.py
test_a_directory_holding_a_workspace_marker_is_refused | resize | 8 | home: directory holding a workspace marker refused; reads disk marker; seam: marker probe passed in | tests/provision/test_home.py; source/sushicore/provision/home.py
test_env_var_with_tilde_is_expanded | resize | 8 | home: env var with tilde expanded; reads HOME, USERPROFILE and environment; seam: environment mapping and home passed in | tests/provision/test_home.py; source/sushicore/provision/home.py
test_found_vcpkg_dir_prefers_an_existing_legacy_tree | resize | 8 | home: found vcpkg dir prefers an existing legacy tree; reads environment and disk; seam: environment and probe passed in | tests/provision/test_home.py; source/sushicore/provision/home.py
test_found_vcpkg_dir_defaults_to_the_current_root | resize | 8 | home: found vcpkg dir defaults to the current root; reads environment through root(); seam: root passed in | tests/provision/test_home.py; source/sushicore/provision/home.py; tests/provision/conftest.py
test_sources_dir_is_under_the_root | resize | 8 | home: sources dir under the root; reads environment through root(); seam: root passed in | tests/provision/test_home.py; source/sushicore/provision/home.py; tests/provision/conftest.py
```

### `tests/provision/test_integrity.py`

```
test_sha256_of_returns_the_lower_case_hex_digest | keep | 9 | integrity: sha256_of is the lower-case digest of the file bytes; the file read is the boundary, so medium is right | tests/provision/test_integrity.py; source/sushicore/provision/integrity.py
test_verify_accepts_a_file_with_the_expected_digest | keep | 9 | integrity: matching digest raises nothing | tests/provision/test_integrity.py; source/sushicore/provision/integrity.py
test_verify_accepts_an_upper_case_expected_digest | keep | 9 | integrity: expected digest compared without case | tests/provision/test_integrity.py; source/sushicore/provision/integrity.py
test_verify_raises_and_names_the_file_and_both_digests | keep | 9 | integrity: mismatch error carries the file, expected and actual digests; one error, one promise | tests/provision/test_integrity.py; source/sushicore/provision/integrity.py
test_the_mismatch_reaches_the_entry_point_as_a_sushicore_error | keep | 9 | integrity: mismatch is a SushiCoreError, which the entry point prints as one line | tests/provision/test_integrity.py; source/sushicore/provision/integrity.py
test_verify_leaves_the_file_in_place | keep | 9 | integrity: a refused file is left unchanged on disk | tests/provision/test_integrity.py; source/sushicore/provision/integrity.py
```

### `tests/provision/test_link_command.py`

```
test_link_refuses_a_path_that_is_not_a_workspace_and_writes_nothing | rewrite | 1 | link_command: refusal writes nothing; local _Console stand-in for the repository's console, no in-memory adapter in provision/_output.py | tests/provision/test_link_command.py; source/sushicore/provision/link_command.py; source/sushicore/provision/module_provision.py
test_link_puts_the_old_link_back_when_the_registry_write_fails | rewrite | 1 | link_command: failed registry write restores the old link; patches the module's own write_module; _Console stand-in; rewrite needs an injected registry writer | tests/provision/test_link_command.py; source/sushicore/provision/link_command.py; source/sushicore/provision/module_provision.py
test_link_leaves_no_link_when_the_first_registry_write_fails | rewrite | 1 | link_command: first failed registry write leaves no link; patches the module's own write_module; _Console stand-in; rewrite needs an injected registry writer | tests/provision/test_link_command.py; source/sushicore/provision/link_command.py; source/sushicore/provision/module_provision.py
test_the_config_folder_comes_from_the_module | rewrite | 1 | link_command: link and unlink use the module's config folder; _Console stand-in, no in-memory adapter in provision/_output.py | tests/provision/test_link_command.py; source/sushicore/provision/link_command.py; source/sushicore/provision/module_provision.py
```

### `tests/provision/test_links.py`

```
test_link_resolves_to_target_contents | keep | 9 | links: a directory link shows target contents and names its target | tests/provision/test_links.py; source/sushicore/provision/links.py
test_remove_keeps_target_contents | keep | 9 | links: removing a link keeps the target's files | tests/provision/test_links.py; source/sushicore/provision/links.py
test_remove_refuses_a_real_directory | keep | 9 | links: a real directory is never removed as a link | tests/provision/test_links.py; source/sushicore/provision/links.py
test_make_refuses_an_existing_path | keep | 9 | links: a link is not made over an existing path | tests/provision/test_links.py; source/sushicore/provision/links.py
test_plain_directory_is_not_a_link | keep | 9 | links: a plain directory is not a link | tests/provision/test_links.py; source/sushicore/provision/links.py
test_missing_path_is_not_a_link | keep | 9 | links: an absent path is not a link | tests/provision/test_links.py; source/sushicore/provision/links.py
test_link_to_a_removed_target_is_still_a_link | keep | 9 | links: a link whose target is gone is still seen and removable | tests/provision/test_links.py; source/sushicore/provision/links.py
test_junction_is_recognised_by_its_reparse_tag | keep | 9 | links: a junction is recognised by its reparse tag on Windows; skipped elsewhere by skipif | tests/provision/test_links.py; source/sushicore/provision/links.py
```

### `tests/provision/test_lock.py`

```
test_lock_is_released_on_exit | keep | 9 | lock: lock is released on exit; OS file lock is the boundary | tests/provision/test_lock.py; source/sushicore/provision/lock.py
test_second_holder_times_out_naming_the_pid | rewrite | 1 | lock: second holder times out naming the pid; waits 0.3 s of real wall-clock time (forbidden for medium); rewrite with an injected clock held by the lock module, so no real wait | tests/provision/test_lock.py; source/sushicore/provision/lock.py
test_lock_with_garbage_content_does_not_block | keep | 9 | lock: garbage holder content does not block acquisition | tests/provision/test_lock.py; source/sushicore/provision/lock.py
test_lock_creates_its_parent_directory | keep | 9 | lock: missing parent folder is created | tests/provision/test_lock.py; source/sushicore/provision/lock.py
test_a_failing_pid_write_closes_the_descriptor | rewrite | 5 | lock: descriptor closed after a failed pid write; patches os.close and os.write and asserts the count of closes, which is inside of the unit; rewrite against the public promise (the lock file is usable again after the failure, which the test already checks) | tests/provision/test_lock.py; source/sushicore/provision/lock.py
test_an_interrupt_while_polling_closes_the_descriptor | rewrite | 5 | lock: descriptor closed after an interrupt; patches time.sleep of the process and counts closes, inside of the unit; rewrite against the public promise (re-acquire after interrupt), with the clock seam from the timeout rewrite | tests/provision/test_lock.py; source/sushicore/provision/lock.py
test_a_failing_unlock_still_closes_the_descriptor | rewrite | 1 | lock: unlock failure still propagates; patches the module's own _unlock function (forbidden replacement of an owned function); rewrite needs an injected unlock | tests/provision/test_lock.py; source/sushicore/provision/lock.py
```

### `tests/provision/test_migrate.py`

```
test_plan_counts_files_and_bytes_per_component | resize | 8 | migrate: plan counts files and bytes per component; decides on directory listing from disk; seam: a file lister passed to plan | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
test_plan_reports_one_volume_for_two_folders_side_by_side | resize | 8 | migrate: same_volume and enough_space for siblings; reads the volume of both folders; seam: volume id passed in | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
test_plan_rejects_a_name_already_in_the_target | resize | 8 | migrate: plan refuses a component name already in the target; reads the target listing; seam: listing passed in | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
test_plan_ignores_lock_and_registry_in_the_target | resize | 8 | migrate: lock and registry in the target are not collisions; reads the target listing; seam: listing passed in | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
test_plan_rejects_a_target_inside_the_old_root | resize | 8 | migrate: plan refuses a target inside the old root; decision on path values, reached through plan's disk reads; seam: listing passed in, small | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
test_plan_rejects_a_missing_old_root | resize | 8 | migrate: plan refuses a missing old root; reads disk existence; seam: existence predicate passed in | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
test_plan_rejects_an_old_root_linked_elsewhere | resize | 8 | migrate: plan refuses a link as the old root; reads link state on disk; seam: link predicate passed in | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py; source/sushicore/provision/links.py
test_migrate_renames_everything_and_links_the_old_path | split | 3 | migrate: same-volume run renames each component and links the old path; the name joins the moves and the link, which can break apart, so two tests | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py; source/sushicore/provision/links.py
test_migrate_copies_everything_and_links_the_old_path | split | 3 | migrate: cross-volume run copies each component and keeps the old tree aside, plus the link; two results that can break apart | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py; source/sushicore/provision/links.py
test_migrate_refuses_when_space_is_short | keep | 9 | migrate: copy refused with both numbers when the target is too small; disk_usage patch is an external stub | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
test_migrate_reports_already_migrated_and_changes_nothing | keep | 9 | migrate: a second run is a no-op with a report; one promise (idempotent second run) | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
test_interrupted_copy_resumes_without_recopying_finished_components | rewrite | 5 | migrate: a resumed copy does not recopy finished components; counts copytree calls, which is inside of the unit; rewrite against the public promise (the partial folder and the copied bytes after resume) | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
test_verify_failure_stops_before_the_swap_and_leaves_old_untouched | rewrite | 1 | migrate: verify failure stops before the swap; patches the module's own _verify_component (forbidden replacement of an owned function); rewrite needs a verifier passed in | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
test_copy_with_a_missing_file_fails_verification | keep | 9 | migrate: a copy that lost a file fails verification; copytree stub is an external fault injection | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
test_unreadable_file_stops_the_copy_before_the_swap | keep | 9 | migrate: unreadable file stops the copy before the swap, no partial left; external copytree fault | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
test_rename_of_a_component_in_use_names_it_and_keeps_the_journal | keep | 9 | migrate: a rename refused for an open file names the component and keeps the journal; external os.rename fault | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
test_rollback_after_a_refused_rename_restores_the_original_tree | keep | 9 | migrate: rollback after refused rename restores the tree | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
test_interrupted_rename_run_resumes_from_the_journal | keep | 9 | migrate: an interrupted same-volume run resumes from the journal | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
test_rollback_after_success_restores_the_original_tree | keep | 9 | migrate: rollback after success restores the original tree | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
test_rollback_after_a_copy_restores_the_original_tree | keep | 9 | migrate: rollback after copy restores the original tree | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
test_rollback_after_an_interrupted_copy_restores_the_original_tree | keep | 9 | migrate: rollback after an interrupted copy restores the tree; copytree fault is external | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
test_rollback_never_deletes_the_only_copy | keep | 9 | migrate: rollback refuses to delete the only copy | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
test_rollback_without_a_journal_reports_nothing_to_do | keep | 9 | migrate: rollback without a journal reports nothing to roll back | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
test_rollback_skips_the_steps_another_program_recorded | keep | 9 | migrate: rollback leaves journal steps this module does not know | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
test_finalize_deletes_the_aside_copy_and_rollback_then_has_nothing | split | 3 | migrate: finalize deletes the aside copy, closes the journal, and a later rollback has nothing; three results that can break apart | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
test_finalize_refuses_before_migration_and_deletes_nothing | keep | 9 | migrate: finalize refuses a non-link and deletes nothing; one outcome | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
test_finalize_refuses_a_second_time | keep | 9 | migrate: a second finalize refuses | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
test_finalize_with_drop_link_removes_the_link_and_keeps_the_new_root | split | 3 | migrate: drop_link removes the link and keeps the new root; two results that can break apart | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
test_finalize_can_drop_the_link_after_an_earlier_finalize | keep | 9 | migrate: drop_link works after the aside copy is gone | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
test_copy_recreates_a_link_inside_a_component | keep | 9 | migrate: a link inside a component is copied as a link and counted once | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py; source/sushicore/provision/links.py
test_journal_leaves_out_a_line_cut_short | keep | 9 | migrate: a journal line cut short is not returned | tests/provision/test_migrate.py; source/sushicore/provision/migrate.py
```

### `tests/provision/test_module_checks.py`

```
test_no_fragment_adds_no_sushi_rows | rewrite | 1 | module_checks: no fragment, no sushi rows; FakeGit in tests/provision/sushi_fakes.py stands in for IGitClient, no in-memory adapter in provision/git_client.py; quiet fixture patches two of the module's own functions | tests/provision/test_module_checks.py; tests/provision/sushi_fakes.py; tests/provision/conftest.py; source/sushicore/provision/module_checks.py; source/sushicore/provision/git_client.py
test_pinned_and_unpinned_modules_each_get_a_row_and_pins_a_conflict_row | rewrite | 1 | module_checks: a row per pin, per unpinned module and a conflict row; FakeGit stand-in, no in-memory adapter in provision/git_client.py; quiet fixture patches own functions; also several promises (split after the rewrite) | tests/provision/test_module_checks.py; tests/provision/sushi_fakes.py; source/sushicore/provision/module_checks.py; source/sushicore/provision/git_client.py
```

### `tests/provision/test_module_manifest.py`

```
test_a_manifest_that_names_a_fragment_decides_it | rewrite | 1 | module_manifest: manifest key decides the fragment; a small test writing a manifest file (forbidden for small); rewrite so fragment_path takes the parsed manifest | tests/provision/test_module_manifest.py; source/sushicore/provision/module_manifest.py
test_a_manifest_without_the_key_leaves_the_default | rewrite | 1 | module_manifest: manifest without the key gives the default; small test writing a file; rewrite on parsed manifest values | tests/provision/test_module_manifest.py; source/sushicore/provision/module_manifest.py
test_no_manifest_leaves_the_default | rewrite | 1 | module_manifest: no manifest gives the default; small test on a temporary folder; rewrite so the absence is a value, not a file | tests/provision/test_module_manifest.py; source/sushicore/provision/module_manifest.py
test_a_value_that_is_no_path_leaves_the_default | rewrite | 1 | module_manifest: non-path values leave the default; one parametrised row, small test writing a file; rewrite on parsed values | tests/provision/test_module_manifest.py; source/sushicore/provision/module_manifest.py
```

### `tests/provision/test_module_plan.py`

```
test_windows_uses_winget_a_direct_download_and_vcpkg | rewrite | 5 | module_plan: windows managers in order; compares class names of the managers, which is how the choice is built; rewrite against the public manager name, the managers' name attribute | tests/provision/test_module_plan.py; source/sushicore/provision/module_plan.py
test_linux_uses_every_system_manager_and_vcpkg_last | rewrite | 5 | module_plan: linux manager order and count; compares class names, inside of the unit; rewrite against manager names | tests/provision/test_module_plan.py; source/sushicore/provision/module_plan.py
test_the_missing_module_message_names_the_module_and_the_variable | keep | 9 | module_plan: missing-module message names the module, the wanter and the variable | tests/provision/test_module_plan.py; source/sushicore/provision/module_plan.py
test_a_module_that_names_a_fragment_keeps_it_over_the_manifest | rewrite | 1 | module_plan: code-named fragment beats the manifest; a small test writing a manifest file; rewrite on parsed manifest values | tests/provision/test_module_plan.py; source/sushicore/provision/module_plan.py; source/sushicore/provision/module_manifest.py
```

### `tests/provision/test_module_provision.py`

```
test_a_module_names_no_fragment_and_takes_the_cli_folder_by_default | delete | 1 | module_provision: default fragment None and config folder cli; default value (forbidden); the cli folder is exercised by the setup and doctor tests in tests/provision/test_commands.py | tests/provision/test_module_provision.py; tests/provision/test_commands.py; source/sushicore/provision/module_provision.py
test_a_module_that_names_its_config_folder_keeps_it | delete | 1 | module_provision: explicit config folder kept; constructor passthrough (forbidden trivial); tests/provision/test_link_command.py::test_the_config_folder_comes_from_the_module covers it | tests/provision/test_module_provision.py; tests/provision/test_link_command.py; source/sushicore/provision/module_provision.py
test_a_module_checkout_is_never_found_by_default | rewrite | 1 | module_provision: default locator finds nothing and is_binary is False; default value (forbidden), no other test checks the default locator; rewrite to test the default through a module with a sibling folder | tests/provision/test_module_provision.py; source/sushicore/provision/module_provision.py; tests/provision/test_commands.py
```

### `tests/provision/test_outcome.py`

```
test_done_succeeds_with_exit_code_zero_and_an_empty_payload | delete | 1 | outcome: done() literal shape (forbidden trivial); exit 0 is asserted through the CLI tests in tests/provision/test_commands.py | tests/provision/test_outcome.py; tests/provision/test_commands.py; source/sushicore/provision/outcome.py
test_failed_defaults_to_exit_code_one_and_accepts_a_code_and_a_payload | rewrite | 1 | outcome: failed() default code 1 is a default value (forbidden); the passthrough of code 2 is used by tests/provision/test_commands.py; rewrite to the passthrough promise alone | tests/provision/test_outcome.py; source/sushicore/provision/outcome.py
test_finish_sends_one_result_event_and_returns_the_exit_code | keep | 9 | outcome: finish sends one result and returns the code | tests/provision/test_outcome.py; source/sushicore/provision/outcome.py
test_two_outcomes_do_not_share_a_payload | keep | 9 | outcome: outcomes do not share a payload | tests/provision/test_outcome.py; source/sushicore/provision/outcome.py
```

### `tests/provision/test_package_command.py`

```
test_the_command_installs_the_default_tree_to_the_default_prefix | rewrite | 1 | package_command: package installs the default tree to build/dist; recording_console spy (tests/provision/conftest.py) with no in-memory adapter in provision/_output.py; also asserts argv positions (inside) | tests/provision/test_package_command.py; tests/provision/conftest.py; source/sushicore/provision/package_command.py; source/sushicore/provision/_output.py
test_the_command_installs_the_tree_it_is_told_to | rewrite | 1 | package_command: --build-dir overrides the default tree; recording_console spy, no in-memory adapter in provision/_output.py | tests/provision/test_package_command.py; tests/provision/conftest.py; source/sushicore/provision/package_command.py; source/sushicore/provision/_output.py
test_the_command_exits_non_zero_for_a_tree_that_is_not_built | rewrite | 1 | package_command: unbuilt tree exits 1; recording_console spy, no in-memory adapter in provision/_output.py | tests/provision/test_package_command.py; tests/provision/conftest.py; source/sushicore/provision/package_command.py; source/sushicore/provision/_output.py
```

### `tests/provision/test_package_install.py`

```
test_a_built_tree_is_installed_with_its_own_build_type | rewrite | 1 | package_install: install runs with the tree's build type and writes the stage marker; _Console stands in for the console Protocol of package_install.py, which has no in-memory adapter in that module | tests/provision/test_package_install.py; source/sushicore/provision/package_install.py
test_an_install_prints_one_line_counting_files_not_folders | rewrite | 1 | package_install: one summary line counts files, not folders; _Console stand-in, no in-memory adapter in package_install.py | tests/provision/test_package_install.py; source/sushicore/provision/package_install.py
test_a_failed_install_prints_all_of_cmakes_output | rewrite | 1 | package_install: a failed install prints cmake's output and leaves no stage marker; _Console stand-in, no in-memory adapter in package_install.py | tests/provision/test_package_install.py; source/sushicore/provision/package_install.py
test_the_summary_counts_up_to_date_files_apart | resize | 8 | package_install: install_summary counts up-to-date files apart and ignores missing paths; decides on the output text and file existence; seam: existence predicate passed in | tests/provision/test_package_install.py; source/sushicore/provision/package_install.py
test_a_tree_that_is_not_built_exits_non_zero_naming_it | rewrite | 1 | package_install: unbuilt tree refused and named; _Console stand-in, no in-memory adapter in package_install.py | tests/provision/test_package_install.py; source/sushicore/provision/package_install.py
test_no_archive_runs_no_cpack_and_archive_does | rewrite | 1 | package_install: CPack runs only when archive is asked; _Console stand-in, no in-memory adapter in package_install.py; asserts call positions (inside) | tests/provision/test_package_install.py; source/sushicore/provision/package_install.py
test_a_prefix_with_foreign_files_needs_force | rewrite | 1 | package_install: foreign prefix needs force; _Console stand-in, no in-memory adapter in package_install.py | tests/provision/test_package_install.py; source/sushicore/provision/package_install.py
test_a_staged_prefix_is_emptied_without_force | rewrite | 1 | package_install: a staged prefix is emptied without force; _Console stand-in, no in-memory adapter in package_install.py | tests/provision/test_package_install.py; source/sushicore/provision/package_install.py
test_the_prefix_is_never_the_checkout | rewrite | 1 | package_install: the checkout is refused as prefix even with force; _Console stand-in, no in-memory adapter in package_install.py | tests/provision/test_package_install.py; source/sushicore/provision/package_install.py
```

### `tests/provision/test_pin_chain.py`

```
test_a_chain_pinning_one_version_has_no_conflict | resize | 8 | pin_chain: three levels pinning one version agree; reads fragment files on disk; seam: fragment reader passed in | tests/provision/test_pin_chain.py; source/sushicore/provision/pin_chain.py; tests/provision/sushi_fakes.py
test_a_chain_pinning_two_versions_names_both_repositories | resize | 8 | pin_chain: conflict found and named with both pinners and versions; reads fragment files on disk; seam: fragment reader passed in | tests/provision/test_pin_chain.py; source/sushicore/provision/pin_chain.py; tests/provision/sushi_fakes.py
test_a_library_with_no_checkout_ends_its_branch | resize | 8 | pin_chain: unresolved library ends its branch with no conflict; reads disk for the checkout; seam: locator passed in | tests/provision/test_pin_chain.py; source/sushicore/provision/pin_chain.py; tests/provision/sushi_fakes.py
```

### `tests/provision/test_pipeline.py`

```
test_pipeline_stops_on_the_first_failure | rewrite | 1 | pipeline: stops on the first failed step; _Step is a test-written stand-in for the repository's Step ABC, no in-memory step in pipeline.py; recording_console requested and unused | tests/provision/test_pipeline.py; source/sushicore/provision/pipeline.py; tests/provision/conftest.py
test_empty_selection_installs_nothing | rewrite | 1 | pipeline: empty selection installs nothing; default values (forbidden); as_dict is read only here, so rewrite to show that a step given the empty selection installs nothing | tests/provision/test_pipeline.py; source/sushicore/provision/pipeline.py; tests/provision/test_selection.py
test_gpu_reads_through_the_selection | delete | 1 | pipeline: InstallContext.gpu reads the selection; property passthrough (forbidden trivial); gpu=True reaches the install steps in tests/provision/test_steps/test_install_deps.py | tests/provision/test_pipeline.py; source/sushicore/provision/pipeline.py; tests/provision/test_steps/test_install_deps.py
test_each_step_is_reported_once_with_a_header_a_progress_event_and_an_outcome | rewrite | 1 | pipeline: each step reported once; recording_console spy and _Step stand-in, no in-memory adapter in provision/_output.py; also several promises in one name (split candidate) | tests/provision/test_pipeline.py; tests/provision/conftest.py; source/sushicore/provision/pipeline.py; source/sushicore/provision/_output.py
test_the_pipeline_reaches_for_no_rich_progress_bar | delete | 1 | pipeline: no rich import in pipeline; change detector on source text (forbidden); the layering rule is held by tools/layering/check_package_layers.py, which lists rich in K_COMPONENT_PACKAGES | tests/provision/test_pipeline.py; source/sushicore/provision/pipeline.py; tools/layering/check_package_layers.py
test_a_caller_that_still_passes_show_progress_is_served | rewrite | 1 | pipeline: a caller passing show_progress is served; recording_console spy and _Step stand-in | tests/provision/test_pipeline.py; tests/provision/conftest.py; source/sushicore/provision/pipeline.py
```

### `tests/provision/test_probe.py`

```
test_classify_prefers_a_discrete_adapter | resize | 8 | probe: classify gives the discrete vendor; pure logic in a medium file, no seam needed, so small | tests/provision/test_probe.py; source/sushicore/provision/probe.py; tests/conftest.py; tests/provision/conftest.py
test_integrated_only_falls_back_to_its_vendor | resize | 8 | probe: classify gives the vendor of an integrated-only list; pure logic, small | tests/provision/test_probe.py; source/sushicore/provision/probe.py; tests/conftest.py; tests/provision/conftest.py
test_binary_works_rejects_a_missing_command | keep | 9 | probe: binary_works is False for a command not on PATH; a real process start is the boundary, so medium is the smallest size | tests/provision/test_probe.py; source/sushicore/provision/probe.py; tests/conftest.py; tests/provision/conftest.py
test_tools_dir_follows_the_root | delete | 1 | forbidden kind: a _private name (probe._tools_dir); the promise is tested in tests/provision/test_home.py::test_subdirectories_hang_off_the_root, the own-module test of home | tests/provision/test_probe.py; tests/provision/test_home.py; source/sushicore/provision/probe.py; tests/provision/conftest.py
test_find_vcvars_is_none_off_windows | resize | 8 | probe: find_vcvars is None off Windows; reach: sys.platform patched, a process-wide value; seam: pass the platform into find_vcvars from the shell | tests/provision/test_probe.py; source/sushicore/provision/probe.py; tests/provision/conftest.py
test_find_vcvars_scans_the_newest_year_first | rewrite | 1 | forbidden kind: replaces the module's own function _vcvars_from_vswhere and sys.platform; the only test of the promise; rewrite passes the Program Files roots into _vcvars_from_disk_scan and asserts on a fixture tree | tests/provision/test_probe.py; source/sushicore/provision/probe.py; tests/provision/conftest.py
test_find_vcvars_prefers_vswhere | rewrite | 1 | forbidden kind: replaces the module's own function _vcvars_from_vswhere and sys.platform; the only test of the promise; rewrite gives find_vcvars a vswhere locator parameter | tests/provision/test_probe.py; source/sushicore/provision/probe.py; tests/provision/conftest.py
test_find_vcvars_is_none_when_nothing_is_installed | rewrite | 1 | forbidden kind: replaces the module's own _vcvars_from_vswhere and sys.platform; the only test of the promise; rewrite passes empty roots and a locator that returns none | tests/provision/test_probe.py; source/sushicore/provision/probe.py; tests/provision/conftest.py
test_resolve_windows_keeps_the_2022_glob_first | rewrite | 1 | forbidden kind: replaces the module's own _first_glob and find_vcvars, and stands in a SimpleNamespace for ProvisionSettings; the only test of the promise; rewrite uses ProvisionSettings and a glob seam, and absorbs the fallback test as rows | tests/provision/test_probe.py; source/sushicore/provision/probe.py; tests/provision/conftest.py
test_resolve_windows_falls_back_to_find_vcvars | rewrite | 1 | forbidden kind: replaces the module's own _first_glob and find_vcvars, and stands in a SimpleNamespace for ProvisionSettings; the only test of the promise; rewrite folds into the resolve_windows row table with the test above | tests/provision/test_probe.py; source/sushicore/provision/probe.py; tests/provision/conftest.py
test_installed_toolchain_prefers_the_current_root | merge | 4 | probe: installed_toolchain returns the first root holding the file; merge with tests/provision/test_probe.py::test_installed_toolchain_falls_back_to_a_legacy_root and ::test_installed_toolchain_is_none_when_no_root_holds_it into one row table | tests/provision/test_probe.py; source/sushicore/provision/probe.py; tests/provision/conftest.py
test_installed_toolchain_falls_back_to_a_legacy_root | merge | 4 | probe: installed_toolchain returns the first root holding the file; merge with tests/provision/test_probe.py::test_installed_toolchain_prefers_the_current_root into one row table | tests/provision/test_probe.py; source/sushicore/provision/probe.py; tests/provision/conftest.py
test_installed_toolchain_is_none_when_no_root_holds_it | merge | 4 | probe: installed_toolchain gives none when no root holds the file; merge with tests/provision/test_probe.py::test_installed_toolchain_prefers_the_current_root into one row table | tests/provision/test_probe.py; source/sushicore/provision/probe.py; tests/provision/conftest.py
test_discovery_records_a_legacy_bundle | rewrite | 1 | forbidden kind: a _private name (probe._discover_installed_toolchains); no other test records a legacy bundle; rewrite goes through resolve_local_config on linux and asserts llvm_root | tests/provision/test_probe.py; source/sushicore/provision/probe.py; tests/provision/conftest.py
test_a_missing_lspci_is_recorded | resize | 8 | probe: a display-adapter reader whose process cannot start yields empty and one warning; reach: subprocess.run replaced and the logger captured, both process-wide; seam: a runner parameter on the reader and an in-memory log sink from the logger port | tests/provision/test_probe.py; source/sushicore/provision/probe.py; tests/provision/conftest.py
test_a_video_controller_query_that_times_out_is_recorded | resize | 8 | probe: the Windows adapter reader whose process times out yields empty and one warning; reach: subprocess.run replaced and the logger captured; seam: a runner parameter and an in-memory log sink | tests/provision/test_probe.py; source/sushicore/provision/probe.py; tests/provision/conftest.py
test_a_defect_in_an_adapter_query_is_not_reported_as_no_adapters[_linux_display_adapters] and [_windows_display_adapters] | resize | 8 | probe: a non-process error escapes the adapter readers; reach: subprocess.run replaced, a process-wide attribute; seam: a runner parameter on each reader; one parametrised line; absorbs tests/provision/test_probe.py::test_binary_works_does_not_report_a_defect_as_a_broken_binary as a row | tests/provision/test_probe.py; source/sushicore/provision/probe.py; tests/provision/conftest.py
test_binary_works_records_why_a_command_did_not_run | resize | 8 | probe: binary_works logs the error behind a False answer; reach: subprocess.run replaced and the logger captured; seam: a runner parameter on binary_works and an in-memory log sink | tests/provision/test_probe.py; source/sushicore/provision/probe.py; tests/provision/conftest.py
test_binary_works_does_not_report_a_defect_as_a_broken_binary | merge | 4 | probe: a non-process error escapes; the same promise as tests/provision/test_probe.py::test_a_defect_in_an_adapter_query_is_not_reported_as_no_adapters, merged as a row of that test | tests/provision/test_probe.py; source/sushicore/provision/probe.py; tests/provision/conftest.py
test_find_vcvars_logs_a_vswhere_that_did_not_run | merge | 4 | probe: a vswhere that cannot start is logged with its reason; merge with tests/provision/test_probe.py::test_find_vcvars_logs_a_vswhere_that_failed into one row table | tests/provision/test_probe.py; source/sushicore/provision/probe.py; tests/provision/conftest.py
test_find_vcvars_logs_a_vswhere_that_failed | merge | 4 | probe: a vswhere that exits non-zero is logged with its status; merge with tests/provision/test_probe.py::test_find_vcvars_logs_a_vswhere_that_did_not_run into one row table | tests/provision/test_probe.py; source/sushicore/provision/probe.py; tests/provision/conftest.py
```

### `tests/provision/test_registry.py`

```
test_empty_registry_has_no_components | keep | 9 | registry: load of a missing file gives no components; the file read is the boundary | tests/provision/test_registry.py; source/sushicore/provision/registry.py; tests/conftest.py
test_add_save_load_round_trips | keep | 9 | registry: save then load returns the component; file boundary | tests/provision/test_registry.py; source/sushicore/provision/registry.py; tests/conftest.py
test_second_consumer_merges_instead_of_duplicating | resize | 8 | registry: add merges consumers of one name and version; reach: load() reads the registry file; seam: an in-memory registry file store passed to Registry | tests/provision/test_registry.py; source/sushicore/provision/registry.py; tests/conftest.py
test_release_keeps_a_component_another_consumer_uses | resize | 8 | registry: release is True only when no consumer is left; reach: file via load(); seam: in-memory registry file store | tests/provision/test_registry.py; source/sushicore/provision/registry.py; tests/conftest.py
test_corrupt_registry_raises_instead_of_emptying | keep | 9 | registry: an unparsable file raises RegistryError naming the file; the file bytes are the boundary | tests/provision/test_registry.py; source/sushicore/provision/registry.py; tests/conftest.py
test_save_leaves_no_temp_file | keep | 9 | registry: save leaves only the registry file; a folder is the boundary | tests/provision/test_registry.py; source/sushicore/provision/registry.py; tests/conftest.py
test_round_trip_preserves_unicode_and_special_characters | keep | 9 | registry: save then load keeps unicode and special characters; file boundary | tests/provision/test_registry.py; source/sushicore/provision/registry.py; tests/conftest.py
test_find_without_version_raises_when_ambiguous | resize | 8 | registry: find without a version raises on two versions; reach: load() reads a file; seam: in-memory registry file store | tests/provision/test_registry.py; source/sushicore/provision/registry.py; tests/conftest.py
test_entry_missing_a_field_raises_naming_the_file | keep | 9 | registry: a malformed entry raises RegistryError naming the file; the file's bytes are the boundary | tests/provision/test_registry.py; source/sushicore/provision/registry.py; tests/conftest.py
test_seed_records_each_component_with_its_stamp_version | keep | 9 | registry: seed records each folder with its stamp tag; a folder tree is the boundary | tests/provision/test_registry.py; source/sushicore/provision/registry.py; tests/conftest.py
test_seed_skips_components_already_recorded | keep | 9 | registry: seed skips a name already held; folder tree boundary | tests/provision/test_registry.py; source/sushicore/provision/registry.py; tests/conftest.py
test_seed_of_an_empty_tree_adds_nothing | keep | 9 | registry: seed of a tree with no component adds nothing; count of zero, folder boundary | tests/provision/test_registry.py; source/sushicore/provision/registry.py; tests/conftest.py
```

### `tests/provision/test_selection.py`

```
test_an_unsatisfied_group_turns_on_its_first_declared_member | rewrite | 1 | forbidden kind: stand-in _Source for IDependencySource, a port the repository owns with no in-memory adapter in fragments.py; the only test of the promise; rewrite uses an in-memory dependency source that fragments.py owns, with the rows below | tests/provision/test_selection.py; source/sushicore/provision/selection.py; tests/conftest.py
test_declaration_order_decides_the_default | rewrite | 1 | forbidden kind: stand-in _Source for IDependencySource; the only test of the promise; rewrite uses the in-memory dependency source as a row | tests/provision/test_selection.py; source/sushicore/provision/selection.py; tests/conftest.py
test_a_satisfied_group_turns_nothing_on | rewrite | 1 | forbidden kind: stand-in _Source for IDependencySource; the only test of the promise; rewrite uses the in-memory dependency source | tests/provision/test_selection.py; source/sushicore/provision/selection.py; tests/conftest.py
test_a_requested_key_turns_on_beside_the_default | rewrite | 1 | forbidden kind: stand-in _Source for IDependencySource; the only test of the promise; rewrite uses the in-memory dependency source | tests/provision/test_selection.py; source/sushicore/provision/selection.py; tests/conftest.py
test_a_requested_key_turns_on_in_a_satisfied_group | rewrite | 1 | forbidden kind: stand-in _Source for IDependencySource; the only test of the promise; rewrite uses the in-memory dependency source | tests/provision/test_selection.py; source/sushicore/provision/selection.py; tests/conftest.py
test_an_unknown_requested_key_raises_and_names_the_valid_ones | rewrite | 1 | forbidden kind: stand-in _Source for IDependencySource; the only test of the promise; rewrite uses the in-memory dependency source | tests/provision/test_selection.py; source/sushicore/provision/selection.py; tests/conftest.py
test_an_optional_toolchain_is_not_installed_unasked | rewrite | 1 | forbidden kind: stand-in _Source for IDependencySource, and two results of two calls in one test; the only test of the promise; rewrite splits the requested case into its own row | tests/provision/test_selection.py; source/sushicore/provision/selection.py; tests/conftest.py
test_a_source_declaring_no_toolchain_selects_none | rewrite | 1 | forbidden kind: stand-in _Source for IDependencySource; the only test of the promise; rewrite uses the in-memory dependency source | tests/provision/test_selection.py; source/sushicore/provision/selection.py; tests/conftest.py
test_gpu_turns_on_when_a_gpu_only_dependency_is_declared | rewrite | 1 | forbidden kind: stand-in _Source for IDependencySource, and the helper _with_gpu_dependency builds it from _RUNTIME; the only test of the promise; rewrite uses the in-memory dependency source | tests/provision/test_selection.py; source/sushicore/provision/selection.py; tests/conftest.py
test_gpu_stays_off_when_the_caller_refuses_it | rewrite | 1 | forbidden kind: stand-in _Source for IDependencySource; the only test of the promise; rewrite uses the in-memory dependency source | tests/provision/test_selection.py; source/sushicore/provision/selection.py; tests/conftest.py
test_gpu_stays_off_when_nothing_declared_needs_one | rewrite | 1 | forbidden kind: stand-in _Source for IDependencySource; the only test of the promise; rewrite uses the in-memory dependency source | tests/provision/test_selection.py; source/sushicore/provision/selection.py; tests/conftest.py
test_the_component_table_names_every_selection_field | delete | 1 | forbidden kind: a test of trivial code, a constant table; it states no behaviour beyond the table's contents, which enabled_keys already checks in tests/provision/test_selection.py::test_enabled_keys_follow_the_table_order | tests/provision/test_selection.py; source/sushicore/provision/selection.py
test_a_shared_fragment_cannot_select_a_toolchain | rewrite | 1 | forbidden kind: stand-in _Source for IDependencySource; the only test of the promise that a shared owner selects nothing; rewrite uses the in-memory dependency source | tests/provision/test_selection.py; source/sushicore/provision/selection.py; tests/conftest.py
test_enabled_keys_follow_the_table_order | keep | 9 | selection: enabled_keys follows the table order; pure value logic, small | tests/provision/test_selection.py; source/sushicore/provision/selection.py; tests/conftest.py
```

### `tests/provision/test_setup_command.py`

```
test_an_unknown_toolchain_stops_setup_with_the_usage_code | rewrite | 1 | forbidden kind: stand-in _Console for the console port and _OfflineGit for IGitClient, neither with an in-memory adapter in its port module; the same promise is tested in tests/provision/test_commands.py::test_setup_rejects_an_unknown_toolchain_before_the_lock, which the own-module ruling deletes, so this is the only test left; rewrite uses the in-memory console and git adapters | tests/provision/test_setup_command.py; source/sushicore/provision/setup_command.py; tests/provision/test_commands.py; tests/conftest.py; tests/provision/conftest.py
```

### `tests/provision/test_sinks.py`

```
test_module_sink_writes_config_local | keep | 9 | sinks: ModuleSink writes [tool.<platform>] to config.local.toml; file boundary | tests/provision/test_sinks.py; source/sushicore/provision/sinks.py; tests/conftest.py
test_workspace_sink_keeps_modules | split | 3 | two promises: write_paths keeps the [modules] table, and write_paths writes [tool.linux]; the name states the first and the second assertion is a second result | tests/provision/test_sinks.py; source/sushicore/provision/sinks.py; tests/conftest.py
test_write_tool_sets_a_top_level_key | keep | 9 | sinks: write_tool sets a top-level tool key; file boundary | tests/provision/test_sinks.py; source/sushicore/provision/sinks.py; tests/conftest.py
test_clear_removes_only_the_tool_table | keep | 9 | sinks: clear removes the tool table and keeps modules; file boundary | tests/provision/test_sinks.py; source/sushicore/provision/sinks.py; tests/conftest.py
test_backup_copies_the_existing_file_before_it_changes | keep | 9 | sinks: backup copies the prior bytes to .toml.bak before a change; file boundary | tests/provision/test_sinks.py; source/sushicore/provision/sinks.py; tests/conftest.py
test_backup_returns_none_when_the_target_is_absent | keep | 9 | sinks: backup returns none and writes nothing when the file is absent; file boundary | tests/provision/test_sinks.py; source/sushicore/provision/sinks.py; tests/conftest.py
```

### `tests/provision/test_steps/test_console_output.py`

```
test_calls_reach_the_bound_console | rewrite | 1 | small test reaches the process-wide console provider in _output.py and records through the recording_console spy; rewrite with the provider passed to the proxy, and an in-memory console adapter in _output.py | tests/provision/test_steps/test_console_output.py; tests/provision/conftest.py; source/sushicore/provision/_output.py
test_unbound_console_raises_a_named_error | rewrite | 1 | small test sets the process-wide provider to None (reach into a process-wide instance from small); rewrite with a proxy built on an explicit provider | (same files)
test_provider_is_called_lazily | rewrite | 1 | small test binds the process-wide provider; rewrite with an explicit provider argument | (same files)
test_a_plain_console_answers_is_machine_for_steps_literal | rewrite | 1 | private name steps._literal and the private module _output; small test binds the process-wide console; rewrite through a public step with a real Console | tests/provision/test_steps/test_console_output.py; source/sushicore/provision/steps.py; source/sushicore/provision/_output.py
```

### `tests/provision/test_steps/test_detect.py`

```
test_undeclared_toolchains_are_not_needed | rewrite | 1 | stand-in MemorySource for IDependencySource; rewrite with an in-memory source in source/sushicore/provision/fragments.py | tests/provision/test_steps/test_detect.py; source/sushicore/provision/steps.py; source/sushicore/provision/fragments.py
test_declared_toolchains_are_missing_when_absent | rewrite | 1 | stand-in MemorySource for IDependencySource; same rewrite | (same files)
test_rows_are_grouped_by_owner_in_dependency_order | rewrite | 1 | stand-in MemorySource for IDependencySource; same rewrite | (same files)
test_a_toolchain_whose_capability_another_provides_is_not_needed | rewrite | 1 | stand-in MemorySource for IDependencySource; same rewrite | (same files)
test_every_member_of_an_unsatisfied_capability_is_missing | rewrite | 1 | stand-in MemorySource for IDependencySource; same rewrite | (same files)
```

### `tests/provision/test_steps/test_install_deps.py`

```
test_provision_adapters_for_run_skips_without_a_resolved_llvm_root | rewrite | 1 | stubs repository functions steps_mod.provision_gpu_adapters and probe.resolve_local_config, and a recording_console spy; rewrite through injected adapter builder and resolver | tests/provision/test_steps/test_install_deps.py; tests/provision/conftest.py; source/sushicore/provision/steps.py
test_provision_adapters_for_run_uses_the_resolved_llvm_root | rewrite | 1 | stubs steps_mod.provision_gpu_adapters; rewrite through the injected builder | (same files)
test_provision_adapters_for_run_drops_probed_keys_the_settings_do_not_hold | rewrite | 1 | stubs provision_gpu_adapters and probe.resolve_local_config; rewrite through injected seams | (same files)
test_run_windows_reaches_provision_adapters_for_run_when_gpu_is_selected | rewrite | 1 | stubs seven private InstallDepsStep methods and steps_mod functions; stand-in _FakeAptManager is not used here; rewrite with injected sub-steps | (same files)
test_run_windows_skips_provision_adapters_for_run_without_gpu | rewrite | 1 | same stubs; rewrite with injected sub-steps. Its GPU-off case pairs with the reaches test above | (same files)
test_run_linux_reaches_provision_adapters_for_run_when_gpu_is_selected | rewrite | 1 | stubs private InstallDepsStep._install_toolchains and steps_mod functions; stand-in _FakeAptManager(LinuxPackageManager); rewrite with injected seams | (same files)
test_run_linux_skips_provision_adapters_for_run_without_gpu | rewrite | 1 | same stubs and stand-in; rewrite with injected seams | (same files)
test_run_windows_with_no_gpu_provisions_nothing | rewrite | 1 | stubs as above and recording_console spy; carries: no GPU detected means nothing is provisioned and a message is printed | (same files)
test_run_linux_with_no_gpu_provisions_nothing | rewrite | 1 | stubs as above and recording_console spy; carries: no GPU detected on Linux means nothing is provisioned | (same files)
test_provision_adapters_for_run_uses_a_toolchain_already_on_the_machine | rewrite | 1 | stubs provision_gpu_adapters and probe.resolve_local_config; rewrite through injected resolver | (same files)
test_vs_build_tools_are_not_installed_when_a_visual_studio_has_the_cpp_tools | rewrite | 1 | stubs probe.find_vcvars and subprocess.run (process-wide), and a stand-in winget (_WingetWithoutBuildTools) for the package manager interface; rewrite through injected seams | (same files)
```

### `tests/provision/test_steps/test_steps.py`

```
test_configure_writes_through_the_sink | rewrite | 1 | stand-in _Sink for the repository's sink interface and stub of probe.resolve_local_config; rewrite with an in-memory sink in source/sushicore/provision/sinks.py | tests/provision/test_steps/test_steps.py; tests/provision/conftest.py; source/sushicore/provision/steps.py; source/sushicore/provision/sinks.py
test_configure_backs_up_before_writing | rewrite | 1 | stand-in _Sink and stub of probe.resolve_local_config, recording_console spy; rewrite with the in-memory sink and console adapter | (same files)
test_configure_skips_the_backup_line_when_there_is_nothing_to_back_up | rewrite | 1 | same stand-in, stub and spy; rewrite; its no-backup case pairs with the backs-up test | (same files)
test_uninstall_leaves_a_refused_root_intact | rewrite | 1 | recording_console spy and process-wide home.bind_root; rewrite with the root passed to the step | (same files)
test_configure_dry_run_prints_the_rendered_config | rewrite | 1 | stand-in _Sink, stub of probe.resolve_local_config, recording_console spy; rewrite | (same files)
test_windows_uninstall_refuses_before_touching_tools | rewrite | 1 | stand-ins _EmptySource and _Sink; process-wide home.bind_root; rewrite with the root and sink passed in | (same files)
test_linux_uninstall_refuses_before_removing_anything | rewrite | 1 | stand-ins _EmptySource and _Sink; process-wide home.bind_root; rewrite | (same files)
test_missing_dependency_hint_names_the_calling_program | rewrite | 1 | capsys_console spy (recording_console with a text view) and private steps._MISSING and DetectStep._report_inventory; rewrite through a public step and the console's in-memory adapter | (same files)
test_missing_dependency_hint_uses_the_rerun_command_the_consumer_names | rewrite | 1 | capsys_console spy and private steps._MISSING; rewrite as above | (same files)
test_a_context_names_no_consumer_until_it_is_given_one | rewrite | 1 | capsys_console spy and private steps._MISSING, DetectStep._report_inventory; rewrite as above | (same files)
test_install_deps_binds_the_manifest_digests_for_the_length_of_the_run | rewrite | 1 | stubs the private InstallDepsStep._run_windows and a recording_console spy; rewrite through an injected Windows install step | (same files)
test_a_digest_mismatch_stops_the_pipeline_and_unbinds_the_run | rewrite | 1 | stubs private InstallDepsStep._run_windows, a stand-in Step subclass for the pipeline, and a process-wide verifier binding; rewrite | (same files)
test_the_removal_hint_the_consumer_supplies_follows_the_note | merge | 4 | merge with test_no_removal_hint_leaves_the_plain_note into rows over the hint: removal_note appends the hint, or leaves the plain note alone | (same files)
test_no_removal_hint_leaves_the_plain_note | merge | 4 | merge with test_the_removal_hint_the_consumer_supplies_follows_the_note into the same rows; the merged rows are pure and resize to small | (same files)
```

### `tests/provision/test_sushi_fetch.py`

```
test_a_missing_library_is_fetched_and_then_resolves_as_fetched | rewrite | 1 | forbidden kind: stand-in FakeGit for IGitClient and recording_console for the console port, neither an in-memory adapter of its port module; the only test of the promise; rewrite uses an in-memory git client that the git_client module owns | tests/provision/test_sushi_fetch.py; tests/provision/sushi_fakes.py; source/sushicore/provision/sushi_fetch.py; source/sushicore/provision/sushi_sources.py; tests/provision/conftest.py; tests/conftest.py
test_a_sibling_wins_and_the_step_is_skipped | rewrite | 1 | forbidden kind: stand-in FakeGit for IGitClient and recording_console; the only test of the promise; rewrite uses the in-memory git client | tests/provision/test_sushi_fetch.py; tests/provision/sushi_fakes.py; source/sushicore/provision/sushi_fetch.py; source/sushicore/provision/sushi_sources.py; tests/provision/conftest.py; tests/conftest.py
test_the_directory_variable_wins | rewrite | 1 | forbidden kind: stand-in FakeGit for IGitClient and recording_console; the step-level promise is not tested elsewhere (test_sushi_sources.py tests resolve, not the step); rewrite uses the in-memory git client | tests/provision/test_sushi_fetch.py; tests/provision/sushi_fakes.py; source/sushicore/provision/sushi_fetch.py; source/sushicore/provision/sushi_sources.py; tests/provision/conftest.py; tests/conftest.py
test_a_commit_off_the_pin_fails_and_leaves_no_folder | rewrite | 1 | forbidden kind: stand-in FakeGit for IGitClient and recording_console; the only test of the promise; rewrite uses the in-memory git client with a HEAD off the pin | tests/provision/test_sushi_fetch.py; tests/provision/sushi_fakes.py; source/sushicore/provision/sushi_fetch.py; source/sushicore/provision/sushi_sources.py; tests/provision/conftest.py; tests/conftest.py
test_a_failed_clone_names_the_url_the_tag_and_the_directory_variable | rewrite | 1 | forbidden kind: stand-in FakeGit for IGitClient and recording_console; the only test of the promise; rewrite uses the in-memory git client that refuses and the in-memory console | tests/provision/test_sushi_fetch.py; tests/provision/sushi_fakes.py; source/sushicore/provision/sushi_fetch.py; source/sushicore/provision/sushi_sources.py; tests/provision/conftest.py; tests/conftest.py
test_a_fetched_copy_at_the_pin_is_not_cloned_again | rewrite | 1 | forbidden kind: stand-in FakeGit for IGitClient and recording_console; the only test of the promise; rewrite uses the in-memory git client and counts its clones | tests/provision/test_sushi_fetch.py; tests/provision/sushi_fakes.py; source/sushicore/provision/sushi_fetch.py; source/sushicore/provision/sushi_sources.py; tests/provision/conftest.py; tests/conftest.py
```

### `tests/provision/test_sushi_setup.py`

```
test_the_locator_tries_the_base_first_then_the_fetched_copy | rewrite | 1 | forbidden kind: lambda stand-ins for Locate, the repository's locator type in closure.py, with no in-memory adapter; the only test of the promise; rewrite uses an in-memory Locate beside closure.py | tests/provision/test_sushi_setup.py; source/sushicore/provision/sushi_setup.py; source/sushicore/provision/sushi_sources.py; tests/provision/sushi_fakes.py; tests/provision/conftest.py; tests/conftest.py
test_prepare_fetches_a_chain_that_agrees | rewrite | 1 | forbidden kind: stand-in FakeGit for IGitClient and recording_console; the only test of the promise; rewrite uses the in-memory git client | tests/provision/test_sushi_setup.py; tests/provision/sushi_fakes.py; source/sushicore/provision/sushi_setup.py; source/sushicore/provision/sushi_sources.py; tests/provision/conftest.py; tests/conftest.py
test_prepare_stops_on_a_conflict_before_cloning | rewrite | 1 | forbidden kind: stand-in FakeGit for IGitClient and recording_console; the only test of the promise; rewrite uses the in-memory git client and the in-memory console | tests/provision/test_sushi_setup.py; tests/provision/sushi_fakes.py; source/sushicore/provision/sushi_setup.py; source/sushicore/provision/sushi_sources.py; tests/provision/conftest.py; tests/conftest.py
test_prepare_has_nothing_to_do_without_pins | rewrite | 1 | forbidden kind: stand-in FakeGit for IGitClient; the only test of the promise; rewrite asserts on the in-memory git client that no clone is attempted | tests/provision/test_sushi_setup.py; tests/provision/sushi_fakes.py; source/sushicore/provision/sushi_setup.py; tests/provision/conftest.py; tests/conftest.py
```

### `tests/provision/test_sushi_source_check.py`

```
test_a_missing_library_fails_with_the_fix | rewrite | 1 | forbidden kind: stand-in FakeGit for IGitClient, not used by the promise; the only test of the promise; rewrite drops the git stand-in | tests/provision/test_sushi_source_check.py; tests/provision/sushi_fakes.py; source/sushicore/provision/sushi_source_check.py; source/sushicore/provision/sushi_sources.py; tests/provision/conftest.py; tests/conftest.py
test_a_fetched_library_reports_fetched | rewrite | 1 | forbidden kind: stand-in FakeGit for IGitClient, not used by the promise; the only test of the promise; rewrite drops the git stand-in | tests/provision/test_sushi_source_check.py; tests/provision/sushi_fakes.py; source/sushicore/provision/sushi_source_check.py; source/sushicore/provision/sushi_sources.py; tests/provision/conftest.py; tests/conftest.py
test_a_sibling_at_the_pin_reports_sibling | rewrite | 1 | forbidden kind: stand-in FakeGit for IGitClient with a HEAD table; the only test of the promise; rewrite uses the in-memory git client with that HEAD table | tests/provision/test_sushi_source_check.py; tests/provision/sushi_fakes.py; source/sushicore/provision/sushi_source_check.py; source/sushicore/provision/sushi_sources.py; tests/provision/conftest.py; tests/conftest.py
test_a_sibling_off_the_pin_warns | rewrite | 1 | forbidden kind: stand-in FakeGit for IGitClient with a HEAD table; the only test of the promise; rewrite uses the in-memory git client | tests/provision/test_sushi_source_check.py; tests/provision/sushi_fakes.py; source/sushicore/provision/sushi_source_check.py; source/sushicore/provision/sushi_sources.py; tests/provision/conftest.py; tests/conftest.py
test_the_pin_check_fails_on_a_conflict_and_passes_without_one | split | 3 | two promises joined by "and" that can break apart: the conflict FAILs, and the agreed pins pass; the second state is a second test | tests/provision/test_sushi_source_check.py; source/sushicore/provision/sushi_source_check.py; source/sushicore/provision/pin_chain.py; tests/provision/sushi_fakes.py; tests/conftest.py
test_an_unpinned_module_warns_and_names_where_it_was_found | keep | 9 | sushi_source_check: an unpinned library WARNs, is not required, and names its sibling; a folder tree is the boundary | tests/provision/test_sushi_source_check.py; source/sushicore/provision/sushi_source_check.py; source/sushicore/provision/sushi_sources.py; tests/provision/sushi_fakes.py; tests/conftest.py
```

### `tests/provision/test_sushi_sources.py`

```
test_the_directory_variable_is_upper_case | delete | 1 | forbidden kind: a test of trivial code, a one-line name builder; the name is stated in the fetch message, which tests/provision/test_sushi_fetch.py checks | tests/provision/test_sushi_sources.py; tests/provision/test_sushi_fetch.py; source/sushicore/provision/sushi_sources.py
test_the_fetched_copy_sits_under_the_home | rewrite | 7 | the promise holds, but the test takes the root fixture and never uses it, which hides the cause; rewrite drops the unused fixture and asserts on a fixture home | tests/provision/test_sushi_sources.py; source/sushicore/provision/sushi_sources.py; tests/provision/conftest.py; tests/conftest.py
test_nothing_resolves_without_a_checkout | keep | 9 | sushi_sources: resolve gives none without a checkout; folder boundary | tests/provision/test_sushi_sources.py; source/sushicore/provision/sushi_sources.py; tests/conftest.py
test_the_fetched_copy_is_found_last | keep | 9 | sushi_sources: a fetched copy resolves as fetched when nothing else exists; Q4: the same promise in tests/test_stack_config.py::test_locate_sibling_finds_the_fetched_copy_of_a_pinned_library is in another module, so this own-module test stays | tests/provision/test_sushi_sources.py; source/sushicore/provision/sushi_sources.py; tests/test_stack_config.py; tests/conftest.py
test_the_fetched_copy_needs_a_version | keep | 9 | sushi_sources: no version means no fetched copy is looked for; folder boundary | tests/provision/test_sushi_sources.py; source/sushicore/provision/sushi_sources.py; tests/conftest.py
test_a_sibling_wins_over_the_fetched_copy | keep | 9 | sushi_sources: the sibling wins over the fetched copy; folder boundary | tests/provision/test_sushi_sources.py; source/sushicore/provision/sushi_sources.py; tests/conftest.py
test_a_configured_directory_wins_over_the_environment_and_the_sibling | split | 3 | two promises: the variable wins over the sibling, and the configured directory wins over the variable; the name joins them with "beats ... which beats" | tests/provision/test_sushi_sources.py; source/sushicore/provision/sushi_sources.py; tests/conftest.py
test_a_directory_that_does_not_exist_falls_through | keep | 9 | sushi_sources: a variable naming no folder falls through to the sibling; folder boundary | tests/provision/test_sushi_sources.py; source/sushicore/provision/sushi_sources.py; tests/conftest.py
```

### `tests/provision/test_system.py`

```
test_sudo_bash_dry_run_runs_nothing | rewrite | 1 | forbidden kind: recording_console, a recorder for the console port that the test takes and never asserts, with no in-memory console adapter; the only test of the promise; rewrite asserts on an in-memory console that the command was shown and not run | tests/provision/test_system.py; source/sushicore/provision/system.py; tests/provision/conftest.py; tests/conftest.py
test_os_release_is_a_dict | resize | 8 | system: os_release gives a dict; reach: the real /etc/os-release, a file, from a small file; the assertion is a type only; seam: a text argument for os_release, and the rewrite asserts parsed keys | tests/provision/test_system.py; source/sushicore/provision/system.py; tests/provision/conftest.py; tests/conftest.py
test_an_unreadable_os_release_is_recorded | resize | 8 | system: an unreadable os-release yields empty and one warning naming /etc/os-release; reach: the Path name in system replaced and the logger captured, both process-wide; seam: a text reader parameter and an in-memory log sink | tests/provision/test_system.py; source/sushicore/provision/system.py; tests/provision/conftest.py; tests/conftest.py
test_an_absent_os_release_is_not_a_warning | resize | 8 | system: an absent os-release yields empty and no warning; reach: the Path name in system replaced and the logger captured; seam: a text reader parameter and an in-memory log sink | tests/provision/test_system.py; source/sushicore/provision/system.py; tests/provision/conftest.py; tests/conftest.py
```

### `tests/provision/test_user_environment.py`

```
test_registry_write_stores_the_value_and_broadcasts | rewrite | 1 | forbidden kind: FakeKey and the broadcast spy for EnvironmentKey, a port the repository owns with no in-memory adapter in user_environment.py; the only test of the promise; rewrite uses an in-memory key that user_environment.py owns | tests/provision/test_user_environment.py; source/sushicore/provision/user_environment.py; tests/provision/conftest.py; tests/conftest.py
test_registry_read_returns_none_for_an_unset_name | rewrite | 1 | forbidden kind: FakeKey and the event-log spy for EnvironmentKey; the only test of the promise; rewrite uses the in-memory key | tests/provision/test_user_environment.py; source/sushicore/provision/user_environment.py; tests/provision/conftest.py; tests/conftest.py
test_registry_read_returns_what_was_written | rewrite | 1 | forbidden kind: FakeKey for EnvironmentKey; the only test of the registry round trip; rewrite uses the in-memory key | tests/provision/test_user_environment.py; source/sushicore/provision/user_environment.py; tests/provision/conftest.py; tests/conftest.py
test_registry_remove_deletes_the_value_and_broadcasts | rewrite | 1 | forbidden kind: FakeKey and the event-log spy for EnvironmentKey; the only test of the promise; rewrite uses the in-memory key | tests/provision/test_user_environment.py; source/sushicore/provision/user_environment.py; tests/provision/conftest.py; tests/conftest.py
test_registry_remove_of_an_unset_name_is_not_an_error | rewrite | 1 | forbidden kind: FakeKey for EnvironmentKey; the promise is shared with the profile store, so the rewrite folds it into one UserEnvironment contract suite in user_environment.py, instantiated for the in-memory key and the profile store | tests/provision/test_user_environment.py; source/sushicore/provision/user_environment.py; tests/provision/conftest.py; tests/conftest.py
test_profile_write_creates_the_block | keep | 9 | user_environment: a profile write creates one managed block with the exact text; file boundary | tests/provision/test_user_environment.py; source/sushicore/provision/user_environment.py; tests/conftest.py
test_profile_write_keeps_the_lines_around_the_block | keep | 9 | user_environment: a profile write keeps the user's lines around the block; file boundary | tests/provision/test_user_environment.py; source/sushicore/provision/user_environment.py; tests/conftest.py
test_profile_write_replaces_the_line_of_a_set_name | keep | 9 | user_environment: a second write replaces the variable's line in place; file boundary | tests/provision/test_user_environment.py; source/sushicore/provision/user_environment.py; tests/conftest.py
test_profile_read_returns_what_was_written | split | 3 | two promises: a hostile value reads back unchanged, and the file escapes $ and the other special characters; the second is the file format, asserted on a second result | tests/provision/test_user_environment.py; source/sushicore/provision/user_environment.py; tests/conftest.py
test_profile_read_returns_none_without_a_file | keep | 9 | user_environment: a read from a missing file gives none and writes nothing; file boundary | tests/provision/test_user_environment.py; source/sushicore/provision/user_environment.py; tests/conftest.py
test_profile_read_ignores_an_export_outside_the_block | keep | 9 | user_environment: an export line outside the managed block is not read as stored; file boundary | tests/provision/test_user_environment.py; source/sushicore/provision/user_environment.py; tests/conftest.py
test_profile_remove_deletes_one_line | keep | 9 | user_environment: a remove deletes only the variable's line; file boundary | tests/provision/test_user_environment.py; source/sushicore/provision/user_environment.py; tests/conftest.py
test_profile_remove_of_the_last_variable_drops_the_markers | keep | 9 | user_environment: a block emptied by a remove leaves the file as it was before the write; file boundary | tests/provision/test_user_environment.py; source/sushicore/provision/user_environment.py; tests/conftest.py
test_profile_remove_of_an_unset_name_leaves_the_file_alone | merge | 4 | user_environment: remove of an absent name is not an error and writes nothing; merge with tests/provision/test_user_environment.py::test_registry_remove_of_an_unset_name_is_not_an_error into the one UserEnvironment contract suite | tests/provision/test_user_environment.py; source/sushicore/provision/user_environment.py; tests/conftest.py
test_default_store_is_used_when_none_is_passed | rewrite | 1 | forbidden kind: replaces the module's own default_environment; the only test of the promise; rewrite gives the three functions a platform parameter and asserts on the store it selects | tests/provision/test_user_environment.py; source/sushicore/provision/user_environment.py; tests/provision/conftest.py; tests/conftest.py
```

### `tests/provision/toolchains/test_adaptivecpp.py`

```
test_install_adaptivecpp_reuses_an_existing_binary | rewrite | 1 | fake_console spy (FakeConsole duplicated from the other toolchain tests; no in-memory console adapter in _output.py); carries: an existing binary is reused | tests/provision/toolchains/test_adaptivecpp.py; tests/provision/conftest.py; source/sushicore/provision/toolchains/adaptivecpp.py (def list); source/sushicore/provision/_output.py
test_install_adaptivecpp_skips_without_git_or_cmake | rewrite | 1 | fake_console spy and stub of adaptivecpp.shutil.which; carries: skips and warns without git or cmake | (same files)
test_install_adaptivecpp_dry_run_reports_without_building | rewrite | 1 | fake_console spy and stub of shutil.which; carries: a dry run reports the path and builds nothing | (same files)
test_find_windows_sdk_rc_dir_returns_empty_without_a_match | rewrite | 1 | private name _find_windows_sdk_rc_dir and stub of adaptivecpp._glob.glob (the glob module, process-wide); rewrite through install_adaptivecpp on Windows | (same files)
test_find_windows_sdk_rc_dir_returns_the_highest_sorting_match | rewrite | 1 | private name and stub of _glob.glob; rewrite as above; pairs with the empty-match test | (same files)
test_find_windows_llvm_finds_a_vendored_tree | rewrite | 1 | private name _find_windows_llvm; rewrite through the public install path | (same files)
test_find_windows_llvm_returns_none_when_nothing_is_installed | rewrite | 1 | private name and stub of pathlib.Path.is_dir (process-wide); rewrite through the public path | (same files)
test_confirm_timeout_returns_the_default_when_unanswered | rewrite | 1 | private name _confirm_timeout, builtins.input stub (stdin), and fake_console spy; rewrite with an injected reader | (same files)
test_confirm_timeout_machine_mode_uses_the_prompted_answer | rewrite | 1 | private name _confirm_timeout and a FakeConsole bound on the process-wide provider; rewrite | (same files)
test_acpp_deps_linux_without_a_manager_returns_no_llvm_dir | rewrite | 1 | private name _acpp_deps_linux; rewrite through install_adaptivecpp | (same files)
test_acpp_deps_linux_apt_installs_the_pinned_llvm_packages | rewrite | 1 | private name, stub of Path.is_dir (process-wide), fake_console spy; rewrite through the public path | (same files)
test_acpp_deps_linux_other_manager_translates_generic_packages | rewrite | 1 | private name and fake_console spy; rewrite through the public path | (same files)
test_acpp_deps_windows_reuses_an_existing_llvm | rewrite | 1 | private name; stubs private adaptivecpp._find_windows_llvm; fake_console spy; rewrite | (same files)
test_acpp_deps_windows_without_consent_skips_the_download | rewrite | 1 | private name; stubs private _find_windows_llvm; fake_console spy; rewrite | (same files)
test_explain_acpp_skip_windows_names_the_setup_command | rewrite | 1 | private name _explain_acpp_skip and fake_console spy; rewrite | (same files)
test_explain_acpp_skip_linux_names_the_dev_packages | rewrite | 1 | private name and fake_console spy; rewrite | (same files)
```

### `tests/provision/toolchains/test_intel_llvm.py`

```
test_install_intel_llvm_reuses_an_existing_bundle | rewrite | 1 | fake_console spy and stub of intel_llvm.gh_latest_release_asset; rewrite | tests/provision/toolchains/test_intel_llvm.py; tests/provision/conftest.py; source/sushicore/provision/toolchains/intel_llvm.py (def list); source/sushicore/provision/toolchains/stamp.py
test_install_intel_llvm_dry_run_reports_without_downloading | rewrite | 1 | fake_console spy; rewrite | (same files)
test_install_intel_llvm_refresh_skips_when_tag_unchanged | rewrite | 1 | fake_console spy and stubs of gh_latest_release_asset and download; rewrite | (same files)
test_install_intel_llvm_downloads_and_extracts_on_first_install | rewrite | 1 | fake_console spy, stubs of gh_latest_release_asset, download and private _extract_tar_gz; rewrite | (same files)
test_install_intel_llvm_returns_none_when_asset_resolution_fails | rewrite | 1 | fake_console spy and stub of gh_latest_release_asset; rewrite | (same files)
test_install_intel_llvm_cleans_up_on_download_failure_without_refresh | rewrite | 1 | fake_console spy and stubs; rewrite | (same files)
test_extract_tar_gz_collapses_a_single_top_level_wrapper_dir | rewrite | 1 | private name _extract_tar_gz; rewrite through install_intel_llvm with a real tar fixture | (same files)
test_extract_tar_gz_leaves_an_unwrapped_layout_alone | rewrite | 1 | private name _extract_tar_gz; rewrite as above, pairs with the wrapper test | (same files)
test_intel_llvm_defines_no_unused_private_function | delete | 1 | change detector: reads the module's source text and regex-counts private names; a lint that belongs to a tools/ checker, not a promise of the unit | tests/provision/toolchains/test_intel_llvm.py; source/sushicore/provision/toolchains/intel_llvm.py (read as text by the test)
```

### `tests/provision/toolchains/test_oneapi.py`

```
test_install_oneapi_noop_when_not_selected | rewrite | 1 | fake_console spy; rewrite with the in-memory console adapter | tests/provision/toolchains/test_oneapi.py; tests/provision/conftest.py; source/sushicore/provision/toolchains/oneapi.py (def list); source/sushicore/provision/_output.py
test_install_oneapi_noop_when_a_sycl_compiler_is_already_detected | rewrite | 1 | fake_console spy; rewrite | (same files)
test_install_oneapi_dry_run_skips_the_download | rewrite | 1 | fake_console spy; rewrite | (same files)
test_install_oneapi_fails_when_the_download_fails | rewrite | 1 | fake_console spy and stub of oneapi.download_oneapi_installer; rewrite | (same files)
test_install_oneapi_runs_the_installer_after_a_successful_download | rewrite | 1 | fake_console spy and stubs of download_oneapi_installer and run_oneapi_installer; rewrite | (same files)
test_download_oneapi_installer_reuses_an_existing_file | rewrite | 1 | fake_console spy and process-wide stub of pathlib.Path.home; rewrite | (same files)
test_download_oneapi_installer_downloads_with_curl | rewrite | 1 | fake_console spy; the subprocess stub is allowed (out-of-process, reached by this adapter); rewrite for the spy | (same files)
test_download_oneapi_installer_returns_none_on_curl_failure | rewrite | 1 | fake_console spy; rewrite | (same files)
test_run_oneapi_installer_reports_success | rewrite | 1 | fake_console spy; rewrite | (same files)
test_run_oneapi_installer_reports_failure | rewrite | 1 | fake_console spy; rewrite | (same files)
test_run_oneapi_installer_elevates_on_uac_required | rewrite | 1 | private name oneapi._ELEVATION_REQUIRED and fake_console spy; rewrite | (same files)
test_run_oneapi_installer_reports_a_non_elevation_launch_failure | rewrite | 1 | fake_console spy; rewrite | (same files)
test_run_oneapi_installer_reports_an_elevated_launch_exception | rewrite | 1 | private name oneapi._ELEVATION_REQUIRED and fake_console spy; rewrite | (same files)
```

### `tests/provision/toolchains/test_stamp.py`

```
test_missing_stamp_reads_empty | merge | 4 | merge with test_read_toolchain_stamp_returns_empty_on_invalid_json, _invalid_utf8 and _on_a_non_object_top_level into rows: read_toolchain_stamp returns {} for an absent, unreadable, non-JSON or non-object stamp | tests/provision/toolchains/test_stamp.py; source/sushicore/provision/toolchains/stamp.py
test_written_stamp_round_trips | keep | 9 | write_toolchain_stamp round-trips source and tag | tests/provision/toolchains/test_stamp.py; source/sushicore/provision/toolchains/stamp.py
test_adapter_commit_is_recorded_without_losing_the_tag | merge | 4 | merge with test_record_toolchain_adapter_keeps_the_existing_source_and_tag into rows over vendor and tag: record_toolchain_adapter records the commit and keeps source and tag | (same files)
test_toolchains_dir_follows_the_root | delete | 4 | the same promise is tested in tests/provision/test_home.py::test_subdirectories_hang_off_the_root, which owns the path; stamp.toolchains_dir only delegates to home.toolchains_dir | tests/provision/toolchains/test_stamp.py; tests/provision/test_home.py; source/sushicore/provision/toolchains/stamp.py; source/sushicore/provision/home.py
test_write_toolchain_stamp_keeps_an_existing_adapters_key | keep | 9 | write_toolchain_stamp keeps an existing adapters key | tests/provision/toolchains/test_stamp.py; source/sushicore/provision/toolchains/stamp.py
test_record_toolchain_adapter_keeps_the_existing_source_and_tag | merge | 4 | merge with test_adapter_commit_is_recorded_without_losing_the_tag into the same rows | (same files)
test_toolchain_adapter_commit_reads_back_a_recorded_commit | keep | 9 | toolchain_adapter_commit reads back a recorded commit and None for another vendor | tests/provision/toolchains/test_stamp.py; source/sushicore/provision/toolchains/stamp.py
test_read_toolchain_stamp_returns_empty_on_invalid_json | merge | 4 | merge with test_missing_stamp_reads_empty into the read_toolchain_stamp empty-dict rows | (same files)
test_read_toolchain_stamp_returns_empty_on_invalid_utf8 | merge | 4 | merge with test_missing_stamp_reads_empty into the same rows; note: read_text() has no encoding, so on Windows the bytes decode as cp1252 and fail as JSON, not as UTF-8; the row's name overstates the check | (same files)
test_read_toolchain_stamp_returns_empty_on_a_non_object_top_level | merge | 4 | merge with test_missing_stamp_reads_empty into the same rows | (same files)
test_toolchain_adapter_commit_treats_a_non_dict_adapters_as_absent | keep | 9 | toolchain_adapter_commit treats a non-dict adapters value as absent | (same files)
test_record_toolchain_adapter_replaces_a_non_dict_adapters | keep | 9 | record_toolchain_adapter replaces a non-dict adapters value | (same files)
test_write_toolchain_stamp_is_atomic_via_a_temp_file_and_replace | rewrite | 5 | asserts the internal call sequence of os.replace (temp name, then stamp name): a change detector, it fails on a refactor that keeps the promise; rewrite against the promise that a failed write leaves the previous stamp readable | tests/provision/toolchains/test_stamp.py; source/sushicore/provision/toolchains/stamp.py
test_a_failing_replace_removes_the_temp_file | keep | 9 | write_toolchain_stamp: a failing replace leaves no temp file and no stamp | (same files)
```

### `tests/test_aliases.py`

```
test_alias_notice_names_both_spellings_and_the_date | resize | 8 | a dated alias notice names both spellings and the date; a pure value, so small sees it | tests/conftest.py;tests/test_aliases.py;source/sushicore/aliases.py
test_alias_announces_once_to_a_terminal_only | resize | 8 | announce once per table, to a terminal only; announce reads the switch from os.environ, so the switch must be passed in as a value before small sees it (seam: the switch as a parameter) | tests/conftest.py;tests/test_aliases.py;source/sushicore/aliases.py
test_alias_stays_silent_when_switched_off_or_permanent | split | 3 | (a) a permanent alias prints nothing; (b) the switch silences a dated alias; two results of two calls, one test per promise | tests/conftest.py;tests/test_aliases.py;source/sushicore/aliases.py
test_alias_command_runs_the_new_command_and_is_hidden | split | 3 | (a) the old word runs the new callback, a typer run at medium; (b) hidden from the catalogue is already checked by tests/test_describe.py::test_describe_prints_the_catalogue_without_hidden_commands at the same size, so that half is deleted | tests/conftest.py;tests/test_aliases.py;source/sushicore/aliases.py;source/sushicore/describe.py;tests/test_describe.py
test_alias_table_reports_unknown_and_expired_rows | split | 3 | (a) an unknown spelling raises; (b) rows past their date are listed as expired; two results of two calls | tests/conftest.py;tests/test_aliases.py;source/sushicore/aliases.py
```

### `tests/test_brand.py`

```
test_every_mark_row_has_the_same_width | keep | 9 | the mark is one rectangle, a data invariant of the grid that no sibling checks | tests/conftest.py;tests/test_brand.py;source/sushicore/brand.py
test_every_wordmark_row_has_the_same_width | keep | 9 | the wordmark is one rectangle, a data invariant of the grid | tests/conftest.py;tests/test_brand.py;source/sushicore/brand.py
test_the_mark_has_an_even_number_of_rows | delete | 1 | a test of an artwork constant; source/sushicore/ui/logo.py pads an odd grid (lines 58 and 73), so no code promise needs evenness | tests/conftest.py;tests/test_brand.py;source/sushicore/brand.py;source/sushicore/ui/logo.py
test_the_wordmark_has_an_even_number_of_rows | delete | 1 | the same artwork constant; source/sushicore/ui/logo.py pads odd grids | tests/conftest.py;tests/test_brand.py;source/sushicore/brand.py;source/sushicore/ui/logo.py
test_the_mark_stays_small_enough_for_a_help_screen | delete | 1 | a constant compared with a test-local limit; help fit is checked on choose_logo widths in tests/help/test_logo_choice.py | tests/conftest.py;tests/test_brand.py;source/sushicore/brand.py;tests/help/test_logo_choice.py
test_the_wordmark_has_sixteen_rows | delete | 1 | equates a constant with a test-local copy of it | tests/conftest.py;tests/test_brand.py;source/sushicore/brand.py
test_the_wordmark_stays_short_enough_to_sit_beside_the_mark | delete | 1 | a constant compared with test-local limits | tests/conftest.py;tests/test_brand.py;source/sushicore/brand.py
test_one_blank_column_separates_the_letters_and_two_blank_rows_the_lines | delete | 1 | the expected layout is K_LINE_LETTERS, pasted from the current artwork; artwork, not code | tests/conftest.py;tests/test_brand.py;source/sushicore/brand.py
test_these_letters_read_the_same_mirrored_left_to_right | delete | 1 | one parametrised test of the artwork symmetry of pasted letter lists (6 cases) | tests/conftest.py;tests/test_brand.py;source/sushicore/brand.py
test_the_s_reads_the_same_after_a_half_turn | delete | 1 | artwork symmetry of pasted letter lists | tests/conftest.py;tests/test_brand.py;source/sushicore/brand.py
test_the_mark_uses_only_brand_keys_glow_keys_and_the_transparent_key | keep | 9 | a grid key without a colour has no colour to draw with | tests/conftest.py;tests/test_brand.py;source/sushicore/brand.py;source/sushicore/ui/logo.py
test_the_wordmark_uses_only_the_foreground_key_amber_and_the_transparent_key | keep | 9 | the wordmark keys have a colour or the foreground key | tests/conftest.py;tests/test_brand.py;source/sushicore/brand.py;source/sushicore/ui/logo.py
test_every_palette_key_appears_in_one_of_the_grids | delete | 2 | an unused palette key draws nothing wrong; no defect follows if it breaks | tests/conftest.py;tests/test_brand.py;source/sushicore/brand.py
test_palette_values_are_lowercase_hex_colours | keep | 9 | palette values are the colour strings the grid is drawn with | tests/conftest.py;tests/test_brand.py;source/sushicore/brand.py
test_the_palette_names_the_four_brand_keys | delete | 1 | pins the key set to a copied literal | tests/conftest.py;tests/test_brand.py;source/sushicore/brand.py
test_the_glow_palette_names_the_inner_and_outer_ring | delete | 1 | pins the key set to a copied literal | tests/conftest.py;tests/test_brand.py;source/sushicore/brand.py
test_the_foreground_key_is_not_a_palette_key | keep | 9 | the terminal-foreground key must not collide with a palette key, or a colour changes meaning | tests/conftest.py;tests/test_brand.py;source/sushicore/brand.py
```

### `tests/test_build_admission.py`

```
test_the_launcher_runs_the_gate_script_with_the_trees_state_folder | rewrite | 8 | the defines are a value promise that fits small, but the assertion gate_script().is_file() reaches a file from a small test; rewrite without the file check | tests/conftest.py;tests/test_build_admission.py;source/sushicore/build_admission.py
test_a_build_is_refused_while_the_gate_is_stopped | split | 3 | (a) stop_file is the gate's K_STOP under the state folder, small; (b) refusal while the stop file exists needs a real file, medium | tests/conftest.py;tests/test_build_admission.py;source/sushicore/build_admission.py;source/sushicore/build_gate.py
test_the_launcher_names_the_cache_only_when_there_is_one | keep | 9 | the cache is named in the launcher only when one is given | tests/conftest.py;tests/test_build_admission.py;source/sushicore/build_admission.py
test_a_configured_cache_that_is_missing_is_not_used | resize | 8 | the decision depends on a real file's existence; medium is the smallest size that sees it | tests/conftest.py;tests/test_build_admission.py;source/sushicore/build_admission.py
test_time_trace_requests_are_written_as_the_gate_keys_a_unit_and_cleared | rewrite | 1 | reaches the private name build_gate._requested_units (a forbidden kind), writes and removes files in small, and holds two actions; rewrite through a public read and split | tests/conftest.py;tests/test_build_admission.py;source/sushicore/build_admission.py;source/sushicore/build_gate.py
```

### `tests/test_build_env.py`

```
test_without_device_selection_drops_every_listed_variable | resize | 8 | a pure value filter; small sees it | tests/conftest.py;tests/test_build_env.py;source/sushicore/build_env.py
test_without_device_selection_keeps_the_toolchain_entries | resize | 8 | a pure value filter; small sees it | tests/conftest.py;tests/test_build_env.py;source/sushicore/build_env.py
test_without_device_selection_ignores_case | resize | 8 | a pure value filter; small sees it | tests/conftest.py;tests/test_build_env.py;source/sushicore/build_env.py
test_a_dumped_shell_environment_loses_only_the_device_choice | resize | 8 | parse_windows_set and the filter are both values; small sees it | tests/conftest.py;tests/test_build_env.py;source/sushicore/build_env.py
test_without_caller_choices_drops_the_scratch_folder_and_the_device | split | 3 | "and" joins two results that can break apart: the scratch folder is dropped, the device is dropped | tests/conftest.py;tests/test_build_env.py;source/sushicore/build_env.py
test_a_callers_scratch_folder_survives_a_cached_snapshot | resize | 8 | the promise is merge_env over the snapshot dict; the file read adds nothing to it | tests/conftest.py;tests/test_build_env.py;source/sushicore/build_env.py
test_a_cache_written_before_this_existed_heals_on_read | resize | 8 | healing is without_caller_choices on the parsed snapshot, reachable as values; the round trip is covered by test_a_cache_still_round_trips_what_the_build_needs | tests/conftest.py;tests/test_build_env.py;source/sushicore/build_env.py
test_a_cache_still_round_trips_what_the_build_needs | keep | 9 | the round trip through a real file is the boundary; medium is right | tests/conftest.py;tests/test_build_env.py;source/sushicore/build_env.py
test_the_current_environment_still_reaches_a_subprocess | rewrite | 7 | the name says a subprocess is reached and none is started; the body checks that a caller's device choice survives merge_env; rename to the promise, then resize to small | tests/conftest.py;tests/test_build_env.py;source/sushicore/build_env.py
test_snapshot_vcvars_names_the_path_and_drops_device_selection | rewrite | 1 | stand-in _Console written by the test for the console port; in-memory adapter needed: sushicore.console.Console over renderer.PlainRenderer(stream=io.StringIO()); the subprocess fake is allowed, the adapter reaches the process | tests/conftest.py;tests/test_build_env.py;source/sushicore/build_env.py;source/sushicore/console.py;source/sushicore/renderer.py
test_snapshot_vcvars_warns_and_returns_none_on_failure | rewrite | 1 | stand-in _Console for the console port; same in-memory adapter as above | tests/conftest.py;tests/test_build_env.py;source/sushicore/build_env.py;source/sushicore/console.py;source/sushicore/renderer.py
test_snapshot_windows_keeps_its_own_command_and_messages | rewrite | 1 | stand-in _Console for the console port and a SimpleNamespace stand-in for ToolConfig, a repository type; use a real ToolConfig and the in-memory console adapter | tests/conftest.py;tests/test_build_env.py;source/sushicore/build_env.py;source/sushicore/config_base.py;source/sushicore/console.py;source/sushicore/renderer.py
test_a_cache_that_cannot_be_written_is_recorded | keep | 9 | a file the OS refuses is a real boundary, medium is right; the warning is read through caplog on the module logger, which medium allows | tests/conftest.py;tests/test_build_env.py;source/sushicore/build_env.py
```

### `tests/test_build_gate.py`

```
test_an_edge_that_fits_is_admitted_and_reserved | rewrite | 1 | the everyone_alive fixture replaces the repository function build_gate.alive; the liveness check should be a value passed to admit | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
test_an_edge_that_does_not_fit_waits_until_the_running_ones_end | rewrite | 1 | replaces build_gate.alive inside the test; holds two results (waits, then admitted), split when rewritten | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
test_an_edge_alone_is_admitted_whatever_its_peak | rewrite | 1 | requests everyone_alive, which replaces build_gate.alive, but an empty ledger never calls it; drop the fixture | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
test_a_light_edge_passes_a_waiting_heavy_head_only_inside_the_backfill_window | rewrite | 1 | replaces build_gate.alive; several steps in one test (heavy waits, light passes, light after the window refused), split | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
test_nothing_is_admitted_beside_running_work_when_free_memory_is_under_the_reserve | rewrite | 1 | replaces build_gate.alive through the fixture | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
test_edges_are_told_apart_and_keyed_by_source_or_output | rewrite | 7 | four asserts over four inputs of one promise (edge_of); rows | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
test_a_measured_unit_is_reserved_at_its_own_peak | merge | 4 | merge with tests/test_build_gate.py::test_a_unit_measured_before_keeps_its_own_peak_whatever_the_kind_shows; the same promise, the other case has the richer state | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
test_a_new_unit_is_reserved_at_the_larger_of_its_kinds_default_and_largest_peak_while_few_are_measured | rewrite | 7 | three asserts over three inputs of expected_peak; rows | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
test_a_well_measured_kind_reserves_headroom_over_its_largest_peak_not_the_default | rewrite | 7 | two inputs of one headroom formula; rows | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
test_headroom_never_exceeds_the_default_and_never_falls_below_the_largest_peak | rewrite | 7 | two inputs of the bounds on headroom; rows | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
test_a_unit_measured_before_keeps_its_own_peak_whatever_the_kind_shows | keep | 9 | the surviving case for test_a_measured_unit_is_reserved_at_its_own_peak: a measured unit keeps its own peak when its kind is well measured | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
test_a_peak_counts_its_unit_once_and_keeps_the_largest | split | 3 | "and" joins the count and the largest peak, two results that can break apart | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
test_a_gated_command_runs_returns_its_code_and_leaves_the_ledger_empty | rewrite | 1 | a small test starts a child process and writes a state folder, and holds a platform if in its body; the process and the file belong to medium | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
test_memory_freed_by_another_program_during_the_build_is_used | rewrite | 1 | replaces build_gate.alive through everyone_alive | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
test_a_stopped_gate_fails_the_edge_without_running_it | rewrite | 1 | a small test writes the stop file and starts a child process; medium | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
test_a_cache_setting_the_environment_makes_is_kept | rewrite | 1 | monkeypatch.setenv in a small test; cached() should take its environment as a value | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
test_only_a_host_compile_runs_through_the_compiler_cache | rewrite | 1 | monkeypatch.delenv in a small test; three promises in one test (host only, default folder, empty cache); split when rewritten | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
test_a_cache_option_reaches_the_gated_command | rewrite | 1 | replaces the repository function build_gate.run with a lambda; pass the runner in or check the argv | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
test_only_a_compile_of_a_requested_unit_is_traced | rewrite | 7 | five asserts over inputs of wants_time_trace; rows | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
test_a_requested_compile_runs_with_the_time_trace_flag_and_skips_the_cache | rewrite | 1 | a small test reads the time-trace file; pass the requested set to run as a value; the subprocess.call fake is fine at medium | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
test_a_host_object_that_instantiates_a_kernel_submission_is_found | rewrite | 1 | a small test writes an object file (3 cases); seam: a bytes function under kernel_submission_in | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
test_a_host_object_without_one_passes | rewrite | 1 | a small test writes a file and reads a missing one; seam: the bytes function | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
test_an_elf_object_that_defines_a_kernel_submission_is_found | rewrite | 1 | writes an ELF file in small; defined_symbols(bytes) is already public and takes the bytes | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
test_an_elf_object_whose_debug_information_names_a_submission_passes | rewrite | 1 | writes an ELF file in small; defined_symbols(bytes) takes the bytes | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
test_an_elf_object_that_only_references_a_submission_passes | rewrite | 1 | writes an ELF file in small; defined_symbols(bytes) takes the bytes | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
test_a_coff_object_is_judged_by_the_symbols_it_defines | rewrite | 1 | writes two COFF files in small; defined_symbols(bytes) takes the bytes | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
test_a_host_compile_that_instantiates_a_kernel_fails_and_loses_its_object | rewrite | 1 | a small test runs a child process and writes a file; medium | tests/conftest.py;tests/test_build_gate.py;source/sushicore/build_gate.py
```

### `tests/test_build_report.py`

```
test_edges_are_read_from_the_offset_once_per_command | rewrite | 1 | a small test writes three files; holds several promises (offset, one edge per command, classification, summary, write and read); split, with the file parts at medium | tests/conftest.py;tests/test_build_report.py;source/sushicore/build_report.py
test_link_outputs_and_stamps_are_told_apart | rewrite | 7 | two classify calls over two inputs of one promise; rows | tests/conftest.py;tests/test_build_report.py;source/sushicore/build_report.py
test_the_count_of_a_kinds_units_is_neither_a_unit_nor_a_kind | keep | 9 | count keys stay out of kinds and the heaviest list; pure | tests/conftest.py;tests/test_build_report.py;source/sushicore/build_report.py
test_the_reserved_prefixes_equal_those_of_the_gate | keep | 9 | guards a constant duplicated across two modules; the better fix is one shared constant | tests/conftest.py;tests/test_build_report.py;source/sushicore/build_report.py;source/sushicore/build_gate.py
```

### `tests/test_build_trace.py`

```
test_headers_are_summed_across_units_and_count_each_unit_once | rewrite | 1 | writes trace files in small; seam: _add reads events, summarise runs over event values | tests/conftest.py;tests/test_build_trace.py;source/sushicore/build_trace.py
test_templates_and_unit_times_are_read | rewrite | 1 | writes trace files in small; same seam | tests/conftest.py;tests/test_build_trace.py;source/sushicore/build_trace.py
test_a_json_file_without_an_object_beside_it_is_ignored | rewrite | 1 | writes files in small; same seam | tests/conftest.py;tests/test_build_trace.py;source/sushicore/build_trace.py
test_a_broken_trace_is_skipped | rewrite | 1 | writes files in small; the assertion is an or of two outcomes, so it passes on either | tests/conftest.py;tests/test_build_trace.py;source/sushicore/build_trace.py
test_lines_rank_headers_and_templates_and_list_units_slowest_first | rewrite | 1 | writes files in small; index assertions on lines | tests/conftest.py;tests/test_build_trace.py;source/sushicore/build_trace.py
test_no_traces_gives_one_line | rewrite | 1 | reads an empty folder in small; TraceSummary().lines() is the pure door | tests/conftest.py;tests/test_build_trace.py;source/sushicore/build_trace.py
```

### `tests/test_build_tree.py`

```
test_a_tree_is_named_by_its_type | rewrite | 1 | asserts a default value (K_DEFAULT_BUILD_TYPE == Debug), a forbidden kind; keep the tree_dir naming | tests/conftest.py;tests/test_build_tree.py;source/sushicore/build_tree.py
test_a_tree_of_one_type_refuses_another | rewrite | 1 | writes CMakeCache.txt in small and holds several cases; rows, with the file case at medium | tests/conftest.py;tests/test_build_tree.py;source/sushicore/build_tree.py;source/sushicore/cmake_cache.py
test_the_type_is_never_set_through_a_define | keep | 9 | the define check raises before any file is read | tests/conftest.py;tests/test_build_tree.py;source/sushicore/build_tree.py
test_a_debug_or_sanitized_consumer_links_release_packages | rewrite | 7 | five asserts over five inputs of package_build_type; rows | tests/conftest.py;tests/test_build_tree.py;source/sushicore/build_tree.py
```

### `tests/test_citations.py`

```
test_rewrite_ids_leaves_a_sibling_s_id_alone | resize | 8 | a pure string rewrite; small sees it | tests/conftest.py;tests/test_citations.py;source/sushicore/citations.py
test_repair_text_moves_a_path_a_link_and_a_literal | keep | 9 | path resolution and existence are real file reads; medium | tests/conftest.py;tests/test_citations.py;source/sushicore/citations.py
test_repair_text_places_a_gone_document_in_its_topic | keep | 9 | placement uses real file existence; medium | tests/conftest.py;tests/test_citations.py;source/sushicore/citations.py
test_citing_files_skip_the_archive_and_the_shared_tools | keep | 9 | walks a real tree and asks git check-ignore; medium | tests/conftest.py;tests/test_citations.py;source/sushicore/citations.py
test_repair_citations_writes_only_with_apply | keep | 9 | writes files in both modes; medium | tests/conftest.py;tests/test_citations.py;source/sushicore/citations.py
```

### `tests/test_cli_console.py`

```
test_build_console_machine_uses_the_json_renderer | delete | 1 | reaches the private name console._renderer, a forbidden kind; the promise is checked in tests/test_renderer/test_console_semantics.py::test_console_is_machine_is_true_for_a_json_renderer and in tests/test_config.py::test_a_console_built_from_a_bad_theme_works_and_says_so | tests/conftest.py;tests/test_cli_console.py;source/sushicore/cli_console.py;tests/test_renderer/test_console_semantics.py;tests/test_config.py
test_lazy_console_reads_machine_at_first_build | resize | 8 | build_console reads the environment through load_appearance; medium is the smallest size that sees it | tests/conftest.py;tests/test_cli_console.py;source/sushicore/cli_console.py;source/sushicore/__init__.py
test_lazy_console_exposes_the_new_names | resize | 8 | attribute() builds the console, so the environment is read; medium | tests/conftest.py;tests/test_cli_console.py;source/sushicore/cli_console.py;source/sushicore/__init__.py
test_lazy_console_is_machine_true_when_machine_flag_is_set | merge | 4 | merge with test_lazy_console_is_machine_false_when_machine_flag_is_unset; rows over the flag | tests/conftest.py;tests/test_cli_console.py;source/sushicore/cli_console.py
test_lazy_console_is_machine_false_when_machine_flag_is_unset | merge | 4 | merge with test_lazy_console_is_machine_true_when_machine_flag_is_set; rows over the flag | tests/conftest.py;tests/test_cli_console.py;source/sushicore/cli_console.py
test_lazy_console_layers_extra_files_below_the_directory_files | keep | 9 | the order of sources() on values, with no file read | tests/conftest.py;tests/test_cli_console.py;source/sushicore/cli_console.py
test_lazy_console_still_reads_extra_files_outside_a_checkout | keep | 9 | outside a checkout only the extra paths are listed; values only | tests/conftest.py;tests/test_cli_console.py;source/sushicore/cli_console.py
test_lazy_console_takes_a_theme_from_a_file_it_was_given | rewrite | 1 | writes a file and builds a console in small (the environment); the file-to-spec step is in tests/test_config.py::test_known_values_raise_no_warning, the console mapping only here; rewrite against AppearanceSpec and Theme values | tests/conftest.py;tests/test_cli_console.py;source/sushicore/cli_console.py;tests/test_config.py;source/sushicore/theme.py
```

### `tests/test_cmake_cache.py`

```
test_cached_value_reads_an_entry | keep | 9 | reads a real cache file; medium | tests/conftest.py;tests/test_cmake_cache.py;source/sushicore/cmake_cache.py
test_cached_value_is_none_for_an_absent_entry | keep | 9 | reads a real cache file; medium | tests/conftest.py;tests/test_cmake_cache.py;source/sushicore/cmake_cache.py
test_cached_value_is_none_for_an_unconfigured_tree | keep | 9 | reads a real tree; medium | tests/conftest.py;tests/test_cmake_cache.py;source/sushicore/cmake_cache.py
test_a_prefix_does_not_match_a_longer_entry | keep | 9 | the exact entry name is matched; medium | tests/conftest.py;tests/test_cmake_cache.py;source/sushicore/cmake_cache.py
test_home_directory_is_the_configured_source_path | keep | 9 | the configured source path is read from a real cache; medium | tests/conftest.py;tests/test_cmake_cache.py;source/sushicore/cmake_cache.py
test_a_tree_from_another_path_is_stale | merge | 4 | merge with test_a_tree_from_this_path_is_not_stale and test_an_unconfigured_tree_is_not_stale; is_stale over three inputs | tests/conftest.py;tests/test_cmake_cache.py;source/sushicore/cmake_cache.py
test_a_tree_from_this_path_is_not_stale | merge | 4 | merge with test_a_tree_from_another_path_is_stale and test_an_unconfigured_tree_is_not_stale | tests/conftest.py;tests/test_cmake_cache.py;source/sushicore/cmake_cache.py
test_an_unconfigured_tree_is_not_stale | merge | 4 | merge with test_a_tree_from_another_path_is_stale and test_a_tree_from_this_path_is_not_stale | tests/conftest.py;tests/test_cmake_cache.py;source/sushicore/cmake_cache.py
test_the_sentinel_follows_the_generator | resize | 8 | a pure lookup; small sees it | tests/conftest.py;tests/test_cmake_cache.py;source/sushicore/cmake_cache.py
```

### `tests/test_cmake_driver.py`

```
test_cmake_defaults_to_the_bare_name | rewrite | 1 | stand-in _Runner for the Runner port and a SimpleNamespace stand-in for ToolConfig, both written by the test; in-memory Runner needed in sushicore.proc (none exists) and the real ToolConfig | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py
test_compile_builds_the_expected_argv | rewrite | 1 | _Runner spy records argv for the Runner port; in-memory Runner needed in sushicore.proc; rows with the target and parallel cases | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py
test_compile_appends_targets | rewrite | 1 | _Runner spy for the Runner port; in-memory Runner needed; rows | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py
test_ctest_run_is_drained_and_carries_the_knobs | rewrite | 1 | _Runner spy records run_drained for the Runner port; in-memory Runner needed | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py
test_ctest_run_leaves_out_the_excluded_labels | rewrite | 1 | _Runner spy for the Runner port; in-memory Runner needed | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py
test_ctest_run_writes_a_junit_file_when_asked | rewrite | 1 | _Runner spy for the Runner port; in-memory Runner needed | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py
test_ctest_run_omits_absent_knobs | rewrite | 1 | _Runner spy for the Runner port; in-memory Runner needed | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py
test_needs_configure_when_there_is_no_tree | rewrite | 1 | stand-in _Console and _Runner, both unused by this call; in-memory console adapter and Runner needed | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py;source/sushicore/console.py;source/sushicore/renderer.py
test_needs_configure_when_the_sentinel_is_missing | rewrite | 1 | stand-ins _Console and _Runner, unused by this call; the same adapters as above | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py;source/sushicore/console.py;source/sushicore/renderer.py
test_no_reconfigure_when_expectations_hold | rewrite | 1 | stand-ins _Console and _Runner written for the ports; writes files | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py;source/sushicore/console.py;source/sushicore/renderer.py;source/sushicore/cmake_cache.py
test_reconfigure_when_an_expectation_is_violated | rewrite | 1 | stand-ins _Console and _Runner written for the ports; writes files | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py;source/sushicore/console.py;source/sushicore/renderer.py;source/sushicore/cmake_cache.py
test_root_mismatch_forces_reconfigure_and_warns | rewrite | 1 | _Console spy asserts the warning text on console.lines; in-memory console adapter needed | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/console.py;source/sushicore/renderer.py;source/sushicore/cmake_cache.py
test_root_match_does_not_reconfigure_or_warns | rewrite | 1 | _Console spy asserts no lines; in-memory console adapter needed | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/console.py;source/sushicore/renderer.py;source/sushicore/cmake_cache.py
test_clean_tree_says_so_when_there_is_nothing_to_clean | rewrite | 1 | _Console spy asserts the message; in-memory console adapter needed | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/console.py;source/sushicore/renderer.py
test_clean_tree_removes_the_directory_it_is_given | rewrite | 1 | stand-ins _Console and _Runner, unused by the removal; in-memory adapters needed | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py;source/sushicore/console.py;source/sushicore/renderer.py
test_clean_tree_removes_only_that_directory | rewrite | 1 | stand-ins _Console and _Runner, unused by the removal; in-memory adapters needed | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py;source/sushicore/console.py;source/sushicore/renderer.py
test_clean_tree_reports_a_tree_that_is_still_there | rewrite | 1 | _Console spy asserts the error text; the rmtree fake is allowed (the adapter reaches the file system); in-memory console adapter needed | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/console.py;source/sushicore/renderer.py
test_clean_tree_returns_true_for_a_removed_and_for_an_absent_tree | rewrite | 1 | stand-ins _Console and _Runner, unused by the call; in-memory adapters needed | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py;source/sushicore/console.py;source/sushicore/renderer.py
test_doxygen_passes_a_path_relative_to_cwd | rewrite | 1 | _Runner spy records the doxygen argv for the Runner port; in-memory Runner needed | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py
test_doxygen_derives_a_nested_relative_path | rewrite | 1 | _Runner spy for the Runner port; in-memory Runner needed | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py
test_doxygen_not_found_names_the_absolute_path | rewrite | 1 | _Console spy and _Runner stand-in for the missing Doxyfile message; in-memory adapters needed | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py;source/sushicore/console.py;source/sushicore/renderer.py
test_compile_places_parallel_before_targets | rewrite | 1 | _Runner spy for the Runner port; in-memory Runner needed | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py
test_ctest_run_appends_parallel_and_config_in_order | rewrite | 1 | _Runner spy for the Runner port; in-memory Runner needed | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py
test_ctest_run_passes_parallel_for_a_single_job | rewrite | 1 | _Runner spy for the Runner port; in-memory Runner needed | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py
test_configure_drops_the_cache_when_the_compiler_path_changed | rewrite | 1 | _Runner spy for the Runner port; the only test of the compiler-path branch; in-memory Runner needed | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py;source/sushicore/cmake_cache.py
test_configure_keeps_the_cache_when_only_the_spelling_of_the_path_differs | rewrite | 1 | stand-in _Runner unused by the call; a ternary on os.name in the body, a control flow kind | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py;source/sushicore/cmake_cache.py
test_configure_keeps_the_cache_when_no_compiler_is_named | rewrite | 1 | stand-in _Runner unused by the call; in-memory Runner needed | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py;source/sushicore/cmake_cache.py
test_compile_hands_the_compilers_a_scratch_folder_in_the_tree | rewrite | 1 | _ScratchRunner stand-in for the Runner port, with an assert in its body | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py
test_compile_empties_the_scratch_folder_when_the_build_ends | rewrite | 1 | _ScratchRunner stand-in for the Runner port | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py
test_compile_empties_the_scratch_folder_when_the_build_fails | rewrite | 1 | _ScratchRunner stand-in whose run raises | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py
test_ctest_run_hands_the_shuffle_seed_to_the_tests_through_the_environment | rewrite | 1 | _Runner spy records the environment for the Runner port; two actions in one test, split when rewritten | tests/conftest.py;tests/test_cmake_driver.py;source/sushicore/cmake_driver.py;source/sushicore/proc.py
```

### `tests/test_command_groups.py`

```
test_the_groups_are_backlog_then_design | delete | 1 | pins two constants to literals; no behaviour | tests/conftest.py;tests/test_command_groups.py;source/sushicore/command_groups.py
test_an_app_with_neither_group_lacks_both | merge | 4 | merge with test_an_app_with_one_command_and_no_callback_exposes_nothing; both assert missing_groups on an app with no group | tests/conftest.py;tests/test_command_groups.py;source/sushicore/command_groups.py
test_an_app_that_registered_a_group_through_sushicore_exposes_it | keep | 9 | real registration of both groups; medium | tests/conftest.py;tests/test_command_groups.py;source/sushicore/command_groups.py
test_a_caller_can_ask_for_another_set_of_names | keep | 9 | the caller's names are checked; a different input from the other tests | tests/conftest.py;tests/test_command_groups.py;source/sushicore/command_groups.py
test_an_app_with_one_command_and_no_callback_exposes_nothing | merge | 4 | merge with test_an_app_with_neither_group_lacks_both | tests/conftest.py;tests/test_command_groups.py;source/sushicore/command_groups.py
```

### `tests/test_config.py`

```
test_background_defaults_to_auto | delete | 1 | asserts a default value, a forbidden kind; the auto fallback is covered by the parametrised fallback test, background row | tests/conftest.py;tests/test_config.py;source/sushicore/config.py
test_the_cli_table_sets_the_background | keep | 9 | the [cli] background is read from a file; medium | tests/conftest.py;tests/test_config.py;source/sushicore/config.py
test_the_platform_table_overrides_the_common_one | keep | 9 | the platform table wins over the common one; medium | tests/conftest.py;tests/test_config.py;source/sushicore/config.py
test_the_environment_overrides_the_file | keep | 9 | the environment wins over the file; medium | tests/conftest.py;tests/test_config.py;source/sushicore/config.py
test_an_unknown_background_falls_back_to_auto | merge | 4 | merge with the parametrised test_every_unknown_appearance_value_falls_back_and_warns_once, background row | tests/conftest.py;tests/test_config.py;source/sushicore/config.py
test_a_console_reports_the_background_it_was_built_with | delete | 4 | tests/test_console.py::test_properties_expose_the_bound_parts checks the same dark_background at a smaller size, in another file | tests/conftest.py;tests/test_config.py;source/sushicore/console.py;tests/test_console.py
test_a_console_assumes_a_light_background_by_default | delete | 1 | a constructor default, a default value; the build path is covered by test_build_console_without_a_setting_or_colorfgbg_is_not_dark | tests/conftest.py;tests/test_config.py;source/sushicore/console.py
test_build_console_takes_the_background_from_the_config | keep | 9 | build_console passes the config's background through; medium | tests/conftest.py;tests/test_config.py;source/sushicore/__init__.py;source/sushicore/config.py
test_build_console_falls_back_to_colorfgbg | keep | 9 | the COLORFGBG fallback reaches the console; medium | tests/conftest.py;tests/test_config.py;source/sushicore/__init__.py
test_build_console_without_a_setting_or_colorfgbg_is_not_dark | keep | 9 | with no setting and no COLORFGBG the console is not dark; medium | tests/conftest.py;tests/test_config.py;source/sushicore/__init__.py
test_every_unknown_appearance_value_falls_back_and_warns_once | split | 3 | "falls back and warns once": the fallback value and the single warning are two results that can break apart; four cases | tests/conftest.py;tests/test_config.py;source/sushicore/config.py
test_known_values_raise_no_warning | keep | 9 | known values give no warning; medium | tests/conftest.py;tests/test_config.py;source/sushicore/config.py
test_a_bad_value_from_the_environment_is_handled_the_same_way | keep | 9 | the environment branch of load_appearance is its own code path | tests/conftest.py;tests/test_config.py;source/sushicore/config.py
test_a_console_built_from_a_bad_theme_works_and_says_so | split | 3 | "works" and "says so": the warning event is the promise; the build half is the exception path | tests/conftest.py;tests/test_config.py;source/sushicore/__init__.py;source/sushicore/config.py
```

### `tests/test_config_base.py`

```
test_a_sibling_table_survives_a_tool_write | keep | 9 | a sibling table survives a write; medium | tests/conftest.py;tests/test_config_base.py;source/sushicore/config_base.py;source/sushicore/workspace.py
test_the_platform_sub_table_still_survives | keep | 9 | the platform sub-table survives verbatim; medium | tests/conftest.py;tests/test_config_base.py;source/sushicore/config_base.py;source/sushicore/workspace.py
test_a_non_string_in_a_sibling_table_is_refused | keep | 9 | a value the emitter cannot render raises rather than disappearing; medium | tests/conftest.py;tests/test_config_base.py;source/sushicore/config_base.py;source/sushicore/toml_writer.py
test_the_document_writer_renders_every_table_it_is_given | keep | 9 | every table is written, tool first; medium | tests/conftest.py;tests/test_config_base.py;source/sushicore/config_base.py;source/sushicore/toml_writer.py
```

### `tests/test_console.py`

```
test_each_level_uses_its_style_and_icon | rewrite | 1 | stand-in _Renderer spy records calls for the Renderer port; in-memory adapter: PlainRenderer over io.StringIO in renderer.py, not yet designated the shared adapter | tests/conftest.py;tests/test_console.py;source/sushicore/console.py;source/sushicore/renderer.py;source/sushicore/theme.py;source/sushicore/icons.py
test_a_flat_table_does_not_pass_group_by | rewrite | 1 | same _Renderer spy; same in-memory adapter | tests/conftest.py;tests/test_console.py;source/sushicore/console.py;source/sushicore/renderer.py
test_prompts_are_numbered_per_console | rewrite | 1 | same _Renderer spy | tests/conftest.py;tests/test_console.py;source/sushicore/console.py;source/sushicore/renderer.py
test_result_sends_an_empty_payload_by_default | rewrite | 1 | same _Renderer spy | tests/conftest.py;tests/test_console.py;source/sushicore/console.py;source/sushicore/renderer.py
test_properties_expose_the_bound_parts | rewrite | 1 | same _Renderer spy; reads renderer.raw | tests/conftest.py;tests/test_console.py;source/sushicore/console.py;source/sushicore/renderer.py
```

### `tests/test_deps_fragment/test_base_fragment.py`

```
test_base_fragment_is_a_readable_file | rewrite | 1 | small test reads a repository file through manifests.base_fragment(); rewrite at medium, same promise: the base declares the base tools | tests/test_deps_fragment/test_base_fragment.py; source/sushicore/provision/fragments.py
test_base_fragment_declares_no_module_dependency | rewrite | 1 | small test reads a repository file; rewrite at medium, same promise: the base declares no depends_on | (same files)
test_base_owner_is_the_shared_owner | delete | 1 | test of a constant: BASE_OWNER equals SHARED_OWNER, a copy of a name, with no behaviour behind it | tests/test_deps_fragment/test_base_fragment.py; source/sushicore/provision/fragments.py
```

### `tests/test_deps_fragment/test_deps_fragment.py`

```
test_one_table_per_dependency_is_the_shape | keep | 9 | read: each top-level table is one dependency keyed by its name | tests/test_deps_fragment/test_deps_fragment.py; source/sushicore/deps_fragment.py
test_the_module_table_is_metadata_rather_than_a_dependency | keep | 9 | read: [module] is metadata and never a dependency | (same files)
test_an_array_of_tables_is_refused_rather_than_skipped | keep | 9 | read: refuses an array of tables and names the file | (same files)
test_a_scalar_at_the_top_level_is_refused_too | keep | 9 | read: refuses a non-table top-level key | (same files)
test_the_platform_decides_which_column_is_read | resize | 8 | Dependency.packages_for: the vcpkg column on Windows, the apt column elsewhere; pure on values, so small | (same files)
test_a_dependency_with_no_package_here_is_not_applicable | resize | 8 | status: NOT_APPLICABLE for an entry naming no package here, and install_command is None; pure, so small | (same files)
test_a_package_nobody_can_check_is_unknown | resize | 8 | status: UNKNOWN for a package with no check command; pure, so small | (same files)
test_a_check_command_that_passes_settles_it | keep | 9 | status: SATISFIED when the check command exits 0 | (same files)
test_a_check_command_that_fails_leaves_it_unknown | keep | 9 | status: UNKNOWN when the check command exits non-zero | (same files)
test_a_check_command_that_cannot_run_leaves_it_unknown | keep | 9 | status: UNKNOWN when the check command cannot run | (same files)
test_the_install_command_names_apt_off_windows | resize | 8 | install_command: apt-get install -y off Windows; pure, so small | (same files)
test_the_install_command_names_vcpkg_on_windows | resize | 8 | install_command: vcpkg with the caller's executable and triplet on Windows; pure, so small | (same files)
test_the_triplet_is_left_off_when_the_caller_pins_none | resize | 8 | install_command: the triplet is left off when the caller pins none; pure, so small | (same files)
test_an_entry_without_sha256_pins_nothing | keep | 9 | read: an entry without sha256 pins nothing | (same files)
test_sha256_pins_one_digest_per_platform | keep | 9 | read: sha256 pins one lower-case digest per platform | (same files)
test_a_platform_the_table_leaves_out_has_no_digest | keep | 9 | read: a platform the sha256 table leaves out has no digest | (same files)
test_a_sha256_that_cannot_pin_a_file_is_refused | keep | 9 | read: a sha256 that cannot pin a file is refused, naming the entry | (same files)
test_a_sushi_pin_is_read_with_its_tag_and_commit | keep | 9 | read: a [sushisystems.<name>] pin reads its tag and its commit in lower case | (same files)
test_the_deprecated_sushi_table_reads_with_a_warning | keep | 9 | read: [sushi.<name>] reads the same pins and warns with DeprecationWarning | (same files)
test_pins_under_both_table_names_are_refused | keep | 9 | read: pins under both table names are refused | (same files)
test_a_module_in_depends_on_may_go_unpinned | keep | 9 | read: a module in depends_on may go unpinned | (same files)
test_a_pin_not_in_depends_on_is_refused | keep | 9 | read: a pin naming a module depends_on does not list is refused | (same files)
test_a_malformed_pin_is_refused | keep | 9 | read: a malformed pin (no version, or a short commit) is refused naming the fault | (same files)
test_an_absent_fragment_reads_as_none_with_no_pins | keep | 9 | read_present and pins_at: an absent fragment reads as None with no pins | (same files)
test_the_module_table_names_the_cli_and_the_package_exclusions | keep | 9 | read: [module] cli and package_exclude are read | (same files)
test_a_module_table_without_the_keys_reads_them_empty | rewrite | 1 | default values: asserts the empty defaults of cli and package_exclude, a default-value test; rewrite merged into the rows of the cli-and-exclusions test | (same files)
test_a_malformed_cli_or_exclusion_is_refused | keep | 9 | read: a malformed cli or package_exclude is refused | (same files)
```

### `tests/test_describe.py`

```
test_describe_prints_the_catalogue_without_hidden_commands | split | 3 | (a) the catalogue document (program, contract, help, flags); (b) hidden spellings are left out; one invoke, two promises | tests/conftest.py;tests/test_describe.py;source/sushicore/describe.py;source/sushicore/root_options.py
test_catalogue_carries_applies_to | keep | 9 | applies_to is repeated on every command; medium because installed_version reads package metadata | tests/conftest.py;tests/test_describe.py;source/sushicore/describe.py
test_catalogue_lists_a_group_that_runs_bare_beside_its_children | keep | 9 | a bare-running group is listed beside its children | tests/conftest.py;tests/test_describe.py;source/sushicore/describe.py
```

### `tests/test_diag.py`

```
test_env_without_a_build_environment_fails_with_one_line | rewrite | 1 | stand-in _Console (console port) and _Config (ConfigModule protocol); in-memory adapters needed, the ConfigModule one does not exist | tests/conftest.py;tests/test_diag.py;source/sushicore/diag.py;source/sushicore/profile.py
test_env_shows_only_build_relevant_variables_unless_asked | rewrite | 1 | stand-ins _Console and _Config, and a recording build_env closure | tests/conftest.py;tests/test_diag.py;source/sushicore/diag.py;source/sushicore/profile.py
test_a_value_set_in_the_local_file_names_the_local_file | rewrite | 1 | _LayeredConfig stand-in for ConfigModule; writes files in small; reads the private rich name Table columns _cells | tests/conftest.py;tests/test_diag.py;source/sushicore/diag.py;source/sushicore/profile.py;source/sushicore/workspace.py
test_a_value_from_the_linked_workspace_names_the_workspace | rewrite | 1 | _LayeredConfig stand-in; writes files in small; private _cells | tests/conftest.py;tests/test_diag.py;source/sushicore/diag.py;source/sushicore/profile.py;source/sushicore/workspace.py
test_a_value_set_nowhere_is_the_default | rewrite | 1 | _LayeredConfig stand-in; writes files in small; private _cells; the default branch | tests/conftest.py;tests/test_diag.py;source/sushicore/diag.py;source/sushicore/profile.py;source/sushicore/workspace.py
```

### `tests/test_diag_commands.py`

```
test_diagnostic_commands_delegate_and_return_the_code | rewrite | 1 | stand-in _Diagnostics spy for the DiagnosticsLike protocol; in-memory adapter: Diagnostics over an in-memory config module and console, not built | tests/conftest.py;tests/test_diag_commands.py;source/sushicore/diag_commands.py;source/sushicore/diag.py
test_diagnostic_commands_can_leave_env_to_the_cli | rewrite | 1 | the same _Diagnostics stand-in, passed and unused; the file also holds an unused K_REMOVED constant | tests/conftest.py;tests/test_diag_commands.py;source/sushicore/diag_commands.py;source/sushicore/diag.py
```

### `tests/test_discovery.py`

```
test_resolve_finds_an_explicit_target | rewrite | 1 | _FakeConsole stand-in for the ConsoleLike protocol and a SimpleNamespace stand-in for console.console; in-memory console adapter needed | tests/conftest.py;tests/test_discovery.py;source/sushicore/discovery.py;source/sushicore/console.py;source/sushicore/renderer.py
test_resolve_reports_a_missing_explicit_target_by_name | rewrite | 1 | the same _FakeConsole stand-in | tests/conftest.py;tests/test_discovery.py;source/sushicore/discovery.py;source/sushicore/console.py;source/sushicore/renderer.py
test_resolve_falls_back_to_the_default_when_no_target_is_given | rewrite | 1 | the same _FakeConsole stand-in | tests/conftest.py;tests/test_discovery.py;source/sushicore/discovery.py;source/sushicore/console.py;source/sushicore/renderer.py
test_resolve_reports_a_missing_default_by_name | rewrite | 1 | the same _FakeConsole stand-in | tests/conftest.py;tests/test_discovery.py;source/sushicore/discovery.py;source/sushicore/console.py;source/sushicore/renderer.py
test_resolve_with_sort_ignores_target_and_default_and_delegates_to_select | rewrite | 1 | the same _FakeConsole stand-in; the empty-tree message is the proof of the branch | tests/conftest.py;tests/test_discovery.py;source/sushicore/discovery.py;source/sushicore/console.py;source/sushicore/renderer.py
test_resolve_with_sort_returns_select_choice_even_though_target_also_matches | rewrite | 1 | the same _FakeConsole stand-in; IntPrompt.ask is replaced at the prompt boundary, allowed | tests/conftest.py;tests/test_discovery.py;source/sushicore/discovery.py;source/sushicore/console.py;source/sushicore/renderer.py
```

### `tests/test_entry.py`

```
test_run_turns_a_sushicore_error_into_one_line_and_exit_one | rewrite | 1 | a recorder list (reported.append) for the report sink that run takes; in-memory adapter: Console over PlainRenderer(io.StringIO) | tests/conftest.py;tests/test_entry.py;source/sushicore/entry.py;source/sushicore/errors.py;source/sushicore/console.py;source/sushicore/renderer.py
test_run_falls_back_to_stderr_when_the_reporter_itself_fails | rewrite | 1 | a stand-in reporter that raises, written by the test; use a real LazyConsole over a broken config file | tests/conftest.py;tests/test_entry.py;source/sushicore/entry.py;source/sushicore/errors.py;source/sushicore/cli_console.py
test_run_passes_a_normal_exit_and_other_errors_through | rewrite | 1 | a stand-in reporter lambda for the sink; the final issubclass line checks a class relation; split | tests/conftest.py;tests/test_entry.py;source/sushicore/entry.py;source/sushicore/errors.py
```

### `tests/test_errors.py`

```
test_a_config_error_is_a_sushicore_error_and_a_value_error | keep | 9 | ConfigError is what entry catches and what ValueError callers catch | tests/conftest.py;tests/test_errors.py;source/sushicore/errors.py
test_a_digest_mismatch_names_the_file_and_both_digests | keep | 9 | the attributes and message name the file and both digests | tests/conftest.py;tests/test_errors.py;source/sushicore/errors.py
```

### `tests/test_events.py`

```
test_every_kind_is_named | delete | 1 | pins the kind set to a copied literal; the renderer output is checked in tests/test_renderer/test_json_renderer.py and the refusal in test_unknown_kind_is_refused | tests/conftest.py;tests/test_events.py;source/sushicore/events.py;tests/test_renderer/test_json_renderer.py
test_event_line_is_one_json_object_with_the_kind_first | keep | 9 | one JSON object, kind first; one serialisation promise | tests/conftest.py;tests/test_events.py;source/sushicore/events.py
test_event_line_keeps_non_ascii_and_embedded_newlines_escaped | split | 3 | "and" joins two results that can break apart: non-ASCII kept, newlines escaped | tests/conftest.py;tests/test_events.py;source/sushicore/events.py
test_unknown_kind_is_refused | keep | 9 | an unknown kind raises ValueError | tests/conftest.py;tests/test_events.py;source/sushicore/events.py
```

### `tests/test_icons.py`

```
test_merged_takes_known_non_empty_overrides_only | keep | 9 | icons: merged keeps only the known, non-empty overrides | tests/test_icons.py; source/sushicore/icons.py
test_get_icon_set_returns_a_preset | keep | 9 | icons: get_icon_set returns the named preset | tests/test_icons.py; source/sushicore/icons.py
test_get_icon_set_names_the_known_sets_for_an_unknown_one | keep | 9 | icons: an unknown set name raises ConfigError listing the known sets | tests/test_icons.py; source/sushicore/icons.py
test_a_registered_set_is_found_and_listed | split | 3 | icons: a registered set is found by name; icons: known_icon_sets lists the names sorted; the body also writes the process-wide _ICON_PRESETS, so the registry needs a seam (question 8) | tests/test_icons.py; source/sushicore/icons.py
```

### `tests/test_markup.py`

```
test_a_bracket_that_names_no_style_is_escaped | keep | 9 | markup: a bracket that names no style is escaped | tests/test_markup.py; source/sushicore/markup.py
test_a_cell_with_a_feature_list_survives_a_round_trip_through_markup | keep | 9 | markup: an escaped string shows its brackets as text through Rich | tests/test_markup.py; source/sushicore/markup.py
test_a_bracket_that_names_a_rich_style_is_left_alone | keep | 9 | markup: a bracket naming a Rich style is left alone (parametrised, three rows) | tests/test_markup.py; source/sushicore/markup.py
test_a_theme_name_is_left_alone_when_it_is_known | merge | 4 | markup: a theme name is left alone when known and escaped when not; merge with tests/test_markup.py::test_a_theme_name_is_escaped_when_it_is_not_known_and_not_a_rich_style | tests/test_markup.py
test_a_theme_name_is_escaped_when_it_is_not_known_and_not_a_rich_style | merge | 4 | markup: a theme name is left alone when known and escaped when not; merge with tests/test_markup.py::test_a_theme_name_is_left_alone_when_it_is_known | tests/test_markup.py
test_the_bare_close_everything_tag_is_left_alone | keep | 9 | markup: a bare close tag is left alone | tests/test_markup.py; source/sushicore/markup.py
test_a_bracket_that_is_already_escaped_is_left_alone | merge | 4 | markup: a bracket after an odd run of backslashes is already escaped; merge with tests/test_markup.py::test_a_bracket_after_an_odd_run_of_backslashes_is_escaped_already | tests/test_markup.py
test_several_brackets_in_one_string_are_judged_one_by_one | keep | 9 | markup: several brackets in one string are judged one by one | tests/test_markup.py; source/sushicore/markup.py
test_a_string_without_brackets_is_returned_unchanged | keep | 9 | markup: a string without brackets comes back unchanged | tests/test_markup.py; source/sushicore/markup.py
test_a_link_stays_a_link | keep | 9 | markup: a link tag stays a link | tests/test_markup.py; source/sushicore/markup.py
test_a_link_written_with_a_space_stays_a_link_when_closed_with_a_bare_slash | keep | 9 | markup: a link with a space, closed by a bare slash, stays a link | tests/test_markup.py; source/sushicore/markup.py
test_a_closing_tag_that_closes_nothing_and_names_no_style_is_escaped | keep | 9 | markup: a closing tag that closes nothing and names no style is escaped | tests/test_markup.py; source/sushicore/markup.py
test_a_closing_tag_is_matched_against_the_opening_tag_it_follows | keep | 9 | markup: a closing tag closes the open tag it follows | tests/test_markup.py; source/sushicore/markup.py
test_a_numeric_or_oddly_spelled_name_is_not_a_style | keep | 9 | markup: a numeric or oddly spelled name is not a style (parametrised, three rows) | tests/test_markup.py; source/sushicore/markup.py
test_an_empty_name_is_left_alone | keep | 9 | markup: an empty bracket is left alone (parametrised, two rows) | tests/test_markup.py; source/sushicore/markup.py
test_a_bracket_after_an_even_run_of_backslashes_is_not_escaped | keep | 9 | markup: a bracket after an even run of backslashes gets one more backslash; the name says "not escaped" while the body shows one added, so the name needs a fix | tests/test_markup.py; source/sushicore/markup.py
test_a_bracket_after_an_odd_run_of_backslashes_is_escaped_already | merge | 4 | markup: a bracket after an odd run of backslashes is already escaped; merge with tests/test_markup.py::test_a_bracket_that_is_already_escaped_is_left_alone | tests/test_markup.py
test_a_key_value_bracket_is_not_a_style | keep | 9 | markup: a key=value bracket is not a style | tests/test_markup.py; source/sushicore/markup.py
test_a_styled_cell_keeps_its_style_and_loses_only_its_tags | keep | 9 | markup: a styled cell keeps its style and loses only its tags | tests/test_markup.py; source/sushicore/markup.py
```

### `tests/test_module_config.py`

```
test_a_release_manifest_alone_marks_a_binary_root | keep | 9 | module_config: a release manifest alone marks a binary root | tests/test_module_config.py; source/sushicore/module_config.py; source/sushicore/profile.py
test_a_root_marker_alone_marks_a_source_root | keep | 9 | module_config: a root marker alone marks a source root | tests/test_module_config.py; source/sushicore/module_config.py; source/sushicore/profile.py
test_presence_falls_back_to_the_discovered_root | keep | 9 | module_config: presence with no root walks up to the discovered root | tests/test_module_config.py; source/sushicore/module_config.py
test_a_tree_with_neither_marker_names_both_markers | keep | 9 | module_config: outside a checkout find_project_root exits with a message naming both markers; the message half repeats tests/test_profile.py::test_not_a_project_message_names_both_markers, the exit is this unit's | tests/test_module_config.py; tests/test_profile.py; source/sushicore/module_config.py; source/sushicore/profile.py
test_the_shared_config_is_the_workspace_file | rewrite | 5 | module_config: the shared config is the workspace file, else the legacy file, else none; the test reads the private _shared_config_local, so a rename breaks it; rewrite against the public sources() | tests/test_module_config.py; source/sushicore/module_config.py; source/sushicore/workspace.py
test_an_unupgraded_workspace_falls_back_to_the_old_file | rewrite | 5 | module_config: the shared config is the workspace file, else the legacy file, else none; reads the private _shared_config_local; rewrite against sources() | tests/test_module_config.py; source/sushicore/module_config.py; source/sushicore/workspace.py
test_the_new_file_wins_when_both_exist | rewrite | 5 | module_config: the shared config is the workspace file, else the legacy file, else none; reads the private _shared_config_local; rewrite against sources() | tests/test_module_config.py; source/sushicore/module_config.py; source/sushicore/workspace.py
test_a_workspace_with_neither_file_shares_nothing | rewrite | 5 | module_config: the shared config is the workspace file, else the legacy file, else none; reads the private _shared_config_local; rewrite against sources() | tests/test_module_config.py; source/sushicore/module_config.py; source/sushicore/workspace.py
test_workspace_home_follows_the_link_pointer | keep | 9 | module_config: workspace_home follows the link pointer | tests/test_module_config.py; source/sushicore/module_config.py; source/sushicore/workspace.py
test_a_stale_link_pointer_falls_back_to_the_walk_up | keep | 9 | module_config: a stale link pointer falls back to the walk-up | tests/test_module_config.py; source/sushicore/module_config.py; source/sushicore/workspace.py
test_environment_beats_the_link_pointer | keep | 9 | module_config: SUSHISTACK_HOME beats the link pointer | tests/test_module_config.py; source/sushicore/module_config.py; source/sushicore/workspace.py
```

### `tests/test_plain_text.py`

```
test_tags_are_removed_and_their_text_kept | keep | 9 | plain_text: markup tags are removed and their text kept | tests/test_plain_text.py; source/sushicore/plain_text.py
test_a_bracket_that_is_no_tag_is_kept | keep | 9 | plain_text: a bracket that is no tag is kept | tests/test_plain_text.py; source/sushicore/plain_text.py
test_text_with_a_mismatched_closing_tag_comes_back_as_it_was | keep | 9 | plain_text: a mismatched closing tag leaves the text as it was | tests/test_plain_text.py; source/sushicore/plain_text.py
test_plain_text_is_unchanged | keep | 9 | plain_text: text without markup comes back unchanged | tests/test_plain_text.py; source/sushicore/plain_text.py
test_importing_the_module_does_not_load_rich | keep | 9 | plain_text: importing the module does not load Rich; medium because it starts a child process, and PYTHONPATH "source" depends on the working directory | tests/test_plain_text.py; source/sushicore/plain_text.py
```

### `tests/test_proc.py`

```
test_resolve_exe_falls_back_to_the_name | rewrite | 1 | proc: resolve_exe returns the bare name when nothing is found; stand-in _Recorder for the ConsoleLike the Runner takes; the rewrite needs an in-memory ConsoleLike adapter in source/sushicore/proc.py, which does not exist | tests/test_proc.py; source/sushicore/proc.py
test_resolve_exe_reads_path_case_insensitively | rewrite | 1 | proc: resolve_exe reads PATH case-insensitively; stand-in _Recorder; the rewrite needs the in-memory ConsoleLike adapter in source/sushicore/proc.py, which does not exist | tests/test_proc.py; source/sushicore/proc.py
test_resolve_exe_finds_the_tool_when_the_env_holds_both_path_keys | rewrite | 1 | proc: resolve_exe finds a tool through every PATH-spelled key; stand-in _Recorder; the rewrite needs the in-memory ConsoleLike adapter in source/sushicore/proc.py, which does not exist | tests/test_proc.py; source/sushicore/proc.py
test_not_found_message_names_the_program | rewrite | 1 | proc: a missing executable names the program in its guidance and returns the configured code; stand-in _Recorder; the rewrite needs the in-memory ConsoleLike adapter in source/sushicore/proc.py, which does not exist | tests/test_proc.py; source/sushicore/proc.py
test_drained_output_is_not_parsed_as_markup | rewrite | 1 | proc: run_drained prints child output without markup parsing; stand-in _Recorder; the Popen stand-in is stdlib and allowed; the rewrite needs the in-memory ConsoleLike adapter in source/sushicore/proc.py, which does not exist | tests/test_proc.py; source/sushicore/proc.py
test_missing_exit_code_defaults_to_one_and_is_configurable | rewrite | 1 | proc: missing_exit_code defaults to 1 and is configurable; stand-in _Recorder; the rewrite needs the in-memory ConsoleLike adapter in source/sushicore/proc.py, which does not exist | tests/test_proc.py; source/sushicore/proc.py
test_run_drained_returns_the_missing_exit_code | rewrite | 1 | proc: a missing executable names the program in its guidance and returns the configured code (run_drained); stand-in _Recorder; the rewrite needs the in-memory ConsoleLike adapter in source/sushicore/proc.py, which does not exist | tests/test_proc.py; source/sushicore/proc.py
test_interrupt_propagates_by_default | rewrite | 1 | proc: run and run_drained propagate interrupt by default; stand-in _Recorder; the rewrite needs the in-memory ConsoleLike adapter in source/sushicore/proc.py, which does not exist | tests/test_proc.py; source/sushicore/proc.py
test_run_catches_interrupt_when_asked | rewrite | 1 | proc: run and run_drained return 130 and warn when asked to catch interrupt; stand-in _WarnRecorder; the rewrite needs the in-memory ConsoleLike adapter in source/sushicore/proc.py, which does not exist | tests/test_proc.py; source/sushicore/proc.py
test_run_drained_terminates_the_child_on_interrupt | rewrite | 1 | proc: run and run_drained return 130 and warn when asked to catch interrupt; stand-in _WarnRecorder; the rewrite needs the in-memory ConsoleLike adapter in source/sushicore/proc.py, which does not exist | tests/test_proc.py; source/sushicore/proc.py
test_run_drained_replaces_undecodable_bytes | rewrite | 1 | proc: run_drained replaces undecodable bytes; stand-in _Recorder; the test reads a Popen keyword, a change detector, so the rewrite feeds an undecodable child and reads its output; the in-memory ConsoleLike adapter in source/sushicore/proc.py does not exist | tests/test_proc.py; source/sushicore/proc.py
test_capture_returns_code_stdout_and_stderr_without_echo | rewrite | 1 | proc: capture returns code, stdout and stderr without echo; stand-in _Recorder; the rewrite needs the in-memory ConsoleLike adapter in source/sushicore/proc.py, which does not exist | tests/test_proc.py; source/sushicore/proc.py
test_capture_reports_a_missing_executable_quietly | rewrite | 1 | proc: capture reports a missing executable quietly; stand-in _Recorder; the rewrite needs the in-memory ConsoleLike adapter in source/sushicore/proc.py, which does not exist | tests/test_proc.py; source/sushicore/proc.py
test_capture_catches_interrupt | rewrite | 1 | proc: capture catches interrupt when asked; stand-in _WarnRecorder; the rewrite needs the in-memory ConsoleLike adapter in source/sushicore/proc.py, which does not exist | tests/test_proc.py; source/sushicore/proc.py
test_capture_returns_the_default_missing_exit_code | rewrite | 1 | proc: missing_exit_code defaults to 1 and is configurable (capture); stand-in _Recorder; the rewrite needs the in-memory ConsoleLike adapter in source/sushicore/proc.py, which does not exist | tests/test_proc.py; source/sushicore/proc.py
test_capture_propagates_interrupt_by_default | rewrite | 1 | proc: capture propagates interrupt by default; stand-in _Recorder; the rewrite needs the in-memory ConsoleLike adapter in source/sushicore/proc.py, which does not exist | tests/test_proc.py; source/sushicore/proc.py
```

### `tests/test_profile.py`

```
test_env_overrides_are_prefixed_from_the_profile | resize | 8 | profile: env overrides are prefixed from the profile; a pure value, so small; the file-level medium label is larger than the test needs | tests/test_profile.py; source/sushicore/profile.py
test_extra_env_overrides_win_over_the_prefix | resize | 8 | profile: an extra override wins over the prefix; pure value, so small | tests/test_profile.py; source/sushicore/profile.py
test_an_extra_override_for_a_non_tool_field_is_still_carried | resize | 8 | profile: an extra override for a non-tool field is carried; pure value, so small | tests/test_profile.py; source/sushicore/profile.py
test_sibling_skip_dirs_names_every_sibling | resize | 8 | profile: sibling_skip_dirs names every sibling; pure value, so small | tests/test_profile.py; source/sushicore/profile.py
test_markers_name_the_root_marker_then_the_release_manifest | resize | 8 | profile: markers are the root marker then the release manifest; pure value, so small | tests/test_profile.py; source/sushicore/profile.py
test_presence_is_binary_when_the_release_manifest_is_there | keep | 9 | profile: presence is binary when the manifest is a file | tests/test_profile.py; source/sushicore/profile.py
test_presence_is_source_without_the_release_manifest | keep | 9 | profile: presence is source without the manifest | tests/test_profile.py; source/sushicore/profile.py
test_a_directory_named_like_the_manifest_is_not_a_binary_install | keep | 9 | profile: a directory named like the manifest is not a binary install | tests/test_profile.py; source/sushicore/profile.py
test_not_a_project_message_names_both_markers | resize | 8 | profile: not_a_project_message names both markers; pure string, so small | tests/test_profile.py; source/sushicore/profile.py
test_key_is_the_lower_cased_name | delete | 1 | a property that returns name.lower(); trivial code with no promise of its own (forbidden kind: getter) | tests/test_profile.py; source/sushicore/profile.py
```

### `tests/test_renderer/test_console_semantics.py`

```
test_plain_table_prints_title_header_and_rows | keep | 9 | PlainRenderer.table: prints title, header and rows | tests/test_renderer/test_console_semantics.py; source/sushicore/renderer.py
test_plain_progress_prints_index_of_count | keep | 9 | PlainRenderer.progress: prints the label and index of count | (same files)
test_plain_result_prints_nothing | keep | 9 | PlainRenderer.result: prints nothing | (same files)
test_plain_prompt_returns_default_on_empty_line | rewrite | 1 | small test replaces builtins.input (stdin, a device); PlainRenderer.prompt has no input-stream seam, unlike JsonRenderer; rewrite with an input stream argument | tests/test_renderer/test_console_semantics.py; source/sushicore/renderer.py
test_plain_prompt_returns_default_on_eof | rewrite | 1 | small test replaces builtins.input (stdin); same seam as above | (same files)
test_rich_table_renders_rows | rewrite | 1 | small test captures stdout with capsys (a device); RichRenderer writes to sys.stdout; carries: the table draws its rows; rewrite with an injected stream, medium if the Rich output is kept | (same files)
test_console_table_passes_the_theme_header_style | rewrite | 1 | _Spy implements the Renderer protocol (repository interface) as a recorder; rewrite with JsonRenderer over io.StringIO, the in-memory adapter in source/sushicore/renderer.py | (same files)
test_console_leaves_group_by_out_of_the_call_when_it_is_not_asked_for | rewrite | 1 | _GroupingSpy recorder for the Renderer protocol; rewrite on JsonRenderer over io.StringIO | (same files)
test_console_forwards_the_grouping_column_when_it_is_given | rewrite | 1 | _GroupingSpy recorder; rewrite on JsonRenderer over io.StringIO | (same files)
test_a_renderer_that_never_heard_of_group_by_still_draws_an_ungrouped_table | rewrite | 1 | _Spy recorder for the Renderer protocol; rewrite on JsonRenderer over io.StringIO | (same files)
test_console_progress_defaults_fraction_to_none | rewrite | 1 | _Spy recorder; the default is a public promise, so rewrite on JsonRenderer and check the fraction key of the event | (same files)
test_console_result_defaults_payload_to_empty_dict | rewrite | 1 | _Spy recorder; rewrite on JsonRenderer and check the payload key | (same files)
test_console_prompt_numbers_prompts_per_instance | rewrite | 1 | _Spy recorder; rewrite on JsonRenderer over StringIO with input from io.StringIO | (same files)
test_console_is_machine_is_false_for_a_rich_renderer | merge | 4 | merge with test_console_is_machine_is_true_for_a_json_renderer into rows over the renderer: Console.is_machine is False for Rich and True for JSON | (same files)
test_console_is_machine_is_true_for_a_json_renderer | merge | 4 | merge with test_console_is_machine_is_false_for_a_rich_renderer into the same rows | (same files)
```

### `tests/test_renderer/test_json_renderer.py`

```
test_line_event_carries_level_and_message | keep | 9 | JsonRenderer.line: emits one line event with level and message | tests/test_renderer/test_json_renderer.py; source/sushicore/renderer.py; source/sushicore/events.py (not read)
test_level_is_derived_from_the_prefix_not_the_style | merge | 4 | merge with test_unnamed_prefix_yields_info into rows: the level comes from the prefix, info when none | (same files)
test_unnamed_prefix_yields_info | merge | 4 | merge with test_level_is_derived_from_the_prefix_not_the_style into the same rows | (same files)
test_each_call_is_exactly_one_line | keep | 9 | JsonRenderer: each call emits exactly one line | (same files)
test_events_carry_the_contract_keys | keep | 9 | JsonRenderer: events carry the contract keys | (same files)
test_the_table_event_is_byte_identical_with_and_without_a_grouping_column | keep | 9 | JsonRenderer.table: the event is byte-identical with and without a grouping column | (same files)
test_raw_writes_to_the_error_stream_not_stdout | keep | 9 | JsonRenderer.raw: writes to the error stream, never to stdout | (same files)
test_prompt_emits_the_event_and_reads_one_line | keep | 9 | JsonRenderer.prompt: emits a prompt event and reads one line | (same files)
test_prompt_returns_default_on_eof | keep | 9 | JsonRenderer.prompt: returns the default on EOF | (same files)
test_default_streams_are_forced_to_utf8 | rewrite | 1 | small test replaces sys.stdout (process-wide, a device); rewrite with the stream passed to a stream-encoding seam in renderer.py | (same files)
test_a_stream_that_refuses_utf8_is_recorded | rewrite | 1 | small test replaces sys.stdout and sys.stderr and captures the sushicore.renderer logger (process-wide); rewrite with the streams and an in-memory log sink passed in | (same files)
test_the_table_event_carries_plain_text_with_no_markup | merge | 4 | merge with test_a_cell_with_a_bracket_that_is_no_markup_keeps_it into rows: the table event carries plain text, and keeps brackets that are not markup | (same files)
test_a_cell_with_a_bracket_that_is_no_markup_keeps_it | merge | 4 | merge with test_the_table_event_carries_plain_text_with_no_markup into the same rows | (same files)
```

### `tests/test_renderer/test_rich_components.py`

```
test_table_has_a_title_a_header_a_rule_and_no_frame | keep | 9 | RichRenderer.table: draws a title, a header, a rule and no frame | tests/test_renderer/test_rich_components.py; tests/conftest.py; source/sushicore/renderer.py
test_grouped_table_prints_a_heading_per_group_without_the_group_column | keep | 9 | RichRenderer.table: a grouped table prints a heading per group without the group column | (same files)
test_header_prints_a_blank_line_then_a_rule_holding_the_title | keep | 9 | RichRenderer.header: prints a blank line, then a rule holding the title | (same files)
test_panel_prints_its_title_and_body_inside_a_border | keep | 9 | RichRenderer.panel: prints the title and body inside a border | (same files)
test_importing_sushicore_does_not_load_rich | merge | 4 | merge with test_importing_sushicore_does_not_load_the_windows_console_module into rows over the module name: import sushicore does not load it | (same files)
test_importing_sushicore_does_not_load_the_windows_console_module | merge | 4 | merge with test_importing_sushicore_does_not_load_rich into the same rows | (same files)
test_constructing_a_rich_renderer_switches_on_virtual_terminal_processing_once | rewrite | 1 | stub of the repository function sushicore.windows_console.enable_virtual_terminal made by the test (the file's autouse fixture stubs it too); rewrite with the switch passed into RichRenderer | (same files)
test_header_title_keeps_parsing_markup | merge | 4 | merge with test_panel_title_keeps_parsing_markup into rows over the component: markup in a title is parsed, not printed | (same files)
test_panel_title_keeps_parsing_markup | merge | 4 | merge with test_header_title_keeps_parsing_markup into the same rows | (same files)
test_the_delegating_methods_state_what_they_print_in_one_sentence | delete | 2 | would not fail if the behaviour broke: it checks the docstring of three methods for a sentence count, a documentation rule for a checker, not a promise of the unit | tests/test_renderer/test_rich_components.py; source/sushicore/renderer.py
```

### `tests/test_root_options.py`

```
test_version_prints_the_distribution_and_exits_zero | rewrite | 6 | root_options: --version prints one line naming the distribution and exits 0; the expected output is version_line, the code under test; rewrite with importlib.metadata as the oracle | tests/test_root_options.py; source/sushicore/root_options.py; source/sushicore/describe.py
test_version_of_an_unknown_distribution_reads_unknown | keep | 9 | root_options: version_line reads unknown for a missing distribution | tests/test_root_options.py; source/sushicore/root_options.py
test_version_lines_can_be_supplied_by_the_cli | keep | 9 | root_options: version lines supplied by the CLI are printed | tests/test_root_options.py; source/sushicore/root_options.py
test_root_options_keep_the_help_and_the_commands | split | 3 | root_options: registering keeps the help text; root_options: registering keeps command behaviour | tests/test_root_options.py; source/sushicore/root_options.py
```

### `tests/test_stack_config.py`

```
test_a_stack_config_carries_the_provision_fields | rewrite | 5 | stack_config: a config reads a provision field through the StackConfig; the body is a class-shape check that breaks on composition while behaviour holds; rewrite as a read of use_vcpkg or cxx through a _Config | tests/test_stack_config.py; source/sushicore/stack_config.py; source/sushicore/provision/config.py
test_bundled_clang_is_found_under_the_provision_root | keep | 9 | stack_config: bundled clang is found under the provision root | tests/test_stack_config.py; tests/conftest.py; source/sushicore/stack_config.py
test_a_workspace_tree_wins_over_the_provision_root | keep | 9 | stack_config: a workspace tree wins over the provision root | tests/test_stack_config.py; tests/conftest.py; source/sushicore/stack_config.py
test_the_environment_override_is_the_only_root | keep | 9 | stack_config: SUSHISTACK_DEPS_DIR is the only root when set | tests/test_stack_config.py; tests/conftest.py; source/sushicore/stack_config.py
test_resolved_vcpkg_finds_the_provision_root_tree | keep | 9 | stack_config: resolved vcpkg finds the provision root tree | tests/test_stack_config.py; tests/conftest.py; source/sushicore/stack_config.py
test_locate_sibling_returns_the_directory_beside_the_root | keep | 9 | stack_config: locate_sibling returns the directory beside the root | tests/test_stack_config.py; source/sushicore/stack_config.py
test_locate_sibling_prefers_the_configured_directory | keep | 9 | stack_config: locate_sibling prefers the configured directory | tests/test_stack_config.py; source/sushicore/stack_config.py
test_locate_sibling_is_none_without_a_checkout | keep | 9 | stack_config: locate_sibling is None without a checkout; it reads the process environment and does not clear SUSHIRUNTIME_DIR, unlike test_locate_sibling_finds_the_fetched_copy_of_a_pinned_library | tests/test_stack_config.py; source/sushicore/stack_config.py
test_a_linked_workspace_tree_is_searched | keep | 9 | stack_config: a linked workspace tree is searched | tests/test_stack_config.py; source/sushicore/stack_config.py; source/sushicore/workspace.py
test_a_pinned_llvm_root_wins_when_its_compiler_exists | keep | 9 | stack_config: a pinned llvm root wins when its clang++ exists | tests/test_stack_config.py; source/sushicore/stack_config.py
test_locate_sibling_finds_the_fetched_copy_of_a_pinned_library | keep | 9 | stack_config: a pinned library with no sibling resolves to the fetched copy | tests/test_stack_config.py; source/sushicore/stack_config.py
test_sushi_definitions_hand_cmake_each_resolved_directory | keep | 9 | stack_config: sushi_definitions gives -D<NAME>_DIR for each pinned library that resolves | tests/test_stack_config.py; source/sushicore/stack_config.py
test_sushi_pins_read_the_fragment_the_module_declares | keep | 9 | stack_config: sushi_pins reads the fragment a subclass declares | tests/test_stack_config.py; source/sushicore/stack_config.py
test_sushi_definitions_skip_a_packaged_library | rewrite | 1 | stack_config: a packaged library gets no -D<NAME>_DIR; stand-in _Packaged for the repository-owned PackageSet; rewrite with the real PackageSet value, which needs no adapter | tests/test_stack_config.py; source/sushicore/stack_config.py; source/sushicore/provision/sushi_packages/package_set.py
test_sushi_definitions_skip_a_library_the_package_set_left_out | rewrite | 1 | stack_config: a library the package set left out gets no -D<NAME>_DIR; stand-in _Filtered for the repository-owned PackageSet; rewrite with the real PackageSet value, which needs no adapter | tests/test_stack_config.py; source/sushicore/stack_config.py; source/sushicore/provision/sushi_packages/package_set.py
test_sushi_packages_hands_the_resolver_the_consumer_request | rewrite | 1 | stack_config: sushi_packages gives the resolver the consumer request; monkeypatches the repository function stack_config.default_resolver and uses a stand-in _Resolver; rewrite by injecting the resolver into sushi_packages | tests/test_stack_config.py; source/sushicore/stack_config.py; source/sushicore/provision/sushi_packages/
test_a_config_that_turns_vcpkg_off_resolves_none_even_with_a_tree_present | merge | 4 | stack_config: use_vcpkg False resolves no vcpkg, whatever is present; merge with tests/test_stack_config.py::test_a_config_that_turns_vcpkg_off_ignores_an_explicit_root_too | tests/test_stack_config.py; source/sushicore/stack_config.py
test_a_config_that_turns_vcpkg_off_ignores_an_explicit_root_too | merge | 4 | stack_config: use_vcpkg False resolves no vcpkg, whatever is present; merge with tests/test_stack_config.py::test_a_config_that_turns_vcpkg_off_resolves_none_even_with_a_tree_present | tests/test_stack_config.py; source/sushicore/stack_config.py
test_a_config_that_turns_vcpkg_on_resolves_the_tree | keep | 9 | stack_config: use_vcpkg True resolves the tree | tests/test_stack_config.py; source/sushicore/stack_config.py
test_a_config_that_never_sets_the_key_keeps_resolving_the_tree | keep | 9 | stack_config: an unset use_vcpkg keeps resolving the tree | tests/test_stack_config.py; source/sushicore/stack_config.py
```

### `tests/test_terminal_background.py`

```
test_dark_wins_over_a_light_colorfgbg | keep | 9 | terminal_background: a dark or light setting overrides COLORFGBG | tests/test_terminal_background.py; source/sushicore/terminal_background.py
test_light_wins_over_a_dark_colorfgbg | keep | 9 | terminal_background: a dark or light setting overrides COLORFGBG | tests/test_terminal_background.py; source/sushicore/terminal_background.py
test_auto_reads_a_dark_background_index | keep | 9 | terminal_background: auto reads COLORFGBG's last field against the dark indices (parametrised, four rows) | tests/test_terminal_background.py; source/sushicore/terminal_background.py
test_auto_reads_anything_else_as_not_dark | keep | 9 | terminal_background: an unreadable or missing COLORFGBG is not dark (parametrised, six rows) | tests/test_terminal_background.py; source/sushicore/terminal_background.py
test_auto_without_the_variable_is_not_dark | keep | 9 | terminal_background: an unreadable or missing COLORFGBG is not dark | tests/test_terminal_background.py; source/sushicore/terminal_background.py
```

### `tests/test_theme.py`

```
test_muted_defaults_to_dim | delete | 1 | a default value; the colour is a constant with no promise of its own (forbidden kind: trivial code) | tests/test_theme.py; source/sushicore/theme.py
test_muted_reaches_the_rich_style_map | keep | 9 | theme: the muted token reaches the Rich style map | tests/test_theme.py; source/sushicore/theme.py
test_muted_is_overridable_like_every_other_token | keep | 9 | theme: merged accepts the muted token | tests/test_theme.py; source/sushicore/theme.py
test_console_exposes_the_theme_it_was_built_with | delete | 1 | a getter that returns the object it was given (forbidden kind: trivial code) | tests/test_theme.py; source/sushicore/console.py
```

### `tests/test_toml_writer.py`

```
test_it_renders_tool_first_and_the_other_tables_sorted | split | 3 | toml_writer: tool is rendered first and the other tables sorted; toml_writer: backslashes in values become forward slashes; tests/test_config_base.py::test_the_document_writer_renders_every_table_it_is_given repeats the ordering from another file | tests/test_toml_writer.py; tests/test_config_base.py; source/sushicore/toml_writer.py
test_what_it_writes_reads_back_as_the_same_tables | resize | 8 | toml_writer: what it writes reads back as the same tables; the round trip crosses the file system, which is a boundary, so medium | tests/test_toml_writer.py; source/sushicore/toml_writer.py; source/sushicore/workspace.py
test_a_value_that_is_not_a_string_in_a_table_raises_instead_of_vanishing | resize | 8 | toml_writer: a non-string table value raises TypeError; the decision is on values and fits small, but tmp_path reaches the file system; seam: a render function that returns the text | tests/test_toml_writer.py; source/sushicore/toml_writer.py
test_a_top_level_value_that_is_not_a_table_raises | resize | 8 | toml_writer: a top-level value that is not a table raises TypeError; tmp_path reaches the file system; seam: the render function that returns the text | tests/test_toml_writer.py; source/sushicore/toml_writer.py
test_sub_tables_of_tool_become_platform_tables | split | 3 | toml_writer: tool sub-tables become [tool.<platform>] tables; toml_writer: backslashes in values become forward slashes; the literal "C:\cmake" is an invalid escape and needs a raw string | tests/test_toml_writer.py; tests/test_config_base.py; source/sushicore/toml_writer.py
```

### `tests/test_toolchain_args.py`

```
test_a_clangxx_gets_its_sibling_clang | keep | 9 | toolchain_args: clang++ and icpx get their sibling C driver | tests/test_toolchain_args.py; source/sushicore/toolchain_args.py
test_an_icpx_gets_its_sibling_icx | keep | 9 | toolchain_args: clang++ and icpx get their sibling C driver | tests/test_toolchain_args.py; source/sushicore/toolchain_args.py
test_a_bare_icpx_gets_icx_from_the_path | keep | 9 | toolchain_args: a bare icpx gets icx from PATH; shutil.which is patched, which is stdlib and allowed | tests/test_toolchain_args.py; source/sushicore/toolchain_args.py
test_a_clangxx_without_a_sibling_is_left_alone | merge | 4 | toolchain_args: a compiler with no sibling is returned unchanged; merge with tests/test_toolchain_args.py::test_a_non_clangxx_compiler_is_left_alone | tests/test_toolchain_args.py; source/sushicore/toolchain_args.py
test_a_non_clangxx_compiler_is_left_alone | merge | 4 | toolchain_args: a compiler with no sibling is returned unchanged; merge with tests/test_toolchain_args.py::test_a_clangxx_without_a_sibling_is_left_alone | tests/test_toolchain_args.py; source/sushicore/toolchain_args.py
test_the_windows_exe_suffix_is_preserved | keep | 9 | toolchain_args: the .exe suffix is kept | tests/test_toolchain_args.py; source/sushicore/toolchain_args.py
test_vcpkg_prefix_is_empty_without_a_root | rewrite | 1 | toolchain_args: vcpkg_prefix is empty without a root; a SimpleNamespace stand-in for the repository-owned StackConfig; rewrite with a real StackConfig(use_vcpkg=False), which touches no file | tests/test_toolchain_args.py; source/sushicore/toolchain_args.py; source/sushicore/stack_config.py
test_vcpkg_prefix_names_the_triplet | rewrite | 1 | toolchain_args: vcpkg_prefix names the triplet under the root; a SimpleNamespace stand-in for the repository-owned StackConfig; rewrite with a real StackConfig(vcpkg_root=...) | tests/test_toolchain_args.py; source/sushicore/toolchain_args.py; source/sushicore/stack_config.py
```

### `tests/test_typer_help.py`

```
test_root_help_groups_commands_under_their_panels | keep | 9 | typer_help: root help groups commands under their panels | tests/test_typer_help.py; source/sushicore/typer_help.py
test_a_bare_invocation_prints_the_same_page | keep | 9 | typer_help: a bare invocation prints the root page | tests/test_typer_help.py; source/sushicore/typer_help.py
test_leaf_help_lists_arguments_options_and_examples | split | 3 | typer_help: a leaf page lists its arguments; typer_help: a leaf page lists its options; typer_help: a leaf page lists its examples | tests/test_typer_help.py; source/sushicore/typer_help.py
test_leaf_help_shows_the_extras_typer_puts_on_a_parameter | split | 3 | typer_help: a parameter's required extra is shown; typer_help: a page prints no escape backslashes | tests/test_typer_help.py; source/sushicore/typer_help.py
test_a_sub_group_draws_its_own_page_not_a_leaf_page | keep | 9 | typer_help: a sub-group draws its own page | tests/test_typer_help.py; source/sushicore/typer_help.py
test_a_leaf_below_a_sub_group_draws_a_page | keep | 9 | typer_help: a leaf below a sub-group draws its page | tests/test_typer_help.py; source/sushicore/typer_help.py
test_a_command_with_no_panel_lands_under_commands | keep | 9 | typer_help: a command with no panel lands under Commands | tests/test_typer_help.py; source/sushicore/typer_help.py
test_no_logo_on_a_console_that_is_not_a_terminal | keep | 9 | typer_help: no logo on a non-terminal console | tests/test_typer_help.py; source/sushicore/typer_help.py
test_the_click_formatter_is_left_empty_for_a_page_drawing_group | keep | 9 | typer_help: the Click formatter writes nothing for a page-drawing group | tests/test_typer_help.py; source/sushicore/typer_help.py
test_the_provider_is_called_as_a_plain_function_not_bound_to_the_group | keep | 9 | typer_help: the provider is called once, as a plain function | tests/test_typer_help.py; source/sushicore/typer_help.py
test_looking_a_child_up_twice_leaves_it_with_one_help_page | keep | 9 | typer_help: a child looked up twice keeps one help page | tests/test_typer_help.py; source/sushicore/typer_help.py
test_the_root_page_shows_the_logo_on_a_terminal_with_256_colours_or_more | rewrite | 1 | typer_help: the root page shows the logo on a 256-colour or truecolour terminal; stand-in _TerminalConsole for the repository-owned Console; the rewrite needs an in-memory Renderer in source/sushicore/renderer.py whose raw Rich console is a terminal of a given colour system, width and background; none exists, PlainRenderer is colourless | tests/test_typer_help.py; source/sushicore/typer_help.py; source/sushicore/renderer.py; source/sushicore/console.py
test_the_page_reaches_a_truecolour_terminal_with_the_rolls_own_colour_codes | rewrite | 1 | typer_help: the truecolour page carries the rolled colour codes; stand-in _TerminalConsole; the rewrite needs the in-memory terminal Renderer in source/sushicore/renderer.py, which does not exist | tests/test_typer_help.py; source/sushicore/typer_help.py; source/sushicore/renderer.py
test_the_root_page_leaves_one_blank_line_above_the_logo_and_two_below_it | rewrite | 1 | typer_help: the root page has one blank line above the logo and two below; stand-in _TerminalConsole; the rewrite needs the in-memory terminal Renderer in source/sushicore/renderer.py, which does not exist; the name joins two layout facts, so split it when rewritten | tests/test_typer_help.py; source/sushicore/typer_help.py; source/sushicore/renderer.py
test_a_dark_terminal_draws_the_lockup_with_its_glow | rewrite | 1 | typer_help: a dark terminal draws the logo with its glow; stand-in _TerminalConsole; the rewrite needs the in-memory terminal Renderer in source/sushicore/renderer.py, which does not exist | tests/test_typer_help.py; source/sushicore/typer_help.py; source/sushicore/renderer.py
test_a_light_terminal_draws_the_lockup_without_a_glow | rewrite | 1 | typer_help: a light terminal draws the logo without glow; stand-in _TerminalConsole; the rewrite needs the in-memory terminal Renderer in source/sushicore/renderer.py, which does not exist | tests/test_typer_help.py; source/sushicore/typer_help.py; source/sushicore/renderer.py
test_a_console_too_narrow_for_the_wordmark_draws_the_mark_alone | rewrite | 1 | typer_help: a console too narrow for the wordmark draws the mark alone; stand-in _TerminalConsole; the rewrite needs the in-memory terminal Renderer in source/sushicore/renderer.py, which does not exist | tests/test_typer_help.py; source/sushicore/typer_help.py; source/sushicore/renderer.py
test_a_console_narrower_than_the_mark_draws_no_logo | rewrite | 1 | typer_help: a console narrower than the mark draws no logo; stand-in _TerminalConsole; the rewrite needs the in-memory terminal Renderer in source/sushicore/renderer.py, which does not exist | tests/test_typer_help.py; source/sushicore/typer_help.py; source/sushicore/renderer.py
test_a_leaf_page_does_not_show_the_logo_on_a_colour_terminal | rewrite | 1 | typer_help: a leaf page shows no logo; stand-in _TerminalConsole; the rewrite needs the in-memory terminal Renderer in source/sushicore/renderer.py, which does not exist | tests/test_typer_help.py; source/sushicore/typer_help.py; source/sushicore/renderer.py
test_the_root_page_hides_the_logo_on_a_standard_colour_terminal | rewrite | 1 | typer_help: a standard-colour terminal shows no logo; stand-in _TerminalConsole; the rewrite needs the in-memory terminal Renderer in source/sushicore/renderer.py, which does not exist | tests/test_typer_help.py; source/sushicore/typer_help.py; source/sushicore/renderer.py
test_the_root_page_hides_the_logo_when_colour_is_switched_off_on_a_terminal | rewrite | 1 | typer_help: colour switched off hides the logo; stand-in _TerminalConsole; the rewrite needs the in-memory terminal Renderer in source/sushicore/renderer.py, which does not exist | tests/test_typer_help.py; source/sushicore/typer_help.py; source/sushicore/renderer.py
test_a_group_whose_provider_raises_falls_back_to_typers_help | merge | 4 | typer_help: a provider that raises falls back to Typer's help with one warning; merge with tests/test_typer_help.py::test_a_child_whose_provider_raises_falls_back_to_typers_help; the caplog sink sits on the process-wide logger, so the merged test needs a logger seam (question 8) | tests/test_typer_help.py; source/sushicore/typer_help.py
test_a_child_whose_provider_raises_falls_back_to_typers_help | merge | 4 | typer_help: a provider that raises falls back to Typer's help with one warning; merge with tests/test_typer_help.py::test_a_group_whose_provider_raises_falls_back_to_typers_help; the caplog sink sits on the process-wide logger | tests/test_typer_help.py; source/sushicore/typer_help.py
test_a_help_group_used_without_a_provider_falls_back_to_typers_help | resize | 8 | typer_help: a group without a provider falls back to Typer's help with one warning; caplog installs a sink on the process-wide logger; seam: a logger argument to help_group | tests/test_typer_help.py; source/sushicore/typer_help.py
test_a_stray_close_tag_in_rich_help_is_logged_and_handed_to_typers_help | split | 3 | typer_help: a stray close tag in help markup is logged; typer_help: a stray close tag falls back to Typer's help without raising; the body asserts that a MarkupError escapes the invocation, so the name and the body disagree; the second promise has no passing test and needs a ruling on the defect | tests/test_typer_help.py; source/sushicore/typer_help.py
test_typer_alone_fails_on_the_same_stray_close_tag | delete | 3 | no promise of this unit: it asserts that Typer itself raises MarkupError | tests/test_typer_help.py
test_each_help_call_logs_one_warning_of_its_own | resize | 8 | typer_help: a provider that raises falls back to Typer's help with one warning per call; caplog sink on the process-wide logger; seam: a logger argument | tests/test_typer_help.py; source/sushicore/typer_help.py
test_a_block_that_fails_to_draw_leaves_no_part_of_the_page_on_the_console | rewrite | 1 | typer_help: a block that fails to draw leaves no part of the page on the console; monkeypatches the repository-owned HelpPage with the stand-in _HalfDrawnPage; rewrite with a real HelpPage whose block raises, through a seam | tests/test_typer_help.py; source/sushicore/typer_help.py; source/sushicore/help/page.py
```

### `tests/test_typer_theme.py`

```
test_apply_points_typer_styles_at_the_theme | resize | 8 | typer_theme: Typer's help styles follow the theme; it writes Typer's process-wide rich_utils module and restores three of its eleven names; seam: apply_typer_theme takes the target module | tests/test_typer_theme.py; source/sushicore/typer_theme.py
```

### `tests/test_windows_console.py`

```
test_both_handles_are_turned_on_with_their_old_mode_or_the_bit | rewrite | 1 | windows_console: both standard handles get the VT bit and keep their other mode bits; asserts the order of GetStdHandle calls, a change detector (forbidden kind); rewrite without the order check | tests/test_windows_console.py; source/sushicore/windows_console.py
test_a_handle_with_the_bit_already_set_is_not_written_but_counts_as_on | resize | 8 | windows_console: a handle already on is not written and counts as on; reaches sys.platform through the on_windows fixture, a process-wide value; seam: enable_virtual_terminal takes a platform argument; FakeKernel32 is kernel32, not owned, so it is allowed | tests/test_windows_console.py; tests/conftest.py; source/sushicore/windows_console.py
test_a_redirected_handle_is_skipped_and_the_other_still_counts | resize | 8 | windows_console: a redirected handle is skipped and the other still counts; reaches sys.platform through on_windows; seam: a platform argument | tests/test_windows_console.py; tests/conftest.py; source/sushicore/windows_console.py
test_two_redirected_handles_give_false | resize | 8 | windows_console: two redirected handles give False; reaches sys.platform through on_windows; seam: a platform argument | tests/test_windows_console.py; tests/conftest.py; source/sushicore/windows_console.py
test_a_refused_write_does_not_count_as_on | resize | 8 | windows_console: a refused write does not count as on; reaches sys.platform through on_windows; seam: a platform argument | tests/test_windows_console.py; tests/conftest.py; source/sushicore/windows_console.py
test_an_os_error_from_the_api_gives_false | resize | 8 | windows_console: an OS error gives False; reaches sys.platform through on_windows; seam: a platform argument | tests/test_windows_console.py; tests/conftest.py; source/sushicore/windows_console.py
test_a_missing_function_gives_false | resize | 8 | windows_console: a missing function gives False; reaches sys.platform through on_windows; seam: a platform argument | tests/test_windows_console.py; tests/conftest.py; source/sushicore/windows_console.py
test_off_windows_nothing_is_called_and_the_result_is_false | resize | 8 | windows_console: off Windows nothing is called and the result is False; reaches sys.platform by monkeypatching it to linux; seam: a platform argument | tests/test_windows_console.py; source/sushicore/windows_console.py
test_the_default_kernel32_declares_a_pointer_wide_handle | resize | 8 | windows_console: the default kernel32 declares pointer-wide handle prototypes; loads the real kernel32 through ctypes.WinDLL, a file-level boundary, so medium; no seam needed | tests/test_windows_console.py; source/sushicore/windows_console.py
```

### `tests/test_workspace/test_link.py`

```
test_write_then_read_returns_the_workspace | keep | 9 | [L1] | tests/test_workspace/test_link.py; source/sushicore/workspace.py
test_read_raises_on_a_malformed_local_config_as_config_loading_does | keep | 9 | [L2] | tests/test_workspace/test_link.py; tests/test_workspace/test_read_toml.py; source/sushicore/workspace.py
test_write_keeps_other_tables | delete | 4 | duplicate of [L3] in test_write_and_clear_keep_comments_and_non_string_values, which checks the exact text including the tool table | tests/test_workspace/test_link.py; source/sushicore/workspace.py
test_read_ignores_a_pointer_to_a_deleted_workspace | keep | 9 | [L9] | tests/test_workspace/test_link.py; source/sushicore/workspace.py
test_clear_removes_the_file_when_nothing_else_remains | keep | 9 | [L4] | tests/test_workspace/test_link.py; source/sushicore/workspace.py
test_clear_keeps_the_file_when_other_tables_remain | keep | 9 | [L5] | tests/test_workspace/test_link.py; source/sushicore/workspace.py
test_write_and_clear_keep_comments_and_non_string_values | keep | 9 | [L3] | tests/test_workspace/test_link.py; source/sushicore/workspace.py
test_rewriting_the_link_replaces_only_its_table | keep | 9 | [L11] | tests/test_workspace/test_link.py; source/sushicore/workspace.py
test_a_relative_pointer_resolves_against_the_config_dir | keep | 9 | [L10] | tests/test_workspace/test_link.py; source/sushicore/workspace.py
test_a_decorated_header_is_replaced_not_duplicated | keep | 9 | [L6], both header spellings in one row table | tests/test_workspace/test_link.py; source/sushicore/workspace.py
test_a_root_inline_table_is_refused_and_left_unchanged | merge | 4 | [L7]; merge with test_a_header_inside_a_multiline_string_never_corrupts_the_file, the same refusal with unchanged bytes | tests/test_workspace/test_link.py; source/sushicore/workspace.py
test_a_header_inside_a_multiline_string_never_corrupts_the_file | keep | 9 | [L7]; the row table that takes the merged case | tests/test_workspace/test_link.py; source/sushicore/workspace.py
test_crlf_line_endings_are_preserved | keep | 9 | [L8] | tests/test_workspace/test_link.py; source/sushicore/workspace.py
```

### `tests/test_workspace/test_modules.py`

```
test_no_file_means_no_modules | keep | 9 | [M1] | tests/test_workspace/test_modules.py; source/sushicore/workspace.py
test_write_then_read | keep | 9 | [M2] | tests/test_workspace/test_modules.py; source/sushicore/workspace.py
test_write_keeps_the_tool_table | keep | 9 | [M3] | tests/test_workspace/test_modules.py; source/sushicore/workspace.py
test_remove_reports_whether_it_removed | keep | 9 | [M4] | tests/test_workspace/test_modules.py; source/sushicore/workspace.py
```

### `tests/test_workspace/test_read_toml.py`

```
test_read_toml_reports_a_malformed_file_as_a_config_error | keep | 9 | [R1] | tests/test_workspace/test_read_toml.py; source/sushicore/workspace.py
```

### `tests/testing/test_budget.py`

```
test_a_run_is_default_only_when_nothing_narrowed_it | keep | 9 | [B1] | tests/testing/test_budget.py; source/sushicore/testing/budget.py; source/sushicore/testing/labels.py
test_the_large_tests_start_only_when_something_narrows_them | keep | 9 | [B2] | tests/testing/test_budget.py; source/sushicore/testing/labels.py
test_the_reader_is_called_only_where_the_repository_carries_it | split | 3 | [B3] and [B4]; the reader and exemption files it writes are a file reach that the split halves answer at question 8 | tests/testing/test_budget.py; source/sushicore/testing/budget.py
```

### `tests/testing/test_commands.py`

```
test_the_command_declares_the_same_options_in_every_cli | split | 3 | [C1]; the shared option names repeat [O1] in tests/testing/test_options.py, which stays, so only the command's own names remain as this promise | tests/testing/test_commands.py; tests/testing/test_options.py; source/sushicore/testing/commands.py
test_the_options_a_module_cannot_serve_are_hidden | resize | 8 | [C2]; in-process Typer with no device, file, thread or clock, so small sees it and medium is larger than needed | tests/testing/test_commands.py; source/sushicore/testing/commands.py; source/sushicore/testing/module_tests.py
test_asking_for_large_without_a_filter_exits_with_the_usage_code | delete | 4 | duplicate of tests/testing/test_session.py::test_an_unfiltered_large_run_is_refused_before_anything_runs ([S1], own module); the exit mapping is one line of wiring | tests/testing/test_commands.py; tests/testing/test_session.py; source/sushicore/testing/commands.py; source/sushicore/testing/session.py
```

### `tests/testing/test_labels.py`

```
test_labels_make_the_ctest_patterns | keep | 9 | [LB1] | tests/testing/test_labels.py; source/sushicore/testing/labels.py
test_a_quarantine_asked_with_a_size_keeps_the_size | keep | 9 | [LB2] | tests/testing/test_labels.py; source/sushicore/testing/labels.py
```

### `tests/testing/test_module_tests.py`

```
test_a_module_that_names_no_tree_check_has_no_fault_to_report | delete | 1 | forbidden kind, a default value; the promise that a default check passes a run is exercised by tests/testing/test_session.py::test_a_run_writes_a_junit_file_and_hands_it_to_the_reader, which needs exit 0 with the default check | tests/testing/test_module_tests.py; tests/testing/test_session.py; source/sushicore/testing/module_tests.py
```

### `tests/testing/test_options.py`

```
test_the_shared_options_carry_the_names_every_cli_spells_alike | keep | 9 | [O1] | tests/testing/test_options.py; source/sushicore/testing/options.py
```

### `tests/testing/test_session.py`

```
test_an_unfiltered_large_run_is_refused_before_anything_runs | keep | 9 | [S1]; takes tmp_path only as a root value, and the refusal comes before any tree access | tests/testing/test_session.py; source/sushicore/testing/session.py
test_a_missing_tree_stops_the_run_and_names_the_build_command | resize | 8 | [S2]; the tree check reads the real file system; seam: a file-system port with an in-memory adapter answers the tree check, the owner rules on the port | tests/testing/test_session.py; source/sushicore/testing/session.py; source/sushicore/testing/module_tests.py
test_a_run_writes_a_junit_file_and_hands_it_to_the_reader | split | 3 | [S3] and [S4] | tests/testing/test_session.py; source/sushicore/testing/session.py; source/sushicore/testing/budget.py
test_a_failing_run_keeps_its_code_and_still_prints_the_budget_line | split | 3 | [S5] and [S6] | tests/testing/test_session.py; source/sushicore/testing/session.py; source/sushicore/testing/budget.py
test_a_run_that_wrote_no_junit_file_skips_the_line_and_says_so | resize | 8 | [S7]; the junit and reader presence checks read the real file system; seam: file-system port | tests/testing/test_session.py; source/sushicore/testing/session.py; source/sushicore/testing/budget.py
test_a_sanitizer_is_built_and_its_tree_is_the_one_tested | resize | 8 | [S8]; the junit is written and read in a temporary folder; seam: file-system port | tests/testing/test_session.py; source/sushicore/testing/session.py; source/sushicore/testing/module_tests.py
test_a_failed_sanitizer_build_ends_the_run_with_its_code_and_runs_no_test | keep | 9 | [S9]; the build fails before any tree access | tests/testing/test_session.py; source/sushicore/testing/session.py
test_a_module_without_the_sanitizer_or_the_suite_is_told_so_with_the_usage_code | split | 3 | [S10] and [S11] | tests/testing/test_session.py; source/sushicore/testing/session.py; source/sushicore/testing/module_tests.py
test_the_own_suite_refuses_an_option_it_would_drop_and_a_sanitizer_matches_without_case | split | 3 | [S12] and [S13]; the sanitizer half then reaches a temporary folder and is answered at question 8 once split | tests/testing/test_session.py; source/sushicore/testing/session.py; source/sushicore/testing/module_tests.py
test_the_own_suite_runs_for_the_selection_and_skips_ctest | keep | 9 | [S14]; the own-suite path returns before any tree access | tests/testing/test_session.py; source/sushicore/testing/session.py
test_a_run_is_marked_not_rebuilt_unless_the_module_says_it_rebuilt | resize | 8 | [S15]; the build folder, the reader file and the junit are real files; seam: file-system port | tests/testing/test_session.py; source/sushicore/testing/session.py; source/sushicore/testing/budget.py
test_a_sanitizer_run_is_rebuilt_because_it_builds_its_tree_first | resize | 8 | [S16]; real folders and a reader file; seam: file-system port | tests/testing/test_session.py; source/sushicore/testing/session.py; source/sushicore/testing/budget.py
test_a_run_shuffles_with_the_given_seed_and_prints_it | split | 3 | [S17] and [S18] | tests/testing/test_session.py; source/sushicore/testing/session.py
test_a_run_without_a_seed_draws_one_in_the_range_gtest_accepts | resize | 8 | [S19]; draws from the process-wide random module and reads the build folder; seam: an injected seed source and the file-system port | tests/testing/test_session.py; source/sushicore/testing/session.py
test_a_run_that_turns_the_shuffle_off_gives_ctest_no_seed | resize | 8 | [S20]; a real build folder; seam: file-system port | tests/testing/test_session.py; source/sushicore/testing/session.py
test_a_ctest_call_without_the_shuffle_keyword_still_runs_and_the_run_says_so | resize | 8 | [S21]; a real build folder; the test also rebuilds ModuleTests by copying __dict__, where dataclasses.replace fits; seam: file-system port | tests/testing/test_session.py; source/sushicore/testing/session.py; source/sushicore/testing/module_tests.py
```

### `tests/ui/test_component.py`

```
test_a_class_with_render_satisfies_the_protocol | merge | 4 | [CP1]; merge with test_a_class_without_render_does_not, the same protocol with the other input | tests/ui/test_component.py; source/sushicore/ui/component.py
test_a_class_without_render_does_not | merge | 4 | [CP1]; merge with test_a_class_with_render_satisfies_the_protocol | tests/ui/test_component.py; source/sushicore/ui/component.py
```

### `tests/ui/test_definition_list.py`

```
test_entries_align_and_the_text_wraps_inside_its_column | keep | 9 | [DL1] | tests/ui/test_definition_list.py; source/sushicore/ui/definition_list.py; tests/ui/capture.py
test_a_term_with_brackets_is_printed_literally | keep | 9 | [DL2] | tests/ui/test_definition_list.py; source/sushicore/ui/definition_list.py
test_an_entry_without_text_prints_its_term_alone | keep | 9 | [DL3] | tests/ui/test_definition_list.py; source/sushicore/ui/definition_list.py
test_an_unescaped_extra_marker_stays_on_the_page | delete | 4 | format copy of tests/test_markup.py::test_a_bracket_that_names_no_style_is_escaped; the bracket format is listed once, in the markup owner's test file | tests/ui/test_definition_list.py; tests/test_markup.py; source/sushicore/markup.py
test_an_escaped_extra_marker_shows_its_brackets_once | delete | 4 | format copy of tests/test_markup.py::test_a_bracket_after_an_odd_run_of_backslashes_is_escaped_already; the markup owner's file holds the rule | tests/ui/test_definition_list.py; tests/test_markup.py; source/sushicore/markup.py
test_a_bracket_that_names_a_style_still_styles_its_text | keep | 9 | [DL6] | tests/ui/test_definition_list.py; source/sushicore/ui/definition_list.py; tests/ui/capture.py
test_a_theme_style_name_in_the_text_is_still_a_tag | keep | 9 | [DL7], the component passes its theme styles to the markup | tests/ui/test_definition_list.py; source/sushicore/ui/definition_list.py
test_a_row_is_not_padded_to_the_console_width | keep | 9 | [DL8] | tests/ui/test_definition_list.py; source/sushicore/ui/definition_list.py
test_the_heading_is_bold_and_the_term_carries_no_bold_in_the_default_theme | split | 3 | [DL4] and [DL5] | tests/ui/test_definition_list.py; source/sushicore/ui/definition_list.py; source/sushicore/theme.py
test_a_term_is_amber_and_a_heading_bold_amber_in_the_sushiweb_theme | split | 3 | [DL4] and [DL5]; the term half then merges with the other term-style rows | tests/ui/test_definition_list.py; source/sushicore/ui/definition_list.py; source/sushicore/theme.py
test_a_term_is_plain_and_a_heading_bold_when_the_theme_command_style_is_only_bold | split | 3 | [DL4] and [DL5] | tests/ui/test_definition_list.py; source/sushicore/ui/definition_list.py; source/sushicore/theme.py
test_a_theme_whose_command_style_is_not_bold_keeps_its_term_style | merge | 4 | [DL5]; merge with test_a_term_is_plain_and_a_heading_bold_when_the_theme_command_style_is_only_bold, the same term-style promise with another theme | tests/ui/test_definition_list.py; source/sushicore/ui/definition_list.py; source/sushicore/theme.py
```

### `tests/ui/test_header.py`

```
test_header_is_a_blank_line_then_a_rule_holding_the_title | keep | 9 | [H1] | tests/ui/test_header.py; source/sushicore/ui/header.py; tests/ui/capture.py
test_a_256_colour_render_can_run_before_the_truecolour_one | merge | 4 | [H2]; merge with test_a_truecolour_render_keeps_its_codes_after_a_256_colour_one. Its name and comment describe a run order, which is shared state (Determinism rule 5); the merged rows remove the pairing | tests/ui/test_header.py; source/sushicore/ui/header.py; tests/ui/capture.py
test_a_truecolour_render_keeps_its_codes_after_a_256_colour_one | merge | 4 | [H2]; merge with test_a_256_colour_render_can_run_before_the_truecolour_one; the pairing with the other test is the run-order coupling | tests/ui/test_header.py; source/sushicore/ui/header.py; tests/ui/capture.py
test_a_marked_up_title_prints_without_its_tags | keep | 9 | [H3] | tests/ui/test_header.py; source/sushicore/ui/header.py
test_an_escaped_bracket_in_a_title_prints_literally | keep | 9 | [H4]; the header uses Text.from_markup, so the escaped bracket catches a mutant that prints raw markup | tests/ui/test_header.py; source/sushicore/ui/header.py
test_the_theme_style_sits_under_the_markup_of_a_title | keep | 9 | [H5] | tests/ui/test_header.py; source/sushicore/ui/header.py; source/sushicore/theme.py
```

### `tests/ui/test_logo.py`

```
test_two_pixel_rows_become_one_terminal_row | merge | 4 | [G1]; merge with test_the_glowing_lockup_is_eight_rows_and_seventy_two_columns, all row counts go into one dimension table | tests/ui/test_logo.py; source/sushicore/ui/logo.py; source/sushicore/brand.py
test_the_glowing_lockup_is_eight_rows_and_seventy_two_columns | merge | 4 | [G1]; merge with test_two_pixel_rows_become_one_terminal_row into the dimension table | tests/ui/test_logo.py; source/sushicore/ui/logo.py
test_the_plain_lockup_is_eight_rows_and_sixty_eight_columns | merge | 4 | [G1]; merge with test_the_glowing_lockup_is_eight_rows_and_seventy_two_columns into the dimension table | tests/ui/test_logo.py; source/sushicore/ui/logo.py
test_the_glowing_mark_alone_stays_inside_twenty_columns | merge | 4 | [G1]; merge with test_the_plain_mark_alone_is_six_rows_and_sixteen_columns into the dimension table | tests/ui/test_logo.py; source/sushicore/ui/logo.py
test_the_plain_mark_alone_is_six_rows_and_sixteen_columns | merge | 4 | [G1]; merge with test_the_glowing_mark_alone_stays_inside_twenty_columns into the dimension table | tests/ui/test_logo.py; source/sushicore/ui/logo.py
test_width_counts_the_indent | delete | 2 | [G1]; with indent 0 an ignored indent would still pass, but test_the_plain_lockup_is_eight_rows_and_sixty_eight_columns pins 68 as 66 plus the default indent 2, so the promise has another test | tests/ui/test_logo.py; source/sushicore/ui/logo.py
test_the_widest_row_is_as_wide_as_the_width_says | keep | 9 | [G2], four cases | tests/ui/test_logo.py; source/sushicore/ui/logo.py
test_the_plain_logo_has_no_blank_edge_row_or_column | keep | 9 | [G3], two cases | tests/ui/test_logo.py; source/sushicore/ui/logo.py
test_the_plain_mark_alone_has_no_blank_first_line | merge | 4 | [G3]; merge with test_the_plain_logo_has_no_blank_edge_row_or_column, the same check with the wordmark off | tests/ui/test_logo.py; source/sushicore/ui/logo.py
test_indent_prefixes_every_non_empty_row | keep | 9 | [G4] | tests/ui/test_logo.py; source/sushicore/ui/logo.py
test_each_cell_picks_the_block_that_shows_its_two_pixels | rewrite | 8 | [G5]; monkeypatches sushicore.ui.logo module globals, a reach into process-wide state; seam: Logo takes its grids and palette as values, the owner rules on the public fields | tests/ui/test_logo.py; source/sushicore/ui/logo.py; source/sushicore/brand.py
test_two_different_colours_share_one_cell_as_foreground_and_background | rewrite | 8 | [G6]; the same module-global monkeypatch; seam as for test_each_cell_picks_the_block_that_shows_its_two_pixels | tests/ui/test_logo.py; source/sushicore/ui/logo.py; source/sushicore/brand.py
test_the_wordmark_sits_two_columns_after_the_mark | rewrite | 8 | [G7]; module-global monkeypatch; seam as above | tests/ui/test_logo.py; source/sushicore/ui/logo.py; source/sushicore/brand.py
test_a_shorter_grid_is_centred_against_the_taller_one | rewrite | 8 | [G7]; module-global monkeypatch; seam as above | tests/ui/test_logo.py; source/sushicore/ui/logo.py; source/sushicore/brand.py
test_transparent_edge_rows_and_columns_are_dropped_without_the_glow | rewrite | 8 | [G8]; module-global monkeypatch; seam as above | tests/ui/test_logo.py; source/sushicore/ui/logo.py; source/sushicore/brand.py
test_the_same_edges_stay_with_the_glow | rewrite | 8 | [G8]; module-global monkeypatch; seam as above | tests/ui/test_logo.py; source/sushicore/ui/logo.py; source/sushicore/brand.py
test_an_odd_trimmed_row_count_gains_one_transparent_row_at_the_bottom | rewrite | 8 | [G9]; module-global monkeypatch; seam as above | tests/ui/test_logo.py; source/sushicore/ui/logo.py; source/sushicore/brand.py
test_the_trimmed_mark_sets_the_width_beside_the_wordmark | rewrite | 8 | [G10]; module-global monkeypatch; seam as above | tests/ui/test_logo.py; source/sushicore/ui/logo.py; source/sushicore/brand.py
test_the_glow_rings_draw_nothing_until_the_glow_is_asked_for | rewrite | 8 | [G11]; module-global monkeypatch; seam as above | tests/ui/test_logo.py; source/sushicore/ui/logo.py; source/sushicore/brand.py
test_the_glow_rings_draw_in_their_own_colours_when_asked | rewrite | 8 | [G11]; module-global monkeypatch; seam as above | tests/ui/test_logo.py; source/sushicore/ui/logo.py; source/sushicore/brand.py
test_no_glow_colour_reaches_a_light_terminal | keep | 9 | [G12]; the name speaks of a light terminal, which the code does not model, so the name needs a rename | tests/ui/test_logo.py; source/sushicore/ui/logo.py
test_only_the_wordmark_draws_in_the_terminal_foreground | keep | 9 | [G13] | tests/ui/test_logo.py; source/sushicore/ui/logo.py
test_the_light_logo_matches_its_golden_file | rewrite | 5 | [G14]; compares the full ANSI string, so a Rich change in escape ordering fails it while the logo is unchanged; it also reads a golden file in a small test (question 8); oracle to name: the brand grids and palette, cell by cell | tests/ui/test_logo.py; source/sushicore/ui/logo.py; source/sushicore/brand.py
test_the_dark_logo_matches_its_golden_file | rewrite | 5 | [G14]; the same reasons as the light golden | tests/ui/test_logo.py; source/sushicore/ui/logo.py; source/sushicore/brand.py
test_width_matches_the_widest_row_when_the_wordmark_is_ragged | rewrite | 8 | [G15]; module-global monkeypatch; seam as above | tests/ui/test_logo.py; source/sushicore/ui/logo.py; source/sushicore/brand.py
```

### `tests/ui/test_panel.py`

```
test_panel_puts_the_title_on_the_top_border_and_the_body_inside | keep | 9 | [P1] | tests/ui/test_panel.py; source/sushicore/ui/panel.py; tests/ui/capture.py
test_panel_body_keeps_rich_markup | keep | 9 | [P2] | tests/ui/test_panel.py; source/sushicore/ui/panel.py
test_a_marked_up_title_prints_without_its_tags | keep | 9 | [P3] | tests/ui/test_panel.py; source/sushicore/ui/panel.py
test_an_escaped_bracket_in_a_title_prints_literally | keep | 9 | [P4] | tests/ui/test_panel.py; source/sushicore/ui/panel.py
```

### `tests/ui/test_table.py`

```
test_table_draws_title_header_rule_and_rows | keep | 9 | [T1] | tests/ui/test_table.py; source/sushicore/ui/table.py; tests/ui/capture.py
test_table_without_a_title_starts_at_the_header_row | merge | 4 | [T1]; merge with test_table_draws_title_header_rule_and_rows, title present and absent as two inputs | tests/ui/test_table.py; source/sushicore/ui/table.py
test_table_has_no_outer_frame | delete | 4 | [T1]; duplicate of the exact-text test test_table_draws_title_header_rule_and_rows, which already fails on any frame character | tests/ui/test_table.py; source/sushicore/ui/table.py
test_group_by_must_name_one_of_the_columns | keep | 9 | [T2] | tests/ui/test_table.py; source/sushicore/ui/table.py
test_the_grouped_table_keeps_its_title_and_a_blank_line_under_it | keep | 9 | [T3] | tests/ui/test_table.py; source/sushicore/ui/table.py
test_the_column_headers_are_drawn_once_without_the_group_column | keep | 9 | [T4] | tests/ui/test_table.py; source/sushicore/ui/table.py
test_a_muted_rule_separates_the_headers_from_the_first_group | keep | 9 | [T5] | tests/ui/test_table.py; source/sushicore/ui/table.py
test_each_group_value_becomes_a_heading_in_order_of_first_appearance | keep | 9 | [T6] | tests/ui/test_table.py; source/sushicore/ui/table.py
test_one_blank_line_separates_the_groups_and_none_follows_the_last | keep | 9 | [T6] | tests/ui/test_table.py; source/sushicore/ui/table.py
test_the_group_column_is_gone_from_the_rows | keep | 9 | [T7] | tests/ui/test_table.py; source/sushicore/ui/table.py
test_every_column_but_the_last_lines_up_across_the_groups | keep | 9 | [T8] | tests/ui/test_table.py; source/sushicore/ui/table.py
test_only_the_last_column_wraps | keep | 9 | [T9] | tests/ui/test_table.py; source/sushicore/ui/table.py
test_a_wrapped_detail_keeps_its_first_word_under_the_first_line | keep | 9 | [T9]; the column check fails both a shift left and a shift right | tests/ui/test_table.py; source/sushicore/ui/table.py
test_an_empty_group_value_is_drawn_as_a_dash | keep | 9 | [T10] | tests/ui/test_table.py; source/sushicore/ui/table.py
test_a_status_cell_takes_the_theme_style_its_word_maps_to | keep | 9 | [T11] | tests/ui/test_table.py; source/sushicore/ui/table.py; source/sushicore/theme.py
test_a_status_word_is_recognised_whatever_its_case | keep | 9 | [T11] | tests/ui/test_table.py; source/sushicore/ui/table.py
test_a_cell_that_is_not_a_status_word_carries_no_style | keep | 9 | [T12] | tests/ui/test_table.py; source/sushicore/ui/table.py
test_a_bracket_that_names_no_style_stays_in_a_flat_cell | delete | 4 | format copy of tests/test_markup.py::test_a_bracket_that_names_no_style_is_escaped | tests/ui/test_table.py; tests/test_markup.py; source/sushicore/markup.py
test_a_bracket_that_names_no_style_stays_in_a_grouped_cell | delete | 4 | format copy of tests/test_markup.py::test_a_bracket_that_names_no_style_is_escaped, grouped path | tests/ui/test_table.py; tests/test_markup.py; source/sushicore/markup.py
test_a_cell_that_names_a_theme_style_is_drawn_in_that_style_and_without_its_tags | keep | 9 | [T13] | tests/ui/test_table.py; source/sushicore/ui/table.py; source/sushicore/theme.py
test_a_grouped_cell_that_names_a_theme_style_is_drawn_in_that_style | merge | 4 | [T13]; merge with test_a_cell_that_names_a_theme_style_is_drawn_in_that_style_and_without_its_tags, flat and grouped as two inputs | tests/ui/test_table.py; source/sushicore/ui/table.py
test_a_styled_cell_may_hold_a_bracket_that_names_no_style | delete | 4 | format copy of tests/test_markup.py::test_a_bracket_that_names_no_style_is_escaped | tests/ui/test_table.py; tests/test_markup.py; source/sushicore/markup.py
```

### `tests/ui/test_title.py`

```
test_title_draws_the_name_then_the_description | keep | 9 | [TI1] | tests/ui/test_title.py; source/sushicore/ui/title.py; tests/ui/capture.py
test_title_without_a_description_is_the_name_alone | keep | 9 | [TI2] | tests/ui/test_title.py; source/sushicore/ui/title.py
test_description_interprets_rich_markup | keep | 9 | [TI3] | tests/ui/test_title.py; source/sushicore/ui/title.py
test_a_bracket_that_names_a_style_still_styles_its_text | keep | 9 | [TI4] | tests/ui/test_title.py; source/sushicore/ui/title.py
test_an_unescaped_extra_marker_stays_in_the_description | delete | 4 | format copy of tests/test_markup.py::test_a_bracket_that_names_no_style_is_escaped | tests/ui/test_title.py; tests/test_markup.py; source/sushicore/markup.py
test_an_escaped_extra_marker_shows_its_brackets_once | delete | 4 | format copy of tests/test_markup.py::test_a_bracket_after_an_odd_run_of_backslashes_is_escaped_already | tests/ui/test_title.py; tests/test_markup.py; source/sushicore/markup.py
test_a_theme_style_name_in_the_description_is_still_a_tag | keep | 9 | [TI5], the component passes its theme styles to the markup | tests/ui/test_title.py; source/sushicore/ui/title.py
```

### `tests/ui/test_usage.py`

```
test_usage_keeps_square_brackets_literal | keep | 9 | [U1] | tests/ui/test_usage.py; source/sushicore/ui/usage.py; tests/ui/capture.py
```

### `tools/tests/test_check_package_layers.py`

```
PackageLayersTest.test_reports_a_module_without_a_layer | resize | 8 | rule_unlayered_module; the rule walks source/sushicore on disk, but its decision is a key tested against a layer table, a value decision, so small; seam: a core _unlayered_keys(package, keys) that takes the keys _key derives from paths | tools/tests/test_check_package_layers.py; tools/layering/check_package_layers.py
PackageLayersTest.test_reports_every_form_of_an_upward_import | resize | 8 | rule_upward_import, every import form; decided on the parsed tree, so small; seam: a core _upward_imports(package, own, own_parts, tree) yielding (line, target) out of rule_upward_import | tools/tests/test_check_package_layers.py; tools/layering/check_package_layers.py
PackageLayersTest.test_a_sideways_import_passes_only_where_the_package_allows_it | resize | 8 | rule_upward_import, same-layer import allowed only in a non-strict package; decided on values, so small; seam: the same _upward_imports core, fed the source text of each module | tools/tests/test_check_package_layers.py; tools/layering/check_package_layers.py
PackageLayersTest.test_reports_a_forbidden_import_at_module_level_only_where_asked | resize | 8 | rule_forbidden_import, the nested flag; decided on the parsed tree, so small; seam: a core _forbidden_names(package, tree) yielding (line, name) out of rule_forbidden_import | tools/tests/test_check_package_layers.py; tools/layering/check_package_layers.py
PackageLayersTest.test_accepts_a_component_of_the_right_shape | resize | 8 | rule_ui_component, a right-shaped component yields no issue; the import check is inline in rule_ui_component; seam: _component_problems(stem, tree) (takes only path.stem, so pass the stem) and a new _import_problems(tree) pulled out of rule_ui_component | tools/tests/test_check_package_layers.py; tools/layering/check_package_layers.py
PackageLayersTest.test_reports_each_way_a_component_breaks_its_shape | split | 3 | several promises in one body, one per shape rule: the final mark, the frozen slots dataclass, the render signature, the forbidden import of sushicore.console; split into four tests, each then sized by question 8 through the seam named for the test above | tools/tests/test_check_package_layers.py; tools/layering/check_package_layers.py
PackageLayersTest.test_reports_a_file_whose_class_is_not_named_after_it | resize | 8 | rule_ui_component, the class must be named after the file; decided on the parsed tree, so small; seam: _component_problems(stem, tree) | tools/tests/test_check_package_layers.py; tools/layering/check_package_layers.py
```

### `tools/tests/test_check_test_additions.py`

```
CheckTestAdditionsTest.test_a_commit_at_its_limit_passes_and_one_over_it_is_named | delete | 3 | tools/testing/check_test_additions.py was removed from the shared tools upstream: D:/Projects/sushiskills/tools/testing holds no such file; this copy and its test are a leftover | tools/tests/test_check_test_additions.py; tools/testing/check_test_additions.py
CheckTestAdditionsTest.test_a_fix_has_the_smaller_limit | delete | 3 | the same removal: tools/testing/check_test_additions.py no longer exists upstream in sushiskills; leftover copy | tools/tests/test_check_test_additions.py; tools/testing/check_test_additions.py
CheckTestAdditionsTest.test_a_second_program_needs_the_owners_line | delete | 3 | the same removal: tools/testing/check_test_additions.py no longer exists upstream in sushiskills; leftover copy | tools/tests/test_check_test_additions.py; tools/testing/check_test_additions.py
CheckTestAdditionsTest.test_the_owners_line_approves_a_second_program | delete | 3 | the same removal: tools/testing/check_test_additions.py no longer exists upstream in sushiskills; leftover copy | tools/tests/test_check_test_additions.py; tools/testing/check_test_additions.py
CheckTestAdditionsTest.test_a_repository_that_sets_no_base_commit_is_not_checked | delete | 3 | the same removal: tools/testing/check_test_additions.py no longer exists upstream in sushiskills; leftover copy | tools/tests/test_check_test_additions.py; tools/testing/check_test_additions.py
```

### `tools/tests/test_test_budget_settings.py`

```
TestBudgetSettingsTest.test_the_skill_table_matches_the_settings | rewrite | 1 | forbidden kind: control flow in the body (the skipTest guard); it is the only test of the promise that the skill's Budget table equals K_TEST_BUDGET; in this tree skills/ is absent, so the test always skips and checks nothing; rewrite with the skip moved into the fixture and the skill path passed in | tools/tests/test_test_budget_settings.py; tools/settings.py
TestBudgetSettingsTest.test_reads_a_number_with_a_thousands_space_and_a_trailing_note | split | 3 | several promises in one body: a thousands-spaced number parses, a trailing note is dropped, a row no key names is ignored, rows outside the Budget heading are ignored; read_budget is defined in this test file, not in a module, so it needs a home before the split tests can import it | tools/tests/test_test_budget_settings.py; tools/settings.py
TestBudgetSettingsTest.test_names_each_key_that_differs | resize | 8 | settings: differences() names each differing key in sorted order, None for a missing side; plain values, so small; the file-level K_TEST_SIZE = "medium" is the wrong label for this test; no seam needed, the helper is pure | tools/tests/test_test_budget_settings.py; tools/settings.py
TestBudgetSettingsTest.test_every_row_of_the_table_has_a_constant | resize | 8 | settings: the label map and K_TEST_BUDGET name the same keys; a comparison of values, so small; Q4: test_the_skill_table_matches_the_settings is the larger copy of this key check, so this smaller copy stays; file-level medium is the wrong label | tools/tests/test_test_budget_settings.py; tools/settings.py
```

## Adds

Promises a header or a port states that no test checks: `unit: promise | oracle | size`.

```
discovery: find prunes the build-system folders and the CLI's skip names at any depth | exact list on a temp tree | medium
discovery: find stops descending at max_depth | exact list on a temp tree | medium
build_env: prepend_path puts the directories first in a case-insensitive variable | exact value | small
build_env: StackBuildEnv.cache_key changes with platform, vcvars or a sibling directory and not otherwise | equality of keys with a real ModuleProfile | small
citations: rewrite_id_citations rewrites every citation of a renamed ID below root and lists them without apply | exact list and text on a temp tree | medium
build_report: ninja_log_offset returns the log size, so of_build reads only the new edges | file size on a temp tree | medium
build_report: BuildReport.lines lists kinds by total time, then the slowest and heaviest edges | exact lines | small
cmake_driver: doxygen prints the install hint and returns 1 when doxygen is not on PATH | exact message and code | medium
cmake_cache: is_stale ignores case and separators, as Windows does | exact boolean on spellings | medium
config_base: load_tool_config keeps only the declared fields and coerces the bool keys | exact instance on a temp layered config | medium
aliases: deprecated announces the alias once and calls the callback unchanged | exact output and result | medium
diag: config_show lists the project root and each sibling directory | exact rows | medium
cli_console: LazyConsole.built is False until the console is first used | exact boolean | small
proc: run returns the child's own exit code | a real child process exits with a known code | medium
profile: env_tokens gives the common tokens then the module's own | value | small
stack_config: sibling_dir returns the configured path, else ../name beside the root | value | medium
module_config: load layers repo config, shared config, repo local config and environment in that order | contract on a real layered load | medium
theme: get_theme of an unknown name raises ConfigError naming the known themes | contract | small
typer_theme: every style the theme maps reaches Typer, not only three | attribute check per style | small
typer_help: no logo on a console whose encoding is not UTF | contract | small
typer_help: a stray close tag falls back to Typer's help without raising | contract | small
backlog.check: #6 a cited ID that names no open entry is a fault | contract | small
backlog.check: #8c a pin that is a decision, or more than ten pins, is a fault | contract | small
backlog.check: #12 the rows of a table are sorted by ID | contract | small
backlog.store: #9 an area file whose title or columns differ is a fault | contract | small
backlog.editor: #18 pin refuses an eleventh entry when the pins are full | contract | medium
backlog.editor: #19 unpin of an unpinned ID raises EntryNotFoundError | contract | medium
backlog.editor: #20 merge_areas refuses an area merged into itself | contract | medium
design.check: #10 a status line over 160 characters is a finding | contract | small
design.check: #11 a Phases table with other columns is a finding | contract | small
design.store: #7 set_phase_state refuses an unknown state or an unknown phase | contract | medium
design.merge: #5 merge refuses a loose topic that has no folder | contract | medium
design.model: #9 replace_field adds a missing metadata line under Status | contract | small
errors: PageError derives from DocsBundleError and SushiCoreError, so entry.run prints it | issubclass | small
page_text: is_page accepts .md in any case and refuses other suffixes | specified value | small
producer: a publish list without api = true ignores the API source and packs no api/ folder | exact archive listing | medium
main: without --root and --out the archive is written to <cwd>/build/docs/bundle | specified path | medium
pipeline: InstallPipeline re-prints each non-fatal warning of the context after the steps run (_report_warnings has no test) | recording console, one warning in ctx.warnings | small
checks: path_check passes when the path exists (only the FAIL side is tested) | contract on a fixture file | small
checks: stamp_check passes when every installed toolchain carries a stamp (only the WARN side is tested) | contract on a fixture tree | small
checks: fragment_check passes when every check_cmd exits zero (only failing commands are tested) | contract with an injected runner | small
registry: release of an unregistered component returns False | contract | small
probe: is_integrated_adapter reports an Intel Arc A-series line as discrete, not integrated | contract | small
system: ensure_intel_oneapi_repo in a dry run returns True and runs no command | contract | medium
sinks: render_local_config sorts the keys and writes forward slashes | contract | small
sushi_fetch: a dry run keeps an existing fetched folder | contract | medium
sushi_sources: a configured directory naming no folder falls through to the variable, then the sibling | contract | medium
CudaVendor.choose: returns the label of the release select_release picks, probing architectures through the installer | label written by hand, with an in-memory installer | small
RocmVendor.choose: returns the label of the newest tarball whose family covers every card | label written by hand, with an in-memory index | small
ToolkitChoiceFile.write: replaces the file in one step and leaves no .part file behind | directory listing after a write over an old file | medium
RocmVendor.find_system_toolkit: returns /opt/rocm only when hipcc or rocminfo is present and ROCm is installed there | ToolkitInstall or None over a per-test folder and patched PATH lookup | medium
CudaVendor.find_system_toolkit: the nvcc found on PATH names its toolkit root | root path written by hand | medium
CudaVendor.platform_key: arm64 Linux maps to linux-sbsa and x86_64 to linux-x86_64 | key string, host machine as an injected value | small
NvidiaHardware.describe and AmdHardware.describe: name each card and, for NVIDIA, the driver ceiling, as the console line | text written by hand | small
base: run() in dry-run mode prints the command, returns 0 and starts no process | stubbed Popen that fails when called | small
base: refresh_windows_path merges the machine and user Path values, first occurrence kept, case-insensitively | specified values | small (after the seam named for test_a_refused_registry_read_is_recorded_and_leaves_path_alone)
windows_installer: HttpDownloader.fetch reuses a copy whose MD5 matches and deletes one that does not | MD5 of known bytes via hashlib | medium
windows_installer: HttpDownloader.fetch returns None and warns when the download fails | the raised OSError | medium
windows_installer: RegistryMachineEnvironment.read returns None for an absent value | winreg stub that raises | small
windows_installer: adopt_machine_variable copies the machine value into os.environ and returns it, or None when unset | in-memory MachineEnvironment | medium
windows_installer: PowerShellElevatedRunner.run returns LAUNCH_FAILED with the OSError text when the process cannot start | subprocess.run stub that raises OSError | small
direct_download: DirectDownloadWindowsManager.install skips a tool already on PATH and warns on an unknown package ID | recorded console warning and skipped download | small
github_release: gh_latest_asset returns the first asset whose name matches the glob, and raises RuntimeError when none matches | urlopen stub returning release JSON | small
github_release: gh_latest_release_asset returns (tag, url) of the newest matching asset, prereleases included | urlopen stub returning release JSON | small
vcpkg: install of an empty list returns True without bootstrapping; install runs vcpkg install with port:triplet | recorded command | small
vcpkg: remove warns and returns True when the vcpkg executable is absent | recorded console warning | small
linux: DnfManager, YumManager, PacmanManager and ZypperManager install and remove run the native command, with sudo unless root | recorded command at the Popen boundary | small
winget: available is True when winget is on PATH | shutil.which stub returning a path | small
GitSourceInspector.files: lists the tracked and untracked files a git checkout does not ignore, and raises PackageError for a folder that is not a repository | real git in a temporary repository, and a plain folder | medium
probe_vcpkg_head: returns the HEAD commit of a vcpkg tree, or '' when git cannot say | real git in a temporary repository, and a folder with no repository | medium
probe_cmake_version: returns major.minor.patch from the version line, and raises PackageError when there is none | a version line printed by an executable the test writes | medium
run_process: raises PackageError naming the command when the command cannot start | an executable path that does not exist | medium
LinkPublisher.publish: raises PackageError naming the package when the link cannot be made | a link store whose point() raises OSError, from an in-memory adapter in stable_link.py | small
ForcedPackages.read: a lower-case variable name is read as its package variable | the variable in lower case with the nested marker, and a stored package | medium
sushicore_version: returns 'unknown' when the distribution metadata is absent | an injected metadata reader that raises PackageNotFoundError | small
StableLink.targets: counts only entries that carry the link mark | literal set beside an unmarked folder | medium
run_probe: raises PackageError when the command cannot start | pytest.raises PackageError with match | medium
has_sanitizer_runtime: true only when lib/clang/*/lib holds a clang_rt.asan library | literal bool on a temporary tree | medium
TomlDependencySource.all: skips a listed fragment file that does not exist | names of the other files' dependencies | medium
workspace.read_toml: [R2] a missing file reads as an empty table | contract | small
testing.budget: [B5] print_budget warns and leaves the run exit code unchanged when the reader fails | fake run returning 1 | small
ui.panel: [P5] the border is drawn in the theme panel border style | ANSI | small
ui.usage: [U2] the label is muted and the usage text takes the command style | ANSI | small
workspace.walk_up: [W1] walk_up returns the nearest ancestor of start, start included, that satisfies the predicate, or None | contract | small
workspace.load_layered: [W2] load_layered merges later paths over earlier ones, applies environment overrides last and coerces the bool keys | contract | small
LayeredPackage.grouped: a module of a grouped sub-package is keyed by the sub-package's name, so one layer covers all its modules | contract (docstring of LayeredPackage) | small
rule_unlayered_module: a package's own __init__.py is never reported as unlayered | contract (docstring of rule_unlayered_module) | small
rule_forbidden_import: a from-import of a forbidden package is reported, and a relative from-import is not | contract (docstring of rule_forbidden_import) | small
rule_ui_component: a component may import sushicore.brand, sushicore.markup and sushicore.ui.component | contract (K_COMPONENT_IMPORTS, docstring of rule_ui_component) | small
rule_ui_component: __init__.py and component.py are not checked as components | contract (K_COMPONENT_EXEMPT) | small
```
