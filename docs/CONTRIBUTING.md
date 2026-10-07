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
   the design document's status line and [Remaining work](design/REMAINING_WORK.md).
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
| Fixes a recorded defect | Its row removed from [Known issues](reference/KNOWN_ISSUES.md) |
| Introduces a word a reader has to learn | [The glossary](reference/GLOSSARY.md) |

## Checks

```bash
python -m pytest tests -q
python tools/documentation/check_docs_layout.py .
python tools/documentation/check_changelog.py .
python tools/documentation/check_source_comments.py .
python -m unittest discover -s tools/tests
```

`check_changelog.py` prints nothing. `check_docs_layout.py` prints only the entries recorded
under "Documentation and layout" in [Known issues](reference/KNOWN_ISSUES.md), and
`check_source_comments.py` only the findings counted in
[Remaining work](design/REMAINING_WORK.md). A change adds to neither. A claim that a check
passed carries the command and its output.

This repository has no CLI and nothing to compile. A change here is never proved by running a
sibling repository's build.

## Agent work

An agent's spec, plan and report go in one folder, `docs/agent/<YYYY_MM_DD>_<WORK_NAME>/`, as
`SPEC.md`, `PLAN.md` and `REPORT.md`. Finished work moves to `docs/archive/` keeping its path
below `docs/`, and is not edited there.

## Releases

The version is the `version` field of `pyproject.toml`. It changes in a commit of its own,
`chore(release): vX.Y.Z`, and that commit gets the annotated tag `vX.Y.Z`; pushing the tag
publishes to PyPI. At a release the `## Unreleased` section is renamed to the tag and its date,
and every older release section moves to `docs/archive/changelog/`.

## Contributions from outside

Contributions from outside Sushi Systems are not accepted yet.
