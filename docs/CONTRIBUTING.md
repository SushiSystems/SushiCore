# Contributing

SushiCore follows the Sushi Systems skills: `documentation`, `source-comments`,
`python-code-style`, `testing`, `commits`, `api-stability`, `versioning-and-release` and
`project-tools`. This page says what they mean here and does not restate them.

## How a change lands

1. Seven CLIs import this package. A public name that changes or goes away breaks them, so read
   `api-stability` first and say what breaks in the changelog entry.
2. Write the test with the change. `tests/` mirrors the package: `tests/provision/` covers
   `sushicore/provision/`, `tests/ui/` covers `sushicore/ui/`.
3. Update what the change made false, in the same commit: the module README, the manual page,
   the design document's status line and the backlog entry, through the `backlog` commands.
4. Add one line under `## Unreleased` in [the changelog](reference/CHANGELOG.md).
5. Run the checks below.

## What a change must carry

| The change | Carries |
| --- | --- |
| Adds, renames or removes a public name | A changelog entry that names it, and the row in [the architecture overview](architecture/OVERVIEW.md) |
| Touches `sushicore/provision`, `sushicore/ui` or `sushicore/help` | That module's `README.md` |
| Adds a `[cli]` key or an environment variable | [Configuration](reference/CONFIGURATION.md) |
| Adds or changes a JSON event | [JSON events](reference/JSON_EVENTS.md); the keys are a contract with the desktop application |
| Changes a field of `bundle.json` or a key of `docs/publish.toml` | [Documentation bundle](reference/DOCS_BUNDLE.md) and `K_SCHEMA_VERSION`; the documentation site reads both |
| Finishes a phase of a design | The status line of the document under `docs/design/` and the row in [the design map](design/README.md) |
| Fixes a recorded defect | Its entry closed with `python -m sushicore.backlog close <ID>`, in the same commit |
| Introduces a word a reader has to learn | [The glossary](reference/GLOSSARY.md) |

## Checks

```bash
python -m sushicore.tools check .
python -m pytest -q
python -m sushicore.tools.documentation.check_docs_layout .
python -m sushicore.tools.documentation.check_changelog .
python -m sushicore.tools.documentation.check_source_comments .
python -m pytest tests/tools
```

The pre-commit hook runs `check_all.py` with `--skip-history`, which leaves out the two checkers that
read every commit: a commit is not in the history yet, and the `commit-msg` hook judges its message
and its pages. CI runs them in full.

When every tracked file on disk matches the index, the hook checks the repository in place and
writes nothing. When one differs, the hook builds the commit's tree in a hidden folder beside the
repository, `.<name>-pre-commit-*`, and runs the checks there. The files that differ, and staged
files missing on disk, are written from the index. Every other tracked file and every ignored file
outside an ignored folder is copied from the disk. Submodules and ignored folders are folder links,
so `build/` costs nothing. The hook only reads the working tree, which keeps its content and its
modification times, and a commit needs no stash while other work stays unstaged. A copy, unlike a
hard link, can be removed while an editor holds its source open. The folder is removed afterwards. The next
commit removes a folder that an earlier one could not, but only a folder whose
`.sushicore-pre-commit` file names this repository.

`check_changelog.py`, `check_docs_layout.py` and `check_source_comments.py` print nothing when the
repository is clean, and a change adds no finding to them. A claim that a check passed carries the
command and its output.

Every test carries exactly one size: `small`, `medium` or `large`, set by a module-level
`pytestmark`. `tests/conftest.py` fails collection for a test without one and stops a test that
outlives its size's timeout of 1, 10 or 120 seconds. A stage runs a size with
`python -m pytest -m small`. A quarantined test also carries `quarantined`.

This repository has no CLI and nothing to compile. A change here is never proved by running a
sibling repository's build.

## Agent work

An agent's spec, plan and report go in one folder, `docs/agent/<YYYY_MM_DD>_<WORK_NAME>/`, as
`SPEC.md`, `PLAN.md` and `REPORT.md`. Finished work is deleted once its decisions are in the design; the version history
keeps it.

## Releases

The version is the `version` field of `pyproject.toml`. It changes in a commit of its own,
`chore(release): vX.Y.Z`, and that commit gets the annotated tag `vX.Y.Z`; pushing the tag
publishes to PyPI. At a release the `## Unreleased` section is renamed to the tag and its date,
and every older release section is deleted; the tag of its release holds it.

## Contributions from outside

Contributions from outside Sushi Systems are not accepted yet.
