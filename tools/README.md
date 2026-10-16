# tools

Reference implementations of the eight checkers every Sushi Systems repository carries. A rule is
fixed here first and copied out with `checking/copy_shared_tools.py`; which files that copies and
which it keeps is in the `project-tools` skill.

| Path | Checks | Takes |
| --- | --- | --- |
| `check_all.py` | Nothing itself; runs the eight checkers, then the repository's own `<area>/check_<what>.py` files and the tests, and prints only what failed | Repository root |
| `checking/checker.py` | Nothing itself; runs a checker's rule table and prints findings | |
| `checking/copy_shared_tools.py` | Nothing; copies these files into a repository, keeping its license blocks, `settings.py`, this README and its own tools, or lists the files that differ with `--report` | Repository root, `--from` |
| `settings.py` | Nothing; holds the settings that differ between repositories | |
| `checking/ignored_paths.py` | Nothing itself; names the files and folders git ignores, which no checker reads | |
| `documentation/check_source_comments.py` | C++, GLSL, TypeScript and Python: license block, file header, block ceiling, `//` and `#` runs, separators, history words, `@date` | Files or folders |
| `documentation/check_docs_layout.py` | `docs/` entries, required documents, document names, work folders, status lines, design ceiling, links under `docs/`, reachability from `docs/README.md`, READMEs under `modules/<tier>/`, archive candidates | Repository root |
| `documentation/check_changelog.py` | Headings and entry shape, releases kept live, length, one sentence, nesting, cited places | Repository root |
| `documentation/check_docs_truth.py` | The manual against the source: named symbols, cited paths, example sources, history words, page length, duplicated passages, em dashes, the allow-list | Repository root, `--source` |
| `layering/check_layering.py` | Declared tiers and domains, upward includes from a module or its tests, cross-domain and unlisted same-tier includes, reaches into another module's `source/`, dependencies the build file lists, internal headers in installed ones | Repository root |
| `layering/check_package_layers.py` | SushiCore's own: the layer tables of `docs_bundle` and `provision`, the imports they forbid, and the shape of every `ui` component | Repository root |
| `testing/check_test_mirror.py` | `tests/` mirrors the source: one `test_<name>` file per header or source file (`<name>.test.ts` in TypeScript), no test without a unit, no folder without a counterpart, no test that includes a header under `source/`; in a Unity repository, `Assets/<Product>/Tests/` with `<Name>Tests.cs` | Repository root |
| `testing/check_test_sizes.py` | Every C++, Python and TypeScript test names its size, `small`, `medium` or `large`, in its source | Repository root |
| `logs/check_logging.py` | Library code: log calls carry a category, a file declares the categories it uses, no foreign category, no console writes, no swallowed error, Python loggers named after their module | Repository root |
| `licensing/write_license_block.py` | Nothing; writes the license block of `source-comments` into every tracked source file, or lists the files that lack it with `--report` | Repository root, `--project` |
| `routing/summarize_dispatches.py` | Nothing; sums the dispatch lines of every `REPORT.md` per model and effort, for `model-routing` | Repository root |
| `tests/` | Unit tests for the checker rules; run `python -m unittest discover -s tools/tests` | |

`check_docs_layout.py` reads inline Markdown links, with or without a title, wrapped over a
line or in angle brackets. It does not read reference-style links or a link around an image.

`write_license_block.py` is the one tool here that writes files. It takes its licence lines
from `check_source_comments.py`, covers `.in` templates and `.inc` fragments by the file they become, `--closed` for a closed repository, `--skip GLOB` for generated
files and `--upstream PATH=LINE;LINE` for a ported file; a later run without it keeps those lines. A `--report` run that prints nothing
proves a repository's headers are in place.

`check_docs_truth.py` reads the root `README.md`, every document under `docs/` outside
`agent/`, `archive/` and the changelog, and every `README.md` under the source folders. It
looks each name up in one index of the words of those folders; `--source FOLDER`, repeatable,
replaces the default folders. A design document is exempt from the name, path and example
rules. A source example in a manual page is followed within three lines by
``Source: `<file>` `` or `Source: not compiled`, and `--report` ends with the count of the
second kind. `docs/.docs_truth_allow` holds one regular expression per line with ` # reason`
after it, for names and paths the source cannot hold.

Every checker takes `--report` and `--rule NAME`, exits 1 on findings, 0 when clean or
reporting, 2 on a bad path. Python 3.11, standard library only.

## Per-repository settings

`settings.py` holds them. `check_layering.py` does nothing until `K_TIER_ORDER` lists the
repository's tiers, lowest first. `K_DOMAIN_TIERS` names the tiers that share a rank and never
include each other. `K_MODULE_FUNCTION` names the CMake function that declares a module; when it
is set, the dependencies its `K_PUBLIC_DEPENDS` and `K_PRIVATE_DEPENDS` keywords list are checked
against the includes and are the allowed edges between modules of one tier, and a module marked
`K_INTERNAL_MARK` may not be included by an installed header. Without the function,
`K_SAME_TIER_EDGES` lists each `(includer, included)` pair of one tier. `K_CLOSED` makes
`check_source_comments.py` expect the closed licence lines. `check_docs_truth.py` takes a
repository's macro prefixes from the source unless `K_MACRO_PREFIXES` names them.

Every other `K_` constant sits at the top of its checker and is the same in every repository.
`K_LINE_CEILINGS` in `check_docs_truth.py` is compared by a test with the table in the
`documentation` skill.
