# sushicore.docs_bundle

The archive a repository publishes to the documentation site, and the `docs` command group a
CLI registers to build it. The archive's layout and the two files it is driven by are in
[Documentation bundle](../../docs/reference/DOCS_BUNDLE.md).

## What it owns

| Name | File | Does |
| --- | --- | --- |
| `DocsBundleError`, `PublishListError`, `PageError`, `ApiReferenceError`, `ReleaseError` | `errors.py` | The failures the producer reports as one line |
| `iter_links`, `first_heading`, `local_path` | `markdown_scan.py` | Read what a Markdown page links to and what it is called |
| `read_page_text`, `is_page` | `page_text.py` | Read a page as UTF-8 text and say which file names are pages |
| `PublishList`, `read_publish_list` | `publish_list.py` | Read and validate `docs/publish.toml` |
| `read_page_order` | `page_order.py` | Give each page its position in a walk of links that starts at `docs/README.md` |
| `ApiSource`, `stage_api` | `api_reference.py` | Build the API reference and copy the XML files `index.xml` names |
| `write_archive` | `bundle_archive.py` | Pack a folder into a reproducible gzip tar and record its SHA-256 |
| `read_head_commit` | `source_revision.py` | Read the commit a bundle is built from |
| `Page`, `PageSet`, `PageCollector` | `page_set.py` | Collect the published pages and their assets, and check every link |
| `BundleIdentity`, `build_manifest` | `bundle_manifest.py` | Build the `bundle.json` document |
| `BundleRequest`, `BundleResult`, `BundleProducer` | `producer.py` | Stage the pages and the API, write the manifest, pack the archive |
| `register_docs_commands` | `commands.py` | Add the `docs` group to a Typer application |
| `main` | `__main__.py` | `python -m sushicore.docs_bundle`, for a repository with no CLI |

The package re-exports the errors, `ApiSource`, the three producer names,
`register_docs_commands`, `K_SCHEMA_VERSION` and `K_DEFAULT_OUTPUT`. Every other name is
private to it.

## What it depends on

`sushicore.errors` for the base error and `sushicore.workspace.read_toml` for the publish list.
Everything else is the standard library. `commands.py` imports Typer inside
`register_docs_commands`, so importing the package does not need it. It never imports Click:
Typer 0.27 carries its own, and the installed CLIs have no `click` package.

Inside the package a file imports only files in a lower layer. `tests/docs_bundle/test_layering.py`
holds the layer of each file and fails when a module-level import of a sibling points up or
sideways.

## Using it

A CLI replaces its own `docs` command with one call:

```python
from sushicore.docs_bundle import ApiSource, register_docs_commands

register_docs_commands(
    app,
    program="sr",
    panel="Project",
    project_root=find_project_root,
    api=lambda: ApiSource(
        build=project_svc.docs,
        xml_dir=find_project_root() / "build/docs/api-site/xml",
    ),
    report=lambda line: console.success(line),
    group_cls=_help_group,
)
```

`project_root` and `api` are called when a command runs, not when the CLI is imported, so
`--help` works outside a checkout. A CLI that builds no API reference leaves `api` out; its
`docs` group then holds `bundle` alone.

A `DocsBundleError` is not caught here. A CLI that runs through `sushicore.entry.run` prints it
as one line and exits with code 1.

A repository with no CLI runs the module:

```bash
python -m sushicore.docs_bundle --release 1.2.3
```

## Known limits

- Inline Markdown links only. A reference-style link, `[text][label]`, and an HTML `<img>` are
  not followed, so their targets are neither checked nor carried as assets.
- A link target that holds a parenthesis is cut at it.
- The release is three integers. A pre-release suffix is refused.
- The archive is the same bytes for the same files, but a checkout with CRLF line endings holds
  other files than one with LF. The bundle a site pins is the one CI attaches.
