# Documentation style guide

Prose in this repository follows the `humanizer` skill, in the language it is written in. Where
a document goes follows the `documentation` skill. Neither is restated here.

## Paths and citations

- A path is written relative to the repository root, in backticks: `sushicore/provision/home.py`.
  A link to another document is a Markdown link relative to the page that holds it.
- No absolute path from one machine, such as a drive letter or a home folder. This repository
  is public; such a path resolves in no clone and names its owner.
- A document of another repository is cited by naming the repository in the sentence, for
  example "SushiStack's `docs/design/REMAINING_WORK.md`". A bare path means a path here.
- An example path that need not exist is in a code block or in backticks, never a link.

## Names

- The product is SushiCore; the package and the distribution are `sushicore`.
- The CLIs are named by their command, in backticks: `hub`, `sr`, `se`, `sa`, `sb`, `sd`, `st`.
- A class, function, option or config key keeps the spelling the code uses, in backticks.

## Code samples

- A sample is code a reader can paste. It names real modules and real functions of this package.
- A TOML sample shows the default value of each key it lists, and the comment beside it lists
  the other values.
- A JSON event sample uses the keys `sushicore/events.py` and `sushicore/renderer.py` write.

## Module READMEs

`sushicore/provision`, `sushicore/ui` and `sushicore/help` each carry a `README.md` that says
what the module owns, what it depends on and its public entry points. A fact about one of them
is written there and linked from the manual, not repeated in it.

## Changelog

One line per change under `## Unreleased`:
`- <YYYY-MM-DD> — <scope>: <Past-tense verb> <what changed> (<where>).` The scope is the commit
scope, such as `provision`, `help`, `ui`, `config`, `workspace`, `proc`, `cli` or `docs`. At most
240 characters, at most five backticked places, one sentence, never the reason.

## Words

English, British spelling in prose ("licence" the noun, "colour", "organisation"). Identifiers
keep the spelling the code uses, such as `color` in the `[cli]` table and `license` in
`pyproject.toml`.
