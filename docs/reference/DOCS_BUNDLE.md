# Documentation bundle

A documentation bundle is the archive a repository publishes to `docs.sushisystems.io`. The
site reads `bundle.json` and nothing else about a repository, so a repository may change its
`docs/` layout or its API generator and the site keeps working while the bundle keeps this
shape. The code is [`sushicore.docs_bundle`](../../sushicore/docs_bundle/README.md).

## The archive

`docs-bundle-<release>.tar.gz`, with `docs-bundle-<release>.tar.gz.sha256` beside it. The
second file holds the archive's SHA-256, two spaces and the archive's name.

```
bundle.json
pages/<section>/<FILE>.md        the published manual pages
pages/<section>/<asset>          a file a published page links to, such as an image
api/xml/index.xml                Doxygen's XML index; the folder is absent without an API
api/xml/<refid>.xml              one file per compound the index names
```

The member names are sorted, and every member has time 0, owner 0 and mode `0644`, so the same
files give the same bytes and the same SHA-256.

## `bundle.json`

```json
{
  "schema": 1,
  "repository": "sample",
  "title": "Sample",
  "summary": "A sample repository.",
  "version": "1.2.3",
  "commit": "c0ffee",
  "source_url": "https://github.com/SushiSystems/Sample",
  "pages": [
    {
      "path": "pages/guides/BUILDING.md",
      "section": "guides",
      "title": "Building",
      "order": 2,
      "source": "docs/guides/BUILDING.md"
    }
  ],
  "assets": ["pages/guides/images/shot.png"],
  "faq": "pages/guides/FAQ.md",
  "api": { "format": "doxygen-xml", "root": "api/xml" }
}
```

`tests/docs_bundle/test_bundle_manifest.py` pins this document, key order included.

| Field | Rule |
| --- | --- |
| `schema` | The integer `K_SCHEMA_VERSION`, 1. A reader refuses a number it does not know |
| `repository` | The `name` of the publish list: lower-case letters and digits. The first segment of the repository's routes on the site |
| `title`, `summary` | The publish list's `title` and `summary` |
| `version` | The release the bundle was built for, three integers |
| `commit` | The full hash of the commit the bundle was built from |
| `source_url` | The repository's address without a trailing slash, or `null` |
| `pages` | The published pages, ordered by section (`getting_started`, `guides`, `architecture`, `reference`) and then by `order` |
| `pages[].path` | The page's place in the archive |
| `pages[].section` | The folder under `docs/` the page lives in |
| `pages[].title` | The page's first level-one heading |
| `pages[].order` | The position of the page in a breadth-first walk of links that starts at `docs/README.md` and reads on through the manual's pages, counted from 1 |
| `pages[].source` | The page's path in the repository |
| `assets` | Every file under `pages/` that is not a page, sorted |
| `faq` | The archive path of `docs/guides/FAQ.md` when it is published, else `null` |
| `api` | The object above when the archive carries `api/xml`, else `null` |

### Links

A link between two published pages stays relative, as it is written in the repository. A link
whose target is not in `pages` or `assets` leaves the bundle. A reader resolves it against the
page's `source`: with a `source_url` it becomes `<source_url>/blob/<commit>/<path>`, and with
`null` it becomes its text without a link.

## `docs/publish.toml`

The repository says what leaves it.

```toml
name = "sushiruntime"
title = "SushiRuntime"
summary = "The task runtime the SushiStack applications schedule their work on."
sections = ["getting_started", "guides", "architecture", "reference"]
exclude = ["reference/KNOWN_ISSUES.md"]
api = true
source_url = "https://github.com/SushiSystems/SushiRuntime"
```

| Key | Type | Default | Rule |
| --- | --- | --- | --- |
| `name` | string | required | Lower-case letters and digits, starting with a letter |
| `title` | string | required | Not empty |
| `summary` | string | required | Not empty; one sentence |
| `sections` | list of strings | required | At least one of `getting_started`, `guides`, `architecture`, `reference`. No other folder of `docs/` can be published |
| `exclude` | list of strings | `[]` | Paths below `docs/`, spelt as on disk. Each must name a Markdown file of a listed section |
| `api` | boolean | `false` | `true` puts the API reference in the bundle |
| `source_url` | string | unset | Starts with `https://` |

A key outside this table stops the producer, so a misspelt key is not read as absent. An
`exclude` entry that names no page stops it too: a misspelt exclusion would publish the page it
meant to hide.

Every Markdown file under a listed section is published unless it is excluded. Each needs a
level-one heading, each is UTF-8 text, and each is reached from `docs/README.md`, directly or
through other manual pages, which is the rule `check_docs_layout.py` applies. A file whose suffix
is `.md` in any case is a page.

A link in a published page stops the producer, with the page's path and the line, when its
target does not exist, when it is an absolute path, when it leaves the repository, and when it
is written with a backslash.

## The commands

| Invocation | A CLI with an API reference | A CLI without one |
| --- | --- | --- |
| `<cli> docs` | Builds the reference and exits with the build's code | Prints the group's help and exits with code 2 |
| `<cli> docs bundle --release 1.2.3` | Writes the bundle, with `api/xml` when the publish list sets `api = true` | Writes the bundle; fails when the publish list sets `api = true` |
| `<cli> docs bundle` | Exit code 2: `--release` is required | The same |

`--out` names the folder the archive is written to. The default is `build/docs/bundle` under
the repository root. The command prints the archive's path with its page count, then
`sha256` and the digest. It stages the files in `.docs-bundle-staging` inside the output folder
and replaces that folder on every run.

A repository with no CLI runs `python -m sushicore.docs_bundle --release 1.2.3`, with `--root`
for another repository than the working directory and `--out` as above. It builds no API
reference.

`--describe` lists `docs` as a command for a CLI whose group runs bare, and `docs bundle` for
every CLI.

### Limits

- Inline Markdown links only. A reference-style link, `[text][label]`, and an HTML `<img>` are
  not followed, so their targets are neither checked nor carried.
- A link target that holds a parenthesis is cut at it.
- The same files give the same archive, but a checkout with CRLF line endings holds other files
  than one with LF. The bundle a site pins is the one CI attaches.
- `commit` is the checked-out commit. The producer does not look for uncommitted changes, so a
  bundle built from a tree with some carries pages that commit does not hold.
- The release is three integers; `v1.2.3` and `1.2.3-rc1` are refused.
- The files of the API reference are those `index.xml` names. A file an earlier Doxygen run
  left in the output folder is not copied.
