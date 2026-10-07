# Documentation bundle: report

**Status:** Built and reviewed on 2026-10-07. Nothing is pushed and no release was cut.

The plan's fifteen tasks ran inline, in order, on `main` of three repositories. One reviewer
read the whole change afterwards; its Critical and Important findings were fixed in one pass,
each behind a test that failed first.

## What was done

| Repository | Commits | Change |
| --- | --- | --- |
| SushiCore | `62af0f0` to the review fix | `sushicore/docs_bundle/` (13 modules), `_flatten` in `sushicore/describe.py`, `tests/docs_bundle/` (13 files), `docs/reference/DOCS_BUNDLE.md`, the sub-package README, and the manual pages the change made false |
| SushiSkills | `6609f08` | `publish.toml` in the `documentation` skill's tree and in `K_DOCS_ENTRIES`, with its test |
| SushiRuntime | `a373e8a`, `8e6b806` | `docs/publish.toml`, `GENERATE_XML = YES`, the layout checker's entry, `sr docs` as the group SushiCore registers, the CLI guide |

## Verification

SushiCore, after the review fixes:

```
$ python -m pytest tests -q
1053 passed in 7.82s
$ python tools/documentation/check_source_comments.py .
(no output)
$ python tools/documentation/check_changelog.py .
(no output)
$ python tools/documentation/check_docs_layout.py .
docs/agent/plans:1: rule_work_folders: docs/agent/ holds only YYYY_MM_DD_WORK_NAME folders
docs/agent/plans/2026-09-25-hub-root-migration.md:1: rule_document_names: document names are UPPER_SNAKE_CASE.md
```

The two layout lines concern an untracked folder that predates this work. The baseline run at
`433f4f0` gave `2 failed, 967 passed`, both failures in `tests/ui/test_table.py`; they failed
again in the run after task 10 and passed in the last run. This work does not touch that file,
so the two tests depend on something outside it. That is recorded here and not investigated.

SushiRuntime:

```
$ python -m pytest tests -q            (in cli/)
133 passed in 8.23s
$ sr docs bundle --release 1.0.0
[SUCCESS] D:\Projects\sushiruntime\build\docs\bundle\docs-bundle-1.0.0.tar.gz (8 pages)
[SUCCESS] sha256 4c431e9466c46f51f888ce3f6ee9555441ada039fd0c756197e0bcec85e7eab0
```

The archive holds `bundle.json` with the eleven keys of the contract, 8 pages, no asset, 96
files under `api/xml`, `faq` null, and no file from `design`, `agent`, `archive` or the three
excluded pages. A second run after the review fixes gave the same SHA-256.

The failure path, with a line `[gone](NOWHERE.md)` added to a page and removed afterwards:

```
$ python -m sushicore.docs_bundle --release 0.0.0 --out build/docs/bundle-probe
python -m sushicore.docs_bundle: D:\Projects\sushiruntime\docs\guides\INTEGRATION.md:234: links to NOWHERE.md, which does not exist
exit 1
```

`sr docs bundle --help` and `sr --describe` were run through the installed `sr`, which uses
Typer 0.27.2; the catalogue lists `docs` and `docs bundle`.

## Where the work left the plan

- **Click.** The plan's `commands.py` imported `click`. The installed CLIs run Typer 0.27.2,
  which ships no `click` package, so `sr` failed to start. The bare-`docs` callback now takes
  `typer.Context` through an explicit `__annotations__` assignment. The development interpreter
  has Typer 0.20 and Click, which is why the suite did not show it; a test now hides `click`.
- **The exclusion rule** compares against the pages found, not the disk, so a file system that
  ignores case cannot accept a misspelt exclusion.
- **The plan's test of `read_head_commit`** compared before it committed; it commits first.
- **SushiRuntime's `sr` test** also asserts `--release` in the usage error, since exit code 2
  alone was reached before the command existed.
- **SushiSkills' changelog** got a line the plan did not list.
- **SushiRuntime's `docs/reference/CHANGELOG.md`** held the owner's uncommitted line. The two
  lines of this work are in the working tree there and in no commit.
- **No worktree and no workspace folder**; the ledger was kept in the session's scratchpad.

## Review findings fixed

| Finding | Test that failed first |
| --- | --- |
| On Windows a link written with backslashes carried a file from an unlisted folder and wrote outside the staging folder | `test_collect_refuses_a_link_written_with_backslashes` (two cases) |
| An excluded page with the suffix `.MD` was carried as an asset when a page linked to it | `test_collect_never_carries_an_excluded_page_as_an_asset` |
| `[a](<b c.md> "t")` gave the target `b` | `test_iter_links_reads_a_bracketed_target_that_holds_a_space` |
| The outer target of a linked image was not read | `test_iter_links_reads_both_targets_of_a_linked_image` |
| A link whose text wraps over two lines was not read | `test_iter_links_reads_a_link_whose_text_wraps` |
| A `~~~` line inside a backtick fence hid every later link | `test_a_fence_closes_only_on_its_own_marker` |
| A page that is not UTF-8 raised a traceback that named no file; a byte order mark hid the title | `test_read_reports_a_page_that_is_not_utf_8`, `test_read_drops_a_byte_order_mark`, `test_collect_reports_a_page_that_is_not_utf_8` |
| A release with a trailing newline passed the check and failed on the file name | `test_produce_refuses_a_release_that_is_not_three_integers[1.2.3\n]` |

`page_text.py` is new: it owns the reading of a page and the rule for what a page is, which
two files each held before. The README, `DOCS_BUNDLE.md` and both specs were corrected where
the review found them saying something the code does not do.

## Not done

- **No release.** `sushicore.docs_bundle` is in no released SushiCore. SushiRuntime's
  `cli/pyproject.toml` still asks for `sushicore>=0.7.0`, and its `cli.py` now imports the new
  package: an `sr` installed against a released SushiCore fails on every command until the
  release exists and the floor rises. The local `sr` works because SushiCore is installed from
  the checkout.
- **Symbolic links.** A link inside a listed section that points into an unlisted folder would
  be followed. It could not be reproduced on this machine, which refuses to create one, so it
  has no test and no fix.
- **A dirty working tree.** The producer bundles the files on disk and records `HEAD`. The
  bundle built above therefore holds the owner's uncommitted changelog lines under a commit
  that lacks them. `DOCS_BUNDLE.md` states the limit; whether the producer should refuse is the
  owner's decision.
- **Doxygen's XML.** `XML_PROGRAMLISTING` is at its default, which embeds the source of every
  input header in the XML. That suits a source-available repository and has to be decided
  before sushiengine publishes an API, which it does not today. `reference/API_MAINPAGE.md` is
  excluded as a manual page and still reaches `api/xml` as Doxygen's main page.
- **Scanner limits kept:** reference-style links, HTML `<img>`, a parenthesis in a target,
  double-backtick spans and indented code blocks.
- **Deferred from the review, all graded minor:** `source_url = "https://"` is accepted; the
  message for a bad `name` omits the leading-letter rule; a listed section whose folder is
  missing is accepted silently; an `index.xml` that names no compound gives an empty reference;
  one asset linked in two spellings of case appears twice in `assets`; the archive is written
  in place, so a failure while packing leaves a truncated file; `commands.py` and `__main__.py`
  print the archive path in two forms; `build_manifest` takes `has_api` beside a publish list
  that already holds `api`; `PageCollector` is a class where its siblings are functions; the
  docstring of `register_docs_commands` runs past eight lines and some test docstrings do not
  open with a verb; a few agentless passives in docstrings.
- The other seven publishing repositories, the release step and the FAQ pages are sub-project 3.
