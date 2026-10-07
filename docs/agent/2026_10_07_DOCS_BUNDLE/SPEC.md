# Documentation bundle

**Status:** Open — built and reviewed 2026-10-07, see `REPORT.md`; the release that carries it is the owner's.

Sub-project 1 of the documentation site programme, whose design is
`docs/agent/2026_10_07_DOCS_SITE/SPEC.md` in the SushiStack repository. That document fixes the
bundle contract in its section 4 and the owner's decisions D1 to D10. This one fixes what
SushiCore adds and what SushiRuntime changes to prove it.

## 1. What is built

| Repository | Change |
| --- | --- |
| SushiCore | The sub-package `sushicore.docs_bundle`; a `--describe` catalogue that lists a group which runs bare; the reference page `docs/reference/DOCS_BUNDLE.md` |
| SushiSkills | `publish.toml` named in the `documentation` skill's tree and accepted by `check_docs_layout.py` |
| SushiRuntime | `docs/publish.toml`, `GENERATE_XML = YES`, the `docs` group registered from SushiCore, its copy of the layout checker |

The other seven publishing repositories are sub-project 3.

## 2. The sub-package

`sushicore/docs_bundle/`, one responsibility per file. Lower rows import nothing from higher
ones.

| Layer | File | Owns |
| --- | --- | --- |
| 0 | `errors.py` | `DocsBundleError` and the four failures derived from it |
| 0 | `markdown_scan.py` | `iter_links`, `first_heading`, `local_path`: what a Markdown file links to and what it is called |
| 1 | `page_text.py` | `read_page_text`, `is_page`: a page read as UTF-8, and which file names are pages |
| 1 | `publish_list.py` | `PublishList` and `read_publish_list`: `docs/publish.toml`, validated |
| 2 | `page_order.py` | `read_page_order`: a page's position among the links of `docs/README.md` |
| 1 | `api_reference.py` | `ApiSource` and `stage_api`: build the reference, copy the XML `index.xml` names |
| 1 | `bundle_archive.py` | `write_archive`: a reproducible gzip tar and its SHA-256 |
| 1 | `source_revision.py` | `read_head_commit` |
| 3 | `page_set.py` | `Page`, `PageSet`, `PageCollector`: the published pages, their assets, the link rule |
| 4 | `bundle_manifest.py` | `BundleIdentity` and `build_manifest`: the `bundle.json` document |
| 5 | `producer.py` | `BundleRequest`, `BundleResult`, `BundleProducer` |
| 6 | `commands.py` | `register_docs_commands` |
| 6 | `__main__.py` | `python -m sushicore.docs_bundle` |

## 3. Public interface

`sushicore/docs_bundle/__init__.py` re-exports these names and the four errors derived from
`DocsBundleError`: `PublishListError`, `PageError`, `ApiReferenceError`, `ReleaseError`.

```python
class DocsBundleError(SushiCoreError): ...

@dataclass(frozen=True, slots=True)
class ApiSource:
    build: Callable[[], int]      # builds the reference, returns an exit code
    xml_dir: Path                 # where the build leaves Doxygen's XML

@dataclass(frozen=True, slots=True)
class BundleRequest:
    repository_root: Path
    release: str                  # "1.2.3", without the v of the tag
    output_dir: Path
    api: ApiSource | None = None

@dataclass(frozen=True, slots=True)
class BundleResult:
    archive: Path
    sha256: str
    page_count: int

class BundleProducer:
    def __init__(self, read_commit: Callable[[Path], str] = read_head_commit) -> None: ...
    def produce(self, request: BundleRequest) -> BundleResult: ...

def register_docs_commands(
    app: typer.Typer,
    *,
    program: str,
    panel: str,
    project_root: Callable[[], Path],
    api: Callable[[], ApiSource] | None = None,
    report: Callable[[str], None] = print,
    group_cls: type | None = None,
) -> None: ...

K_SCHEMA_VERSION = 1
K_DEFAULT_OUTPUT = Path("build") / "docs" / "bundle"
```

`project_root` and `api` are callables because a CLI finds its project when a command runs, not
when it is imported; `--help` works outside a checkout.

## 4. Command behaviour

| Invocation | With `api` | Without `api` |
| --- | --- | --- |
| `<cli> docs` | Runs `api().build()` and exits with its code | Prints the group's help and exits with code 2, as Click does for a group given no command |
| `<cli> docs bundle --release 1.2.3` | Writes the bundle with `api/xml` when `publish.toml` sets `api = true` | Writes the bundle; fails when `publish.toml` sets `api = true` |
| `<cli> docs bundle` | Exit code 2, `--release` is required | The same |

The archive is `<out>/docs-bundle-<release>.tar.gz`, with `<name>.sha256` beside it; `--out`
defaults to `build/docs/bundle` under the project root. The command prints the archive's path
and its SHA-256 through `report`. A `DocsBundleError` is not caught: `sushicore.entry.run`
prints it as one line and exits with code 1.

## 5. The catalogue

`sushicore.describe._flatten` lists a group as a command of its own, beside its children, when
the group runs without a subcommand. `sr --describe` then holds `docs` and `docs bundle`; `hub`
and `st`, whose group shows help when bare, hold `docs bundle` alone. The shape of an entry does
not change, so `K_CONTRACT_VERSION` stays `"1"`.

## 6. Limits

- Inline Markdown links only. A reference-style link (`[text][label]`) and an HTML `<img>` are
  not followed, so their targets are not checked and not carried as assets.
- The release is three integers. A pre-release suffix is refused.
- A bundle built on Windows from a checkout with CRLF line endings has another SHA-256 than one
  built on Linux. The bundle a site pins is the one CI attaches.

## 7. Acceptance

`sr docs bundle --release <version>` in SushiRuntime writes an archive whose `bundle.json`
carries the fields `docs/reference/DOCS_BUNDLE.md` lists, and a published page that links to a
missing file makes the command exit non-zero with the page's path and line.
