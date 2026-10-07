# Documentation Bundle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `sr docs bundle --release X.Y.Z` writes the archive the documentation site compiles
from, produced by one implementation in SushiCore that every CLI registers.

**Architecture:** A sub-package `sushicore.docs_bundle` of twelve files in six layers. The
lower layers read (`publish.toml`, the index, Markdown links), the middle ones decide (which
pages, which assets, which links are errors), the top ones write (manifest, archive) and expose
one registration call and one `python -m` entry. SushiRuntime replaces its `docs` command with
that call.

**Tech Stack:** Python 3.10+, standard library only for the producer (`tarfile`, `gzip`,
`hashlib`, `xml.etree`, `tomllib` through `sushicore.workspace.read_toml`), Typer for the
command, pytest.

**Spec:** `docs/agent/2026_10_07_DOCS_BUNDLE/SPEC.md` here, and
`docs/agent/2026_10_07_DOCS_SITE/SPEC.md` in the SushiStack repository for the contract.

## Global Constraints

- Python `>=3.10`; no new dependency in `pyproject.toml`.
- No module of `sushicore.docs_bundle` imports `typer` or `click` at module level;
  `import sushicore` works without the `typer` extra.
- Every file opens with the five `#` licence lines and a module docstring of at most six lines;
  every function, class and test carries a one-sentence docstring that starts with its verb.
- Line length 100, double quotes, trailing commas on multi-line calls, constants `K_UPPER_SNAKE`.
- Errors derive from `DocsBundleError`, which derives from `sushicore.errors.SushiCoreError`.
- `bundle.json` field names and the archive layout are those of section 4 of the SushiStack
  spec, verbatim: `schema`, `repository`, `title`, `summary`, `version`, `commit`,
  `source_url`, `pages`, `assets`, `faq`, `api`; `pages/`, `api/xml/`.
- `sections` accepts `getting_started`, `guides`, `architecture`, `reference` and nothing else.
- The archive name is `docs-bundle-<release>.tar.gz`; the default output is `build/docs/bundle`.
- Never run `se`, `cmake`, `ninja` or `ctest`. `python -m pytest` and the checkers under
  `tools/` are the verification.
- Stage by path; no `git add -A`, no `git stash`, no branch switch in a shared tree.
- Three repositories are touched: SushiCore (tasks 1 to 11), SushiSkills (task 12),
  SushiRuntime (tasks 13 to 15). A command's working directory is the repository its task names.

## Review Focus

1. A link target written with a title or angle brackets, `[a](<b c.md> "t")`: the target is
   still found. Pinned in task 1.
2. A link inside a fenced block or a code span: not a link, so an example path never stops the
   producer. Pinned in task 1.
3. An `exclude` entry that names no file: the producer stops, since a misspelt exclusion
   publishes the page it meant to hide. Pinned in task 4.
4. A Doxygen XML file left by an earlier run and no longer named in `index.xml`: not copied.
   Pinned in task 6.
5. A page linked twice in `docs/README.md`, or linked with a fragment: it keeps its first
   position. Pinned in task 3.

## File Structure

```
sushicore/docs_bundle/
    __init__.py            the public surface of SPEC.md section 3
    __main__.py            python -m sushicore.docs_bundle
    README.md
    errors.py
    markdown_scan.py
    publish_list.py
    page_order.py
    page_set.py
    bundle_manifest.py
    api_reference.py
    bundle_archive.py
    source_revision.py
    producer.py
    commands.py
tests/docs_bundle/
    __init__.py
    sample_repository.py   builds the tree every test reads
    conftest.py
    test_markdown_scan.py  test_publish_list.py  test_page_order.py  test_page_set.py
    test_bundle_manifest.py  test_api_reference.py  test_bundle_archive.py
    test_producer.py  test_commands.py  test_main.py  test_layering.py
```

The licence header of every new SushiCore file is these five lines with the file's own name on
the first:

```python
# <file name>
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
```

The code blocks below start at the module docstring; put the header above each.

---

### Task 1: Errors and the Markdown scan

**Files:**
- Create: `sushicore/docs_bundle/__init__.py`, `sushicore/docs_bundle/errors.py`,
  `sushicore/docs_bundle/markdown_scan.py`
- Create: `tests/docs_bundle/__init__.py`, `tests/docs_bundle/test_markdown_scan.py`

**Interfaces:**
- Consumes: `sushicore.errors.SushiCoreError`.
- Produces: `DocsBundleError`, `PublishListError`, `PageError(path, line, message)`,
  `ApiReferenceError`, `ReleaseError`; `MarkdownLink(target: str, line: int)`,
  `iter_links(text: str) -> Iterator[MarkdownLink]`, `first_heading(text: str) -> str | None`,
  `local_path(target: str) -> str | None`.

- [ ] **Step 1: Write the failing test**

`tests/docs_bundle/__init__.py`:

```python
"""Marks the documentation bundle tests as an importable package."""
```

`tests/docs_bundle/test_markdown_scan.py`:

```python
"""Tests what the Markdown scan reads out of a page: its links and its title."""

from __future__ import annotations

from sushicore.docs_bundle.markdown_scan import (
    MarkdownLink,
    first_heading,
    iter_links,
    local_path,
)


def test_iter_links_reports_each_target_with_its_line():
    """Reads inline links and images, with the line each stands on."""
    text = "# T\n\nSee [a](one.md) and ![b](two.png).\n[c](three.md#part)\n"
    assert list(iter_links(text)) == [
        MarkdownLink("one.md", 3),
        MarkdownLink("two.png", 3),
        MarkdownLink("three.md#part", 4),
    ]


def test_iter_links_reads_titled_and_bracketed_targets():
    """Finds the target when a title follows it or angle brackets wrap it."""
    text = '[a](one.md "The title")\n[b](<two.md>)\n[`c`](three.md)\n'
    assert [link.target for link in iter_links(text)] == ["one.md", "two.md", "three.md"]


def test_iter_links_skips_code():
    """Ignores a link written inside a fenced block or a code span."""
    text = "```\n[a](fenced.md)\n```\nUse `[b](span.md)` here.\n~~~\n[c](tilde.md)\n~~~\n"
    assert list(iter_links(text)) == []


def test_first_heading_returns_the_first_level_one_heading():
    """Returns the first `# ` heading and skips one inside a fenced block."""
    assert first_heading("```\n# not this\n```\n\n## Nor this\n\n# The title #\n") == "The title"
    assert first_heading("## Only a second level\n") is None


def test_local_path_drops_the_fragment_and_refuses_addresses():
    """Returns the file part of a target and None for an address or a bare anchor."""
    assert local_path("guides/A%20B.md#part") == "guides/A B.md"
    assert local_path("page.md?raw=1") == "page.md"
    assert local_path("https://sushisystems.io") is None
    assert local_path("mailto:a@b.io") is None
    assert local_path("#part") is None
    assert local_path("//cdn.example/x.png") is None
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/docs_bundle/test_markdown_scan.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'sushicore.docs_bundle'`.

- [ ] **Step 3: Write the implementation**

`sushicore/docs_bundle/__init__.py` (task 10 adds the re-exports):

```python
"""The documentation bundle: what a repository publishes to docs.sushisystems.io."""

from __future__ import annotations
```

`sushicore/docs_bundle/errors.py`:

```python
"""The failures the documentation bundle producer reports as one line."""

from __future__ import annotations

from pathlib import Path

from ..errors import SushiCoreError


class DocsBundleError(SushiCoreError):
    """Reports a documentation tree that cannot be bundled."""


class PublishListError(DocsBundleError):
    """Reports a `docs/publish.toml` that is missing or cannot be used."""


class PageError(DocsBundleError):
    """Reports a published page that breaks a rule, with its file and line."""

    def __init__(self, path: Path, line: int, message: str) -> None:
        """Stores the location and puts it in front of the message."""
        super().__init__(f"{path}:{line}: {message}")
        self.path = path
        self.line = line


class ApiReferenceError(DocsBundleError):
    """Reports an API reference that could not be built or found."""


class ReleaseError(DocsBundleError):
    """Reports a release or a commit the bundle cannot be named after."""
```

`sushicore/docs_bundle/markdown_scan.py`:

```python
"""Reads what a Markdown page links to and what it is called.

Inline links only; `SPEC.md` section 6 of this work records the limit.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from urllib.parse import unquote

K_FENCE = re.compile(r"^\s{0,3}(```|~~~)")
K_CODE_SPAN = re.compile(r"`[^`]*`")
K_LINK = re.compile(r"\[[^\]]*\]\(\s*<?([^)\s>]+)>?[^)]*\)")
K_HEADING = re.compile(r"^#\s+(.*?)\s*#*\s*$")
K_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


@dataclass(frozen=True, slots=True)
class MarkdownLink:
    """Holds one link target and the line it stands on."""

    target: str
    line: int


def _prose_lines(text: str) -> Iterator[tuple[int, str]]:
    """Yields each line outside a fenced code block, with its number."""
    fenced = False
    for number, line in enumerate(text.splitlines(), start=1):
        if K_FENCE.match(line):
            fenced = not fenced
            continue
        if not fenced:
            yield number, line


def iter_links(text: str) -> Iterator[MarkdownLink]:
    """Yields every inline link and image target outside code, in reading order."""
    for number, line in _prose_lines(text):
        for match in K_LINK.finditer(K_CODE_SPAN.sub("", line)):
            yield MarkdownLink(match.group(1), number)


def first_heading(text: str) -> str | None:
    """Returns the text of the first level-one heading, or None when there is none."""
    for _, line in _prose_lines(text):
        match = K_HEADING.match(line)
        if match and match.group(1):
            return match.group(1)
    return None


def local_path(target: str) -> str | None:
    """Returns the file part of a link target, or None when it names no local file."""
    if K_SCHEME.match(target) or target.startswith(("#", "//")):
        return None
    path = unquote(target.split("#", 1)[0].split("?", 1)[0])
    return path or None
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest tests/docs_bundle/test_markdown_scan.py -q`
Expected: `5 passed`.

- [ ] **Step 5: Commit**

```bash
git add sushicore/docs_bundle/__init__.py sushicore/docs_bundle/errors.py sushicore/docs_bundle/markdown_scan.py tests/docs_bundle/__init__.py tests/docs_bundle/test_markdown_scan.py
git commit -m "feat(docs-bundle): add the errors and the Markdown scan"
```

---

### Task 2: The publish list

**Files:**
- Create: `sushicore/docs_bundle/publish_list.py`
- Create: `tests/docs_bundle/sample_repository.py`, `tests/docs_bundle/conftest.py`,
  `tests/docs_bundle/test_publish_list.py`

**Interfaces:**
- Consumes: `PublishListError`; `sushicore.workspace.read_toml(path) -> dict`.
- Produces: `K_FILE_NAME = "publish.toml"`, `K_SECTIONS`, `PublishList(name, title, summary,
  sections: tuple[str, ...], exclude: frozenset[str], api: bool, source_url: str | None)`,
  `read_publish_list(docs_dir: Path) -> PublishList`. Test helpers `write_file(root, relative,
  text)`, `build_sample(root)` and the fixture `repository`.

- [ ] **Step 1: Write the sample tree and the failing test**

`tests/docs_bundle/sample_repository.py`:

```python
"""Builds the small repository the documentation bundle tests read."""

from __future__ import annotations

from pathlib import Path

K_PUBLISH = """name = "sample"
title = "Sample"
summary = "A sample repository."
sections = ["architecture", "guides"]
source_url = "https://github.com/SushiSystems/Sample/"
"""

K_FILES = {
    "README.md": "# Sample\n",
    "docs/publish.toml": K_PUBLISH,
    "docs/README.md": (
        "# Manual\n\n"
        "- [Overview](architecture/OVERVIEW.md)\n"
        "- [Building](guides/BUILDING.md)\n"
        "- [FAQ](guides/FAQ.md)\n"
        "- [Secret](design/SECRET.md)\n"
    ),
    "docs/architecture/OVERVIEW.md": (
        "# Overview\n\nThe design is in [the secret](../design/SECRET.md).\n"
    ),
    "docs/guides/BUILDING.md": (
        "# Building\n\n"
        "Read [the overview](../architecture/OVERVIEW.md#layers) and [the root](../../README.md).\n\n"
        "![A shot](images/shot.png)\n"
    ),
    "docs/guides/FAQ.md": "# FAQ\n\n## Does it build?\n\nYes.\n",
    "docs/design/SECRET.md": "# Secret\n",
}
K_SHOT = b"\x89PNG\r\n\x1a\n"


def write_file(root: Path, relative: str, text: str) -> Path:
    """Writes one file below *root*, creating its folders, and returns its path."""
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def build_sample(root: Path) -> Path:
    """Writes the sample repository below *root* and returns *root*."""
    for relative, text in K_FILES.items():
        write_file(root, relative, text)
    (root / "docs" / "guides" / "images").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "guides" / "images" / "shot.png").write_bytes(K_SHOT)
    return root


def run_git(root: Path, *arguments: str) -> str:
    """Runs git in *root* with a fixed identity and no signing, and returns its output."""
    command = [
        "git", "-c", "user.name=t", "-c", "user.email=t@t.io", "-c", "commit.gpgsign=false",
        *arguments,
    ]
    done = subprocess.run(command, cwd=root, check=True, capture_output=True, text=True)
    return done.stdout.strip()


def commit_all(root: Path) -> str:
    """Makes *root* a git repository holding one commit of its files and returns the hash."""
    run_git(root, "init", "-q")
    run_git(root, "add", "-A")
    run_git(root, "commit", "-q", "-m", "sample")
    return run_git(root, "rev-parse", "HEAD")
```

Add `import subprocess` to the imports of this file, above `from pathlib import Path`.

`tests/docs_bundle/conftest.py`:

```python
"""Fixtures shared by the documentation bundle tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from .sample_repository import build_sample, commit_all


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    """Returns the root of a freshly written sample repository."""
    return build_sample(tmp_path / "sample")


@pytest.fixture
def checkout(repository: Path) -> Path:
    """Returns the sample repository as a git checkout with one commit."""
    commit_all(repository)
    return repository
```

`tests/docs_bundle/test_publish_list.py`:

```python
"""Tests the reader of `docs/publish.toml` and every rule it enforces."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.docs_bundle.errors import PublishListError
from sushicore.docs_bundle.publish_list import PublishList, read_publish_list
from sushicore.errors import ConfigError

from .sample_repository import write_file

K_MINIMAL = 'name = "sample"\ntitle = "Sample"\nsummary = "S."\nsections = ["guides"]\n'


def _read(repository: Path, text: str) -> PublishList:
    """Replaces the sample's publish list with *text* and reads it."""
    write_file(repository, "docs/publish.toml", text)
    return read_publish_list(repository / "docs")


def test_read_returns_every_field(repository):
    """Reads the sample file, orders the sections and trims the address."""
    assert read_publish_list(repository / "docs") == PublishList(
        name="sample",
        title="Sample",
        summary="A sample repository.",
        sections=("guides", "architecture"),
        exclude=frozenset(),
        api=False,
        source_url="https://github.com/SushiSystems/Sample",
    )


def test_read_applies_the_defaults(repository):
    """Leaves exclude empty, api off and the address unset when the file omits them."""
    publish_list = _read(repository, K_MINIMAL)
    assert publish_list.exclude == frozenset()
    assert publish_list.api is False
    assert publish_list.source_url is None


def test_read_takes_exclude_and_api(repository):
    """Reads the exclusions as a set and the api flag as written."""
    publish_list = _read(repository, K_MINIMAL + 'exclude = ["guides/FAQ.md"]\napi = true\n')
    assert publish_list.exclude == frozenset({"guides/FAQ.md"})
    assert publish_list.api is True


def test_read_reports_a_missing_file(tmp_path):
    """Names the path when a repository has no publish list."""
    with pytest.raises(PublishListError) as caught:
        read_publish_list(tmp_path / "docs")
    assert "publish.toml" in str(caught.value)


@pytest.mark.parametrize("section", ["design", "agent", "archive", "Guides"])
def test_read_refuses_a_section_that_cannot_be_published(repository, section):
    """Refuses every section outside the four manual folders."""
    with pytest.raises(PublishListError) as caught:
        _read(repository, K_MINIMAL.replace('"guides"', f'"{section}"'))
    assert section in str(caught.value)


@pytest.mark.parametrize(
    "text",
    [
        K_MINIMAL.replace('name = "sample"\n', ""),
        K_MINIMAL.replace('"sample"', '"Sample Repo"'),
        K_MINIMAL.replace('"S."', '""'),
        K_MINIMAL.replace('["guides"]', "[]"),
        K_MINIMAL.replace('["guides"]', '"guides"'),
        K_MINIMAL + 'api = "yes"\n',
        K_MINIMAL + 'exclude = [1]\n',
        K_MINIMAL + 'source_url = "http://example.org"\n',
        K_MINIMAL + 'sectons = ["guides"]\n',
    ],
)
def test_read_refuses_a_wrong_value(repository, text):
    """Refuses a missing name, a bad name, an empty text, a wrong type and an unknown key."""
    with pytest.raises(PublishListError):
        _read(repository, text)


def test_read_reports_malformed_toml_as_a_config_error(repository):
    """Leaves a file that is not TOML to the shared reader's own error."""
    with pytest.raises(ConfigError):
        _read(repository, "name = ")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/docs_bundle/test_publish_list.py -q`
Expected: collection error, `No module named 'sushicore.docs_bundle.publish_list'`.

- [ ] **Step 3: Write the implementation**

`sushicore/docs_bundle/publish_list.py`:

```python
"""Reads `docs/publish.toml`, the list of what a repository publishes."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ..workspace import read_toml
from .errors import PublishListError

K_FILE_NAME = "publish.toml"
K_SECTIONS: tuple[str, ...] = ("getting_started", "guides", "architecture", "reference")
K_KEYS = frozenset({"name", "title", "summary", "sections", "exclude", "api", "source_url"})
K_NAME = re.compile(r"^[a-z][a-z0-9]*$")
K_ADDRESS_PREFIX = "https://"


@dataclass(frozen=True, slots=True)
class PublishList:
    """Holds what one repository publishes and how the site names it."""

    name: str
    title: str
    summary: str
    sections: tuple[str, ...]
    exclude: frozenset[str]
    api: bool
    source_url: str | None


def _text(path: Path, document: dict, key: str) -> str:
    """Returns a required key's value, which must be a string that is not empty."""
    value = document.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PublishListError(f"{path}: {key} must be a string that is not empty.")
    return value.strip()


def _names(path: Path, document: dict, key: str) -> tuple[str, ...]:
    """Returns an optional key's value, which must be a list of strings."""
    value = document.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise PublishListError(f"{path}: {key} must be a list of strings.")
    return tuple(value)


def _sections(path: Path, document: dict) -> tuple[str, ...]:
    """Returns the published sections in manual order, refusing any other folder."""
    listed = _names(path, document, "sections")
    if not listed:
        raise PublishListError(f"{path}: sections must name at least one section.")
    for section in listed:
        if section not in K_SECTIONS:
            raise PublishListError(
                f"{path}: section {section!r} cannot be published; "
                f"the sections are {', '.join(K_SECTIONS)}."
            )
    return tuple(section for section in K_SECTIONS if section in listed)


def _source_url(path: Path, document: dict) -> str | None:
    """Returns the repository's address without a trailing slash, or None when unset."""
    if "source_url" not in document:
        return None
    value = _text(path, document, "source_url")
    if not value.startswith(K_ADDRESS_PREFIX):
        raise PublishListError(f"{path}: source_url must start with {K_ADDRESS_PREFIX}.")
    return value.rstrip("/")


def read_publish_list(docs_dir: Path) -> PublishList:
    """Reads and validates the publish list of the documentation tree at *docs_dir*.

    Raises:
        PublishListError: The file is missing, or a key is unknown or holds a wrong value.
    """
    path = docs_dir / K_FILE_NAME
    if not path.is_file():
        raise PublishListError(
            f"{path} does not exist; a repository lists what it publishes there."
        )
    document = read_toml(path)
    unknown = sorted(set(document) - K_KEYS)
    if unknown:
        raise PublishListError(
            f"{path}: unknown key {unknown[0]!r}; the keys are {', '.join(sorted(K_KEYS))}."
        )
    name = _text(path, document, "name")
    if not K_NAME.match(name):
        raise PublishListError(f"{path}: name must be lower-case letters and digits.")
    api = document.get("api", False)
    if not isinstance(api, bool):
        raise PublishListError(f"{path}: api must be true or false.")
    return PublishList(
        name=name,
        title=_text(path, document, "title"),
        summary=_text(path, document, "summary"),
        sections=_sections(path, document),
        exclude=frozenset(_names(path, document, "exclude")),
        api=api,
        source_url=_source_url(path, document),
    )
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest tests/docs_bundle/test_publish_list.py -q`
Expected: `18 passed`.

- [ ] **Step 5: Commit**

```bash
git add sushicore/docs_bundle/publish_list.py tests/docs_bundle/sample_repository.py tests/docs_bundle/conftest.py tests/docs_bundle/test_publish_list.py
git commit -m "feat(docs-bundle): read and validate docs/publish.toml"
```

---

### Task 3: The page order

**Files:**
- Create: `sushicore/docs_bundle/page_order.py`
- Test: `tests/docs_bundle/test_page_order.py`

**Interfaces:**
- Consumes: `iter_links`, `local_path`, `PageError`.
- Produces: `K_INDEX_NAME = "README.md"`, `read_page_order(docs_dir: Path) -> dict[str, int]`:
  the path below `docs/` of each Markdown file the index links to, mapped to its position
  starting at 1.

- [ ] **Step 1: Write the failing test**

`tests/docs_bundle/test_page_order.py`:

```python
"""Tests the order a page takes from the links of `docs/README.md`."""

from __future__ import annotations

import pytest

from sushicore.docs_bundle.errors import PageError
from sushicore.docs_bundle.page_order import read_page_order

from .sample_repository import write_file


def test_read_numbers_the_pages_in_link_order(repository):
    """Numbers each linked page from 1 in the order the index links to it."""
    assert read_page_order(repository / "docs") == {
        "architecture/OVERVIEW.md": 1,
        "guides/BUILDING.md": 2,
        "guides/FAQ.md": 3,
        "design/SECRET.md": 4,
    }


def test_read_keeps_the_first_position_of_a_repeated_page(repository):
    """Keeps a page's first position when it is linked again or with a fragment."""
    write_file(
        repository,
        "docs/README.md",
        "[A](guides/A.md)\n[B](guides/B.md#part)\n[A again](./guides/A.md)\n[C](guides/C.md)\n",
    )
    assert read_page_order(repository / "docs") == {
        "guides/A.md": 1,
        "guides/B.md": 2,
        "guides/C.md": 3,
    }


def test_read_skips_what_is_not_a_page_below_docs(repository):
    """Skips an address, a file outside docs/ and a file that is not Markdown."""
    write_file(
        repository,
        "docs/README.md",
        "[site](https://sushisystems.io)\n[root](../README.md)\n"
        "[shot](guides/images/shot.png)\n[A](guides/A.md)\n",
    )
    assert read_page_order(repository / "docs") == {"guides/A.md": 1}


def test_read_reports_a_missing_index(tmp_path):
    """Names the index when the documentation tree has none."""
    with pytest.raises(PageError) as caught:
        read_page_order(tmp_path)
    assert "README.md" in str(caught.value)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/docs_bundle/test_page_order.py -q`
Expected: collection error, `No module named 'sushicore.docs_bundle.page_order'`.

- [ ] **Step 3: Write the implementation**

`sushicore/docs_bundle/page_order.py`:

```python
"""Reads the order of the manual's pages from the links of `docs/README.md`."""

from __future__ import annotations

import posixpath
from pathlib import Path

from .errors import PageError
from .markdown_scan import iter_links, local_path

K_INDEX_NAME = "README.md"
K_PAGE_SUFFIX = ".md"


def read_page_order(docs_dir: Path) -> dict[str, int]:
    """Returns each page the index links to, keyed by its path below docs/, with its position.

    Raises:
        PageError: The documentation tree has no index.
    """
    index = docs_dir / K_INDEX_NAME
    if not index.is_file():
        raise PageError(index, 1, "does not exist; the pages take their order from it")
    order: dict[str, int] = {}
    for link in iter_links(index.read_text(encoding="utf-8")):
        path = local_path(link.target)
        if path is None:
            continue
        page = posixpath.normpath(path)
        if page.startswith("..") or not page.endswith(K_PAGE_SUFFIX):
            continue
        order.setdefault(page, len(order) + 1)
    return order
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest tests/docs_bundle/test_page_order.py -q`
Expected: `4 passed`.

- [ ] **Step 5: Commit**

```bash
git add sushicore/docs_bundle/page_order.py tests/docs_bundle/test_page_order.py
git commit -m "feat(docs-bundle): take the page order from the manual index"
```

---

### Task 4: The page set

**Files:**
- Create: `sushicore/docs_bundle/page_set.py`
- Test: `tests/docs_bundle/test_page_set.py`

**Interfaces:**
- Consumes: `PublishList`, `K_FILE_NAME`, `K_SECTIONS`, `read_page_order`, `K_INDEX_NAME`,
  `iter_links`, `first_heading`, `local_path`, `MarkdownLink`, `PageError`, `PublishListError`.
- Produces: `K_DOCS = "docs"`, `Page(source: str, section: str, title: str, order: int)` where
  `source` is the path below `docs/`; `PageSet(pages: tuple[Page, ...], assets: tuple[str, ...],
  faq: str | None)`; `PageCollector(repository_root: Path, publish_list: PublishList)` with
  `collect() -> PageSet`.

- [ ] **Step 1: Write the failing test**

`tests/docs_bundle/test_page_set.py`:

```python
"""Tests which pages and assets a repository publishes, and which links stop the producer."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from sushicore.docs_bundle.errors import PageError, PublishListError
from sushicore.docs_bundle.page_set import Page, PageCollector, PageSet
from sushicore.docs_bundle.publish_list import read_publish_list

from .sample_repository import write_file


def _collect(repository: Path, **changes) -> PageSet:
    """Collects the sample's pages, with *changes* applied to its publish list."""
    publish_list = replace(read_publish_list(repository / "docs"), **changes)
    return PageCollector(repository, publish_list).collect()


def test_collect_returns_the_pages_in_section_then_index_order(repository):
    """Orders pages by section, then by their position in the index."""
    assert _collect(repository) == PageSet(
        pages=(
            Page("guides/BUILDING.md", "guides", "Building", 2),
            Page("guides/FAQ.md", "guides", "FAQ", 3),
            Page("architecture/OVERVIEW.md", "architecture", "Overview", 1),
        ),
        assets=("guides/images/shot.png",),
        faq="guides/FAQ.md",
    )


def test_collect_leaves_out_an_excluded_page(repository):
    """Publishes neither an excluded page nor an FAQ that was excluded."""
    page_set = _collect(repository, exclude=frozenset({"guides/FAQ.md"}))
    assert [page.source for page in page_set.pages] == [
        "guides/BUILDING.md",
        "architecture/OVERVIEW.md",
    ]
    assert page_set.faq is None


def test_collect_refuses_an_exclusion_that_names_no_file(repository):
    """Stops on a misspelt exclusion, which would publish the page it meant to hide."""
    with pytest.raises(PublishListError) as caught:
        _collect(repository, exclude=frozenset({"guides/FAQ.MD.md"}))
    assert "guides/FAQ.MD.md" in str(caught.value)


def test_collect_accepts_a_link_that_leaves_the_bundle(repository):
    """Accepts links to a design document and to the root README, and carries neither."""
    page_set = _collect(repository)
    assert all("SECRET" not in page.source for page in page_set.pages)
    assert all("README" not in asset for asset in page_set.assets)


def test_collect_reports_a_link_to_a_missing_file(repository):
    """Names the page and the line of a link whose target does not exist."""
    page = write_file(repository, "docs/guides/BUILDING.md", "# Building\n\n\n[gone](NOWHERE.md)\n")
    with pytest.raises(PageError) as caught:
        _collect(repository)
    assert caught.value.path == page
    assert caught.value.line == 4
    assert "NOWHERE.md" in str(caught.value)


@pytest.mark.parametrize("target", ["/etc/hosts", "../../../outside.md"])
def test_collect_reports_a_link_that_cannot_be_resolved(repository, target):
    """Refuses an absolute path and a path that leaves the repository."""
    write_file(repository, "docs/guides/BUILDING.md", f"# Building\n\n[x]({target})\n")
    with pytest.raises(PageError) as caught:
        _collect(repository)
    assert caught.value.line == 3


def test_collect_reports_a_page_without_a_title(repository):
    """Names a page that has no level-one heading."""
    page = write_file(repository, "docs/guides/BUILDING.md", "## Building\n")
    with pytest.raises(PageError) as caught:
        _collect(repository)
    assert caught.value.path == page


def test_collect_reports_a_page_the_index_does_not_link(repository):
    """Names the index and the page when a published page has no order."""
    write_file(repository, "docs/guides/ORPHAN.md", "# Orphan\n")
    with pytest.raises(PageError) as caught:
        _collect(repository)
    assert caught.value.path == repository / "docs" / "README.md"
    assert "guides/ORPHAN.md" in str(caught.value)


def test_collect_refuses_a_list_that_publishes_nothing(repository):
    """Stops when the listed sections hold no Markdown file."""
    with pytest.raises(PublishListError):
        _collect(repository, sections=("reference",))
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/docs_bundle/test_page_set.py -q`
Expected: collection error, `No module named 'sushicore.docs_bundle.page_set'`.

- [ ] **Step 3: Write the implementation**

`sushicore/docs_bundle/page_set.py`:

```python
"""Collects the pages and assets a repository publishes and checks every link they hold.

A link may leave the bundle; decision D10 of the documentation site design says what the site
does with it. A link whose target does not exist stops the collection.
"""

from __future__ import annotations

import posixpath
from dataclasses import dataclass
from pathlib import Path
from typing import final

from .errors import PageError, PublishListError
from .markdown_scan import MarkdownLink, first_heading, iter_links, local_path
from .page_order import K_INDEX_NAME, read_page_order
from .publish_list import K_FILE_NAME, K_SECTIONS, PublishList

K_DOCS = "docs"
K_FAQ = "guides/FAQ.md"
K_PAGE_SUFFIX = ".md"


@dataclass(frozen=True, slots=True)
class Page:
    """Holds one published page: its path below docs/, section, title and order."""

    source: str
    section: str
    title: str
    order: int


@dataclass(frozen=True, slots=True)
class PageSet:
    """Holds everything a bundle carries under pages/."""

    pages: tuple[Page, ...]
    assets: tuple[str, ...]
    faq: str | None


@final
class PageCollector:
    """Collects the published pages of one repository."""

    def __init__(self, repository_root: Path, publish_list: PublishList) -> None:
        """Stores the repository and the list that says what it publishes."""
        self._root = repository_root
        self._docs = repository_root / K_DOCS
        self._publish_list = publish_list

    def collect(self) -> PageSet:
        """Returns the published pages in section and index order, with their assets.

        Raises:
            PublishListError: An exclusion names no file, or nothing is published.
            PageError: A page has no title, no order, or a link to a missing file.
        """
        sources = self._published_sources()
        order = read_page_order(self._docs)
        known = frozenset(sources)
        pages: list[Page] = []
        assets: set[str] = set()
        for source in sources:
            path = self._docs / source
            text = path.read_text(encoding="utf-8")
            title = first_heading(text)
            if title is None:
                raise PageError(path, 1, "has no level-one heading to take its title from")
            if source not in order:
                raise PageError(
                    self._docs / K_INDEX_NAME, 1,
                    f"does not link to {source}, so the page has no order",
                )
            for link in iter_links(text):
                asset = self._asset_of(path, source, link, known)
                if asset is not None:
                    assets.add(asset)
            pages.append(Page(source, source.split("/", 1)[0], title, order[source]))
        pages.sort(key=lambda page: (K_SECTIONS.index(page.section), page.order))
        return PageSet(tuple(pages), tuple(sorted(assets)), K_FAQ if K_FAQ in known else None)

    def _published_sources(self) -> list[str]:
        """Returns the path below docs/ of every page in a listed section, less the exclusions."""
        list_path = self._docs / K_FILE_NAME
        found: list[str] = []
        for section in self._publish_list.sections:
            for path in sorted((self._docs / section).rglob(f"*{K_PAGE_SUFFIX}")):
                found.append(path.relative_to(self._docs).as_posix())
        unknown = sorted(self._publish_list.exclude - set(found))
        if unknown:
            raise PublishListError(
                f"{list_path}: exclude names {unknown[0]}, which is not a page of a listed section."
            )
        sources = [source for source in found if source not in self._publish_list.exclude]
        if not sources:
            raise PublishListError(f"{list_path}: the listed sections hold no page to publish.")
        return sources

    def _asset_of(
        self, path: Path, source: str, link: MarkdownLink, known: frozenset[str],
    ) -> str | None:
        """Returns the asset a link names, or None for a page or a file outside the bundle."""
        local = local_path(link.target)
        if local is None:
            return None
        if local.startswith("/"):
            raise PageError(path, link.line, f"links to {link.target}, an absolute path")
        target = posixpath.normpath(posixpath.join(K_DOCS, posixpath.dirname(source), local))
        if target.startswith(".."):
            raise PageError(path, link.line, f"links to {link.target}, which leaves the repository")
        if not (self._root / target).exists():
            raise PageError(path, link.line, f"links to {link.target}, which does not exist")
        if not target.startswith(K_DOCS + "/"):
            return None
        inside = target[len(K_DOCS) + 1:]
        if inside in known or inside.endswith(K_PAGE_SUFFIX):
            return None
        published = inside.split("/", 1)[0] in self._publish_list.sections
        return inside if published and (self._root / target).is_file() else None
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest tests/docs_bundle/test_page_set.py -q`
Expected: `10 passed`.

- [ ] **Step 5: Commit**

```bash
git add sushicore/docs_bundle/page_set.py tests/docs_bundle/test_page_set.py
git commit -m "feat(docs-bundle): collect the published pages and check their links"
```

---

### Task 5: The manifest

**Files:**
- Create: `sushicore/docs_bundle/bundle_manifest.py`
- Test: `tests/docs_bundle/test_bundle_manifest.py`

**Interfaces:**
- Consumes: `PublishList`, `PageSet`, `Page`.
- Produces: `K_SCHEMA_VERSION = 1`, `K_PAGES_DIR = "pages"`, `K_API_ROOT = "api/xml"`,
  `BundleIdentity(version: str, commit: str)`, `build_manifest(identity, publish_list, page_set,
  *, has_api: bool) -> dict[str, object]`.

- [ ] **Step 1: Write the failing test**

`tests/docs_bundle/test_bundle_manifest.py`:

```python
"""Pins the `bundle.json` document, the contract the documentation site reads."""

from __future__ import annotations

from sushicore.docs_bundle.bundle_manifest import BundleIdentity, build_manifest
from sushicore.docs_bundle.page_set import PageCollector
from sushicore.docs_bundle.publish_list import read_publish_list

K_IDENTITY = BundleIdentity(version="1.2.3", commit="c0ffee")

K_GOLDEN = {
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
            "source": "docs/guides/BUILDING.md",
        },
        {
            "path": "pages/guides/FAQ.md",
            "section": "guides",
            "title": "FAQ",
            "order": 3,
            "source": "docs/guides/FAQ.md",
        },
        {
            "path": "pages/architecture/OVERVIEW.md",
            "section": "architecture",
            "title": "Overview",
            "order": 1,
            "source": "docs/architecture/OVERVIEW.md",
        },
    ],
    "assets": ["pages/guides/images/shot.png"],
    "faq": "pages/guides/FAQ.md",
    "api": None,
}


def _manifest(repository, *, has_api: bool) -> dict:
    """Builds the manifest of the sample repository."""
    publish_list = read_publish_list(repository / "docs")
    page_set = PageCollector(repository, publish_list).collect()
    return build_manifest(K_IDENTITY, publish_list, page_set, has_api=has_api)


def test_build_matches_the_golden_document(repository):
    """Produces exactly the document the contract fixes, key order included."""
    manifest = _manifest(repository, has_api=False)
    assert manifest == K_GOLDEN
    assert list(manifest) == list(K_GOLDEN)


def test_build_names_the_api_root_when_the_bundle_carries_one(repository):
    """Records the format and the folder of the API reference."""
    assert _manifest(repository, has_api=True)["api"] == {
        "format": "doxygen-xml",
        "root": "api/xml",
    }
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/docs_bundle/test_bundle_manifest.py -q`
Expected: collection error, `No module named 'sushicore.docs_bundle.bundle_manifest'`.

- [ ] **Step 3: Write the implementation**

`sushicore/docs_bundle/bundle_manifest.py`:

```python
"""Builds `bundle.json`, the one document the site reads about a repository.

The fields and their rules are in `docs/reference/DOCS_BUNDLE.md`.
"""

from __future__ import annotations

from dataclasses import dataclass

from .page_set import K_DOCS, PageSet
from .publish_list import PublishList

K_SCHEMA_VERSION = 1
K_PAGES_DIR = "pages"
K_API_ROOT = "api/xml"
K_API_FORMAT = "doxygen-xml"


@dataclass(frozen=True, slots=True)
class BundleIdentity:
    """Holds the release a bundle is named after and the commit it was built from."""

    version: str
    commit: str


def build_manifest(
    identity: BundleIdentity, publish_list: PublishList, page_set: PageSet, *, has_api: bool,
) -> dict[str, object]:
    """Returns the `bundle.json` document, its keys in the order the contract lists them."""
    return {
        "schema": K_SCHEMA_VERSION,
        "repository": publish_list.name,
        "title": publish_list.title,
        "summary": publish_list.summary,
        "version": identity.version,
        "commit": identity.commit,
        "source_url": publish_list.source_url,
        "pages": [
            {
                "path": f"{K_PAGES_DIR}/{page.source}",
                "section": page.section,
                "title": page.title,
                "order": page.order,
                "source": f"{K_DOCS}/{page.source}",
            }
            for page in page_set.pages
        ],
        "assets": [f"{K_PAGES_DIR}/{asset}" for asset in page_set.assets],
        "faq": None if page_set.faq is None else f"{K_PAGES_DIR}/{page_set.faq}",
        "api": {"format": K_API_FORMAT, "root": K_API_ROOT} if has_api else None,
    }
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest tests/docs_bundle/test_bundle_manifest.py -q`
Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add sushicore/docs_bundle/bundle_manifest.py tests/docs_bundle/test_bundle_manifest.py
git commit -m "feat(docs-bundle): build the bundle.json document"
```

---

### Task 6: The API reference

**Files:**
- Create: `sushicore/docs_bundle/api_reference.py`
- Test: `tests/docs_bundle/test_api_reference.py`

**Interfaces:**
- Consumes: `ApiReferenceError`.
- Produces: `ApiSource(build: Callable[[], int], xml_dir: Path)`,
  `stage_api(source: ApiSource | None, destination: Path) -> None`.

- [ ] **Step 1: Write the failing test**

`tests/docs_bundle/test_api_reference.py`:

```python
"""Tests the staging of Doxygen's XML: what is built, what is copied, what stops it."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.docs_bundle.api_reference import ApiSource, stage_api
from sushicore.docs_bundle.errors import ApiReferenceError

K_INDEX = (
    '<?xml version="1.0"?>\n<doxygenindex>\n'
    '  <compound refid="classsr_1_1Graph" kind="class"><name>sr::Graph</name></compound>\n'
    '  <compound refid="namespacesr" kind="namespace"><name>sr</name></compound>\n'
    "</doxygenindex>\n"
)


def _xml_dir(tmp_path: Path) -> Path:
    """Writes an XML output folder with two named compounds and one stale file."""
    folder = tmp_path / "xml"
    folder.mkdir()
    (folder / "index.xml").write_text(K_INDEX, encoding="utf-8")
    for name in ("classsr_1_1Graph.xml", "namespacesr.xml", "classsr_1_1Removed.xml"):
        (folder / name).write_text("<doxygen/>\n", encoding="utf-8")
    return folder


def test_stage_builds_then_copies_what_the_index_names(tmp_path):
    """Runs the build once and copies the index and the files it names, nothing stale."""
    calls: list[str] = []
    source = ApiSource(build=lambda: calls.append("build") or 0, xml_dir=_xml_dir(tmp_path))
    destination = tmp_path / "staging" / "api" / "xml"
    stage_api(source, destination)
    assert calls == ["build"]
    assert sorted(path.name for path in destination.iterdir()) == [
        "classsr_1_1Graph.xml",
        "index.xml",
        "namespacesr.xml",
    ]


def test_stage_refuses_a_repository_with_no_api_source(tmp_path):
    """Stops when the publish list asks for an API the command cannot build."""
    with pytest.raises(ApiReferenceError) as caught:
        stage_api(None, tmp_path / "out")
    assert "api = true" in str(caught.value)


def test_stage_reports_a_failed_build(tmp_path):
    """Carries the exit code of a build that failed."""
    with pytest.raises(ApiReferenceError) as caught:
        stage_api(ApiSource(build=lambda: 3, xml_dir=_xml_dir(tmp_path)), tmp_path / "out")
    assert "3" in str(caught.value)


def test_stage_reports_a_build_that_wrote_no_xml(tmp_path):
    """Points at GENERATE_XML when the build left no index."""
    with pytest.raises(ApiReferenceError) as caught:
        stage_api(ApiSource(build=lambda: 0, xml_dir=tmp_path / "nothing"), tmp_path / "out")
    assert "GENERATE_XML" in str(caught.value)


def test_stage_reports_an_index_that_names_a_missing_file(tmp_path):
    """Names the file the index lists and the folder lacks."""
    folder = _xml_dir(tmp_path)
    (folder / "namespacesr.xml").unlink()
    with pytest.raises(ApiReferenceError) as caught:
        stage_api(ApiSource(build=lambda: 0, xml_dir=folder), tmp_path / "out")
    assert "namespacesr.xml" in str(caught.value)


def test_stage_reports_an_index_that_is_not_xml(tmp_path):
    """Reports a malformed index as its own failure, not as a parser traceback."""
    folder = _xml_dir(tmp_path)
    (folder / "index.xml").write_text("<doxygenindex>", encoding="utf-8")
    with pytest.raises(ApiReferenceError):
        stage_api(ApiSource(build=lambda: 0, xml_dir=folder), tmp_path / "out")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/docs_bundle/test_api_reference.py -q`
Expected: collection error, `No module named 'sushicore.docs_bundle.api_reference'`.

- [ ] **Step 3: Write the implementation**

`sushicore/docs_bundle/api_reference.py`:

```python
"""Builds a repository's API reference and stages the Doxygen XML a bundle carries."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from xml.etree import ElementTree

from .errors import ApiReferenceError

K_INDEX = "index.xml"


@dataclass(frozen=True, slots=True)
class ApiSource:
    """Holds how a repository builds its API reference and where the XML lands."""

    build: Callable[[], int]
    xml_dir: Path


def _named_files(index: Path) -> list[str]:
    """Returns the index and the file of every compound it names."""
    try:
        root = ElementTree.parse(index).getroot()
    except ElementTree.ParseError as error:
        raise ApiReferenceError(f"{index} is not valid XML: {error}") from error
    refids = sorted({compound.get("refid", "") for compound in root.iter("compound")})
    return [K_INDEX, *(f"{refid}.xml" for refid in refids if refid)]


def stage_api(source: ApiSource | None, destination: Path) -> None:
    """Builds the API reference and copies the XML its index names into *destination*.

    Raises:
        ApiReferenceError: No source, a failed build, no XML, or a file the index names
            and the output folder lacks.
    """
    if source is None:
        raise ApiReferenceError(
            "docs/publish.toml sets api = true, and this command builds no API reference."
        )
    code = source.build()
    if code != 0:
        raise ApiReferenceError(f"The API reference build exited with code {code}.")
    index = source.xml_dir / K_INDEX
    if not index.is_file():
        raise ApiReferenceError(
            f"{index} does not exist; set GENERATE_XML = YES in the Doxyfile."
        )
    destination.mkdir(parents=True, exist_ok=True)
    for name in _named_files(index):
        path = source.xml_dir / name
        if not path.is_file():
            raise ApiReferenceError(f"{index} names {name}, which is missing.")
        shutil.copyfile(path, destination / name)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest tests/docs_bundle/test_api_reference.py -q`
Expected: `6 passed`.

- [ ] **Step 5: Commit**

```bash
git add sushicore/docs_bundle/api_reference.py tests/docs_bundle/test_api_reference.py
git commit -m "feat(docs-bundle): stage the Doxygen XML the index names"
```

---

### Task 7: The archive

**Files:**
- Create: `sushicore/docs_bundle/bundle_archive.py`
- Test: `tests/docs_bundle/test_bundle_archive.py`

**Interfaces:**
- Consumes: nothing from the package.
- Produces: `write_archive(staging: Path, archive: Path) -> str`, which returns the archive's
  SHA-256 and writes `<archive name>.sha256` beside it.

- [ ] **Step 1: Write the failing test**

`tests/docs_bundle/test_bundle_archive.py`:

```python
"""Tests that the archive holds the staged files and is the same bytes every time."""

from __future__ import annotations

import hashlib
import os
import tarfile
from pathlib import Path

from sushicore.docs_bundle.bundle_archive import write_archive

from .sample_repository import write_file


def _staging(root: Path) -> Path:
    """Writes a staging folder with a manifest and two pages."""
    write_file(root, "bundle.json", "{}\n")
    write_file(root, "pages/guides/B.md", "# B\n")
    write_file(root, "pages/guides/A.md", "# A\n")
    return root


def test_write_packs_every_file_under_its_posix_name(tmp_path):
    """Stores each staged file, sorted, with no folder entries and fixed metadata."""
    archive = tmp_path / "out" / "docs-bundle-1.2.3.tar.gz"
    write_archive(_staging(tmp_path / "staging"), archive)
    with tarfile.open(archive, "r:gz") as packed:
        members = packed.getmembers()
        assert [member.name for member in members] == [
            "bundle.json",
            "pages/guides/A.md",
            "pages/guides/B.md",
        ]
        assert {(member.mtime, member.uid, member.gid, member.mode) for member in members} == {
            (0, 0, 0, 0o644),
        }
        assert packed.extractfile("pages/guides/A.md").read() == b"# A\n"


def test_write_returns_the_digest_and_writes_it_beside_the_archive(tmp_path):
    """Returns the SHA-256 of the archive and records it in the `.sha256` file."""
    archive = tmp_path / "docs-bundle-1.2.3.tar.gz"
    digest = write_archive(_staging(tmp_path / "staging"), archive)
    assert digest == hashlib.sha256(archive.read_bytes()).hexdigest()
    recorded = (tmp_path / "docs-bundle-1.2.3.tar.gz.sha256").read_bytes()
    assert recorded == f"{digest}  docs-bundle-1.2.3.tar.gz\n".encode("ascii")


def test_write_is_reproducible(tmp_path):
    """Produces the same bytes from the same files written at another time."""
    first = _staging(tmp_path / "first")
    second = _staging(tmp_path / "second")
    for path in second.rglob("*.md"):
        os.utime(path, (1_000_000_000, 1_000_000_000))
    one = write_archive(first, tmp_path / "one.tar.gz")
    two = write_archive(second, tmp_path / "two.tar.gz")
    assert one == two
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/docs_bundle/test_bundle_archive.py -q`
Expected: collection error, `No module named 'sushicore.docs_bundle.bundle_archive'`.

- [ ] **Step 3: Write the implementation**

`sushicore/docs_bundle/bundle_archive.py`:

```python
"""Packs a staged bundle into a reproducible gzip tar and records its SHA-256."""

from __future__ import annotations

import gzip
import hashlib
import tarfile
from pathlib import Path

K_MODE = 0o644
K_DIGEST_SUFFIX = ".sha256"


def _members(staging: Path) -> list[tuple[str, Path]]:
    """Returns every file under *staging* with its POSIX name, sorted by that name."""
    files = (path for path in staging.rglob("*") if path.is_file())
    return sorted((path.relative_to(staging).as_posix(), path) for path in files)


def write_archive(staging: Path, archive: Path) -> str:
    """Writes the files under *staging* to *archive* and returns the archive's SHA-256.

    Names are sorted and every time, owner and mode is fixed, so the same files give the
    same bytes. The digest is also written to `<archive name>.sha256`.
    """
    archive.parent.mkdir(parents=True, exist_ok=True)
    with archive.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as packed:
            with tarfile.open(fileobj=packed, mode="w", format=tarfile.GNU_FORMAT) as tar:
                for name, path in _members(staging):
                    member = tarfile.TarInfo(name)
                    member.size = path.stat().st_size
                    member.mode = K_MODE
                    with path.open("rb") as content:
                        tar.addfile(member, content)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    record = archive.with_name(archive.name + K_DIGEST_SUFFIX)
    record.write_bytes(f"{digest}  {archive.name}\n".encode("ascii"))
    return digest
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest tests/docs_bundle/test_bundle_archive.py -q`
Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add sushicore/docs_bundle/bundle_archive.py tests/docs_bundle/test_bundle_archive.py
git commit -m "feat(docs-bundle): write a reproducible archive and its digest"
```

---

### Task 8: The producer

**Files:**
- Create: `sushicore/docs_bundle/source_revision.py`, `sushicore/docs_bundle/producer.py`
- Test: `tests/docs_bundle/test_producer.py`

**Interfaces:**
- Consumes: `read_publish_list`, `PageCollector`, `PageSet`, `K_DOCS`, `build_manifest`,
  `BundleIdentity`, `K_PAGES_DIR`, `K_API_ROOT`, `ApiSource`, `stage_api`, `write_archive`,
  `ReleaseError`.
- Produces: `read_head_commit(repository_root: Path) -> str`;
  `K_DEFAULT_OUTPUT = Path("build") / "docs" / "bundle"`;
  `BundleRequest(repository_root, release, output_dir, api=None)`;
  `BundleResult(archive, sha256, page_count)`;
  `BundleProducer(read_commit=read_head_commit).produce(request) -> BundleResult`.

- [ ] **Step 1: Write the failing test**

`tests/docs_bundle/test_producer.py`:

```python
"""Tests the producer end to end on the sample repository."""

from __future__ import annotations

import json
import tarfile
from pathlib import Path

import pytest

from sushicore.docs_bundle.api_reference import ApiSource
from sushicore.docs_bundle.errors import ApiReferenceError, ReleaseError
from sushicore.docs_bundle.producer import BundleProducer, BundleRequest
from sushicore.docs_bundle.source_revision import read_head_commit

from .sample_repository import K_PUBLISH, commit_all, write_file

K_COMMIT = "c0ffee"


def _produce(repository: Path, out: Path, release: str = "1.2.3", api: ApiSource | None = None):
    """Produces the sample's bundle into *out* with a fixed commit."""
    producer = BundleProducer(read_commit=lambda root: K_COMMIT)
    return producer.produce(BundleRequest(repository, release, out, api))


def _names(archive: Path) -> list[str]:
    """Returns the member names of an archive."""
    with tarfile.open(archive, "r:gz") as packed:
        return packed.getnames()


def test_produce_writes_the_pages_the_assets_and_the_manifest(repository, tmp_path):
    """Packs the published pages, their asset and bundle.json, and nothing unpublished."""
    result = _produce(repository, tmp_path / "out")
    assert result.archive == tmp_path / "out" / "docs-bundle-1.2.3.tar.gz"
    assert result.page_count == 3
    assert _names(result.archive) == [
        "bundle.json",
        "pages/architecture/OVERVIEW.md",
        "pages/guides/BUILDING.md",
        "pages/guides/FAQ.md",
        "pages/guides/images/shot.png",
    ]
    with tarfile.open(result.archive, "r:gz") as packed:
        manifest = json.loads(packed.extractfile("bundle.json").read().decode("utf-8"))
    assert (manifest["version"], manifest["commit"], manifest["api"]) == ("1.2.3", K_COMMIT, None)


def test_produce_is_reproducible_and_replaces_an_earlier_staging(repository, tmp_path):
    """Gives the same digest twice, and a file left in staging does not reach the archive."""
    first = _produce(repository, tmp_path / "out")
    write_file(tmp_path / "out", ".docs-bundle-staging/pages/guides/LEFTOVER.md", "# Old\n")
    second = _produce(repository, tmp_path / "out")
    assert first.sha256 == second.sha256
    assert "pages/guides/LEFTOVER.md" not in _names(second.archive)


@pytest.mark.parametrize("release", ["v1.2.3", "1.2", "1.2.3-rc1", ""])
def test_produce_refuses_a_release_that_is_not_three_integers(repository, tmp_path, release):
    """Refuses a tag's v, a short version and a pre-release suffix."""
    with pytest.raises(ReleaseError):
        _produce(repository, tmp_path / "out", release=release)


def test_produce_carries_the_api_when_the_list_asks_for_it(repository, tmp_path):
    """Packs api/xml and names it in the manifest when publish.toml sets api = true."""
    write_file(repository, "docs/publish.toml", K_PUBLISH + "api = true\n")
    xml_dir = tmp_path / "xml"
    write_file(xml_dir, "index.xml", "<doxygenindex/>\n")
    result = _produce(repository, tmp_path / "out", api=ApiSource(lambda: 0, xml_dir))
    assert "api/xml/index.xml" in _names(result.archive)
    with tarfile.open(result.archive, "r:gz") as packed:
        manifest = json.loads(packed.extractfile("bundle.json").read().decode("utf-8"))
    assert manifest["api"] == {"format": "doxygen-xml", "root": "api/xml"}


def test_produce_stops_when_the_list_asks_for_an_api_nobody_builds(repository, tmp_path):
    """Fails before writing an archive when api = true and no source was given."""
    write_file(repository, "docs/publish.toml", K_PUBLISH + "api = true\n")
    with pytest.raises(ApiReferenceError):
        _produce(repository, tmp_path / "out")
    assert not (tmp_path / "out" / "docs-bundle-1.2.3.tar.gz").exists()


def test_read_head_commit_returns_the_checked_out_hash(repository):
    """Reads the full hash of HEAD from a real checkout."""
    committed = commit_all(repository)
    assert read_head_commit(repository) == committed


def test_read_head_commit_reports_a_folder_that_is_no_checkout(tmp_path, monkeypatch):
    """Reports a folder outside any repository as a release error."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    with pytest.raises(ReleaseError):
        read_head_commit(tmp_path)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/docs_bundle/test_producer.py -q`
Expected: collection error, `No module named 'sushicore.docs_bundle.producer'`.

- [ ] **Step 3: Write the implementation**

`sushicore/docs_bundle/source_revision.py`:

```python
"""Reads the commit a bundle is built from."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .errors import ReleaseError


def read_head_commit(repository_root: Path) -> str:
    """Returns the full hash of the commit checked out in *repository_root*.

    Raises:
        ReleaseError: git cannot be run, or the folder is not a checkout.
    """
    try:
        done = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository_root, capture_output=True, text=True, check=False,
        )
    except OSError as error:
        raise ReleaseError(
            "git could not be run, and a bundle records the commit it was built from."
        ) from error
    if done.returncode != 0:
        raise ReleaseError(f"{repository_root} is not a git checkout: {done.stderr.strip()}")
    return done.stdout.strip()
```

`sushicore/docs_bundle/producer.py`:

```python
"""Produces a repository's documentation bundle: stage, describe, pack."""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, final

from .api_reference import ApiSource, stage_api
from .bundle_archive import write_archive
from .bundle_manifest import K_API_ROOT, K_PAGES_DIR, BundleIdentity, build_manifest
from .errors import ReleaseError
from .page_set import K_DOCS, PageCollector, PageSet
from .publish_list import read_publish_list
from .source_revision import read_head_commit

K_DEFAULT_OUTPUT = Path("build") / "docs" / "bundle"
K_RELEASE = re.compile(r"^\d+\.\d+\.\d+$")
K_MANIFEST_NAME = "bundle.json"
K_STAGING = ".docs-bundle-staging"


@dataclass(frozen=True, slots=True)
class BundleRequest:
    """Holds what to bundle, the release to name it after and where to write it."""

    repository_root: Path
    release: str
    output_dir: Path
    api: ApiSource | None = None


@dataclass(frozen=True, slots=True)
class BundleResult:
    """Holds the archive a run wrote, its SHA-256 and how many pages it carries."""

    archive: Path
    sha256: str
    page_count: int


@final
class BundleProducer:
    """Produces one repository's documentation bundle."""

    def __init__(self, read_commit: Callable[[Path], str] = read_head_commit) -> None:
        """Stores the reader of the commit a bundle records."""
        self._read_commit = read_commit

    def produce(self, request: BundleRequest) -> BundleResult:
        """Writes `docs-bundle-<release>.tar.gz` into the request's output folder.

        Raises:
            DocsBundleError: The release, the publish list, a page or the API reference
                cannot be used; nothing is archived.
        """
        if not K_RELEASE.match(request.release):
            raise ReleaseError(
                f"{request.release!r} is not a release; write it as 1.2.3, without the v of the tag."
            )
        root = request.repository_root
        publish_list = read_publish_list(root / K_DOCS)
        page_set = PageCollector(root, publish_list).collect()
        identity = BundleIdentity(request.release, self._read_commit(root))
        staging = request.output_dir / K_STAGING
        if staging.exists():
            shutil.rmtree(staging)
        self._stage_pages(root, page_set, staging)
        if publish_list.api:
            stage_api(request.api, staging / K_API_ROOT)
        manifest = build_manifest(identity, publish_list, page_set, has_api=publish_list.api)
        text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
        (staging / K_MANIFEST_NAME).write_bytes(text.encode("utf-8"))
        archive = request.output_dir / f"docs-bundle-{request.release}.tar.gz"
        digest = write_archive(staging, archive)
        return BundleResult(archive, digest, len(page_set.pages))

    def _stage_pages(self, root: Path, page_set: PageSet, staging: Path) -> None:
        """Copies every published page and asset under the staging folder's pages/."""
        sources = [page.source for page in page_set.pages] + list(page_set.assets)
        for source in sources:
            target = staging / K_PAGES_DIR / source
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / K_DOCS / source, target)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest tests/docs_bundle/test_producer.py -q`
Expected: `10 passed`.

- [ ] **Step 5: Commit**

```bash
git add sushicore/docs_bundle/source_revision.py sushicore/docs_bundle/producer.py tests/docs_bundle/test_producer.py
git commit -m "feat(docs-bundle): produce the bundle from a repository"
```

---

### Task 9: A group that runs bare in the catalogue

**Files:**
- Modify: `sushicore/describe.py` (`_flatten`, lines 99-115)
- Test: `tests/test_cli_surface.py` (append one test)

**Interfaces:**
- Consumes: nothing new.
- Produces: `catalogue(app, ...)["commands"]` holds an entry named after a group when that
  group's Click object has `invoke_without_command` set, before the group's children.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_cli_surface.py`:

```python
def test_catalogue_lists_a_group_that_runs_bare_beside_its_children():
    """A group that runs without a subcommand is a command; one that shows help is not."""
    app = _app()
    docs = typer.Typer(help="Build the reference.")

    @docs.callback(invoke_without_command=True)
    def docs_root() -> None:
        """Runs when no subcommand is given."""

    @docs.command("bundle")
    def bundle() -> None:
        """Bundle the pages."""

    container = typer.Typer(help="Containers.", no_args_is_help=True)

    @container.command("run")
    def container_run() -> None:
        """Start the container."""

    app.add_typer(docs, name="docs")
    app.add_typer(container, name="container")
    commands = catalogue(app, distribution="sushicore")["commands"]
    assert [command["name"] for command in commands] == [
        "build", "container run", "docs", "docs bundle",
    ]
    assert commands[2]["help"] == "Build the reference."
    assert commands[2]["params"] == []
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_cli_surface.py::test_catalogue_lists_a_group_that_runs_bare_beside_its_children -q`
Expected: FAIL; the names are `["build", "container run", "docs bundle"]`.

- [ ] **Step 3: Change `_flatten`**

Replace the function in `sushicore/describe.py` with:

```python
def _flatten(group: "click.Group", applies_to: Sequence[str], prefix: str = "") -> list[dict]:
    """Describes every visible command under *group*, sorted, with its full name.

    A nested group contributes its children under ``"<group> <child>"``. It gets an entry
    of its own only when it runs without a subcommand. A hidden command or group is an old
    spelling and is left out.
    """
    described: list[dict] = []
    for name in sorted(getattr(group, "commands", {})):
        command = group.commands[name]
        if getattr(command, "hidden", False):
            continue
        if not hasattr(command, "commands"):
            described.append(_command(prefix + name, command, applies_to))
            continue
        if getattr(command, "invoke_without_command", False):
            described.append(_command(prefix + name, command, applies_to))
        described.extend(_flatten(command, applies_to, prefix + name + " "))
    return described
```

- [ ] **Step 4: Run the surface tests**

Run: `python -m pytest tests/test_cli_surface.py -q`
Expected: every test passes, the new one included.

- [ ] **Step 5: Commit**

```bash
git add sushicore/describe.py tests/test_cli_surface.py
git commit -m "feat(describe): list a group that runs without a subcommand"
```

---

### Task 10: The commands, the module entry and the public surface

**Files:**
- Create: `sushicore/docs_bundle/commands.py`, `sushicore/docs_bundle/__main__.py`
- Modify: `sushicore/docs_bundle/__init__.py`
- Test: `tests/docs_bundle/test_commands.py`, `tests/docs_bundle/test_main.py`,
  `tests/docs_bundle/test_layering.py`

**Interfaces:**
- Consumes: `BundleProducer`, `BundleRequest`, `K_DEFAULT_OUTPUT`, `ApiSource`,
  `sushicore.errors.SushiCoreError`.
- Produces: `register_docs_commands(app, *, program, panel, project_root, api=None,
  report=print, group_cls=None) -> None`; `main(argv: Sequence[str] | None = None) -> int` in
  `__main__`; the names of SPEC.md section 3 importable from `sushicore.docs_bundle`.

- [ ] **Step 1: Write the failing tests**

`tests/docs_bundle/test_commands.py`:

```python
"""Tests the `docs` group a CLI registers: the bare form, `bundle`, and what it reports."""

from __future__ import annotations

from pathlib import Path

import typer
from typer.testing import CliRunner

from sushicore.describe import catalogue
from sushicore.docs_bundle import ApiSource, PublishListError, register_docs_commands


def _app(repository: Path, reported: list[str], api=None) -> typer.Typer:
    """Returns an application named `sx` with one command and the docs group."""
    app = typer.Typer(name="sx", no_args_is_help=True, add_completion=False)

    @app.command("build")
    def build() -> None:
        """Build."""

    register_docs_commands(
        app, program="sx", panel="Project", project_root=lambda: repository,
        api=api, report=reported.append,
    )
    return app


def test_bare_docs_builds_the_api_and_returns_its_code(repository):
    """`sx docs` runs the API build and exits with what it returns."""
    calls: list[str] = []
    source = ApiSource(build=lambda: calls.append("build") or 4, xml_dir=repository / "xml")
    result = CliRunner().invoke(_app(repository, [], api=lambda: source), ["docs"])
    assert result.exit_code == 4
    assert calls == ["build"]


def test_bare_docs_shows_help_when_the_cli_builds_no_api(repository):
    """`sx docs` lists `bundle` when there is no API reference to build."""
    result = CliRunner().invoke(_app(repository, []), ["docs"])
    assert "bundle" in result.output


def test_bundle_writes_the_archive_and_reports_it(checkout):
    """`sx docs bundle --release` writes under build/docs/bundle and reports two lines."""
    reported: list[str] = []
    result = CliRunner().invoke(_app(checkout, reported), ["docs", "bundle", "--release", "1.2.3"])
    assert result.exit_code == 0, result.output
    archive = checkout / "build" / "docs" / "bundle" / "docs-bundle-1.2.3.tar.gz"
    assert archive.is_file()
    assert reported[0] == f"{archive} (3 pages)"
    assert reported[1].startswith("sha256 ") and len(reported[1]) == 7 + 64


def test_bundle_writes_where_out_says(checkout, tmp_path):
    """`--out` moves the archive."""
    arguments = ["docs", "bundle", "--release", "1.2.3", "--out", str(tmp_path / "elsewhere")]
    assert CliRunner().invoke(_app(checkout, []), arguments).exit_code == 0
    assert (tmp_path / "elsewhere" / "docs-bundle-1.2.3.tar.gz").is_file()


def test_bundle_requires_a_release(repository):
    """`sx docs bundle` without `--release` is a usage error."""
    assert CliRunner().invoke(_app(repository, []), ["docs", "bundle"]).exit_code == 2


def test_bundle_lets_a_bundle_error_reach_the_entry_point(repository):
    """A broken publish list leaves the command as the error `entry.run` prints."""
    (repository / "docs" / "publish.toml").unlink()
    result = CliRunner().invoke(_app(repository, []), ["docs", "bundle", "--release", "1.2.3"])
    assert isinstance(result.exception, PublishListError)


def test_the_catalogue_holds_docs_only_when_it_runs_bare(repository):
    """`--describe` lists `docs` for a CLI with an API and `docs bundle` for every CLI."""
    source = ApiSource(build=lambda: 0, xml_dir=repository / "xml")
    with_api = catalogue(_app(repository, [], api=lambda: source), distribution="sushicore")
    without = catalogue(_app(repository, []), distribution="sushicore")
    assert [c["name"] for c in with_api["commands"]] == ["build", "docs", "docs bundle"]
    assert [c["name"] for c in without["commands"]] == ["build", "docs bundle"]
```

`tests/docs_bundle/test_main.py`:

```python
"""Tests `python -m sushicore.docs_bundle`, the entry of a repository with no CLI."""

from __future__ import annotations

from sushicore.docs_bundle.__main__ import main


def test_main_writes_the_archive_and_prints_it(checkout, tmp_path, capsys):
    """Writes the bundle of the repository `--root` names and prints path and digest."""
    out = tmp_path / "out"
    code = main(["--release", "1.2.3", "--root", str(checkout), "--out", str(out)])
    assert code == 0
    printed = capsys.readouterr().out.splitlines()
    assert printed[0] == str(out / "docs-bundle-1.2.3.tar.gz")
    assert printed[1].startswith("sha256 ")


def test_main_reports_a_failure_as_one_line_and_exit_one(repository, capsys):
    """Prints one line on stderr and returns 1 when the release cannot be used."""
    assert main(["--release", "v1", "--root", str(repository)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.count("\n") == 1
```

`tests/docs_bundle/test_layering.py`:

```python
"""Keeps the sub-package's layers pointing downward and Typer out of module scope."""

from __future__ import annotations

import ast
from pathlib import Path

import sushicore.docs_bundle as docs_bundle

K_ROOT = Path(docs_bundle.__file__).parent
K_LAYER = {
    "errors": 0, "markdown_scan": 0,
    "publish_list": 1, "page_order": 1, "api_reference": 1, "bundle_archive": 1,
    "source_revision": 1,
    "page_set": 2, "bundle_manifest": 3, "producer": 4, "commands": 5, "__main__": 5,
}
K_COMMAND_FRAMEWORKS = frozenset({"typer", "click"})


def _module_imports(path: Path) -> tuple[set[str], set[str]]:
    """Returns the sibling modules a file imports and the top-level packages it imports."""
    siblings: set[str] = set()
    packages: set[str] = set()
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module:
            siblings.add(node.module.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            packages.add(node.module.split(".")[0])
        elif isinstance(node, ast.Import):
            packages.update(alias.name.split(".")[0] for alias in node.names)
    return siblings, packages


def test_every_module_has_a_layer():
    """Fails when a file is added without a row in the layer table."""
    modules = {path.stem for path in K_ROOT.glob("*.py")} - {"__init__"}
    assert modules == set(K_LAYER)


def test_no_module_imports_a_higher_or_equal_layer():
    """A module imports only siblings in a lower layer."""
    for name, layer in K_LAYER.items():
        siblings, _ = _module_imports(K_ROOT / f"{name}.py")
        for sibling in siblings:
            assert K_LAYER[sibling] < layer, f"{name} imports {sibling}"


def test_no_module_imports_a_command_framework_at_module_level():
    """Typer and Click are imported inside the function that needs them."""
    for path in K_ROOT.glob("*.py"):
        _, packages = _module_imports(path)
        assert not packages & K_COMMAND_FRAMEWORKS, path.name
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/docs_bundle/test_commands.py tests/docs_bundle/test_main.py tests/docs_bundle/test_layering.py -q`
Expected: collection errors for the two missing modules and `ImportError: cannot import name
'ApiSource' from 'sushicore.docs_bundle'`.

- [ ] **Step 3: Write the implementation**

`sushicore/docs_bundle/commands.py`:

```python
"""The `docs` command group, registered on a CLI from where its project and API are.

The behaviour of each invocation is in `docs/reference/DOCS_BUNDLE.md`.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

from .api_reference import ApiSource
from .producer import K_DEFAULT_OUTPUT, BundleProducer, BundleRequest

if TYPE_CHECKING:
    import typer

K_API_HELP = "Build the API reference with Doxygen, or bundle the documentation."
K_BUNDLE_HELP = "Bundle the documentation."


def register_docs_commands(
    app: "typer.Typer",
    *,
    program: str,
    panel: str,
    project_root: Callable[[], Path],
    api: Callable[[], ApiSource] | None = None,
    report: Callable[[str], None] = print,
    group_cls: type | None = None,
) -> None:
    """Adds the `docs` group to *app*: the bare form when *api* is given, and `bundle`.

    Args:
        app: The application to add the group to.
        program: The command the user types, for the examples.
        panel: The help panel the group is listed under.
        project_root: Returns the repository root; called when a command runs.
        api: Returns how this CLI builds its API reference; None for a CLI that builds none.
        report: Prints one line of the result the way the CLI prints.
        group_cls: The Click group class the CLI draws its help with.
    """
    import click
    import typer

    options: dict = {
        "help": K_BUNDLE_HELP if api is None else K_API_HELP,
        "no_args_is_help": api is None,
        "rich_markup_mode": "rich",
    }
    if group_cls is not None:
        options["cls"] = group_cls
    docs_app = typer.Typer(**options)

    if api is not None:
        @docs_app.callback(invoke_without_command=True, epilog=f"{program} docs")
        def docs() -> None:
            """Build the API reference with Doxygen, or bundle the documentation."""
            if click.get_current_context().invoked_subcommand is None:
                raise typer.Exit(api().build())

    @docs_app.command(
        "bundle",
        epilog=f"{program} docs bundle --release 1.2.3\n"
               f"{program} docs bundle --release 1.2.3 --out build/site",
    )
    def bundle(
        release: str = typer.Option(
            ..., "--release", help="The release the bundle is named after, as 1.2.3."),
        out: Optional[Path] = typer.Option(
            None, "--out", help="Where the archive is written. Defaults to build/docs/bundle."),
    ) -> None:
        """Bundle the published documentation for docs.sushisystems.io."""
        root = project_root()
        request = BundleRequest(
            repository_root=root,
            release=release,
            output_dir=out if out is not None else root / K_DEFAULT_OUTPUT,
            api=None if api is None else api(),
        )
        result = BundleProducer().produce(request)
        report(f"{result.archive} ({result.page_count} pages)")
        report(f"sha256 {result.sha256}")

    app.add_typer(docs_app, name="docs", rich_help_panel=panel)
```

`sushicore/docs_bundle/__main__.py`:

```python
"""Bundles the documentation of a repository that has no CLI of its own.

Usage: python -m sushicore.docs_bundle --release 1.2.3 [--root DIR] [--out DIR]
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from ..errors import SushiCoreError
from .producer import K_DEFAULT_OUTPUT, BundleProducer, BundleRequest

K_PROGRAM = "python -m sushicore.docs_bundle"
K_EXIT_FAILURE = 1


def main(argv: Sequence[str] | None = None) -> int:
    """Parses the arguments, writes the bundle and returns the process exit code."""
    parser = argparse.ArgumentParser(
        prog=K_PROGRAM, description="Bundle a repository's published documentation.")
    parser.add_argument("--release", required=True, help="The release, as 1.2.3.")
    parser.add_argument("--root", type=Path, default=None, help="The repository root.")
    parser.add_argument("--out", type=Path, default=None, help="Where the archive is written.")
    arguments = parser.parse_args(argv)
    root = (arguments.root or Path.cwd()).resolve()
    output_dir = arguments.out if arguments.out is not None else root / K_DEFAULT_OUTPUT
    try:
        result = BundleProducer().produce(BundleRequest(root, arguments.release, output_dir))
    except SushiCoreError as error:
        print(f"{K_PROGRAM}: {error}", file=sys.stderr)
        return K_EXIT_FAILURE
    print(result.archive)
    print(f"sha256 {result.sha256}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

`sushicore/docs_bundle/__init__.py`, whole file below the header:

```python
"""The documentation bundle: what a repository publishes to docs.sushisystems.io."""

from __future__ import annotations

from .api_reference import ApiSource
from .bundle_manifest import K_SCHEMA_VERSION
from .commands import register_docs_commands
from .errors import (
    ApiReferenceError,
    DocsBundleError,
    PageError,
    PublishListError,
    ReleaseError,
)
from .producer import K_DEFAULT_OUTPUT, BundleProducer, BundleRequest, BundleResult

__all__ = [
    "ApiReferenceError",
    "ApiSource",
    "BundleProducer",
    "BundleRequest",
    "BundleResult",
    "DocsBundleError",
    "K_DEFAULT_OUTPUT",
    "K_SCHEMA_VERSION",
    "PageError",
    "PublishListError",
    "ReleaseError",
    "register_docs_commands",
]
```

- [ ] **Step 4: Run the whole suite**

Run: `python -m pytest tests -q`
Expected: every test passes; the count is the previous total plus 71.

- [ ] **Step 5: Commit**

```bash
git add sushicore/docs_bundle/commands.py sushicore/docs_bundle/__main__.py sushicore/docs_bundle/__init__.py tests/docs_bundle/test_commands.py tests/docs_bundle/test_main.py tests/docs_bundle/test_layering.py
git commit -m "feat(docs-bundle): register the docs group and the module entry"
```

---

### Task 11: SushiCore's documents

**Files:**
- Create: `sushicore/docs_bundle/README.md`, `docs/reference/DOCS_BUNDLE.md`
- Modify: `docs/README.md` (reference table), `docs/architecture/OVERVIEW.md` (the surfaces
  table and the Typer rule), `docs/reference/GLOSSARY.md`, `docs/reference/CHANGELOG.md`,
  `docs/design/REMAINING_WORK.md`, `docs/CONTRIBUTING.md` (the "must carry" table)

**Interfaces:** none; this task makes the manual true. Load the `documentation` and
`humanizer` skills before writing.

- [ ] **Step 1: Write `sushicore/docs_bundle/README.md`**

Follow the shape of `sushicore/help/README.md`: a two-sentence opening, then `## What it owns`
(one row per file with its public names, copied from SPEC.md section 2), `## What it depends
on` (`sushicore.errors`, `sushicore.workspace.read_toml`, the standard library; Typer and Click
inside `register_docs_commands` only), and `## Using it` with this block:

```python
from sushicore.docs_bundle import ApiSource, register_docs_commands

register_docs_commands(
    app,
    program="sr",
    panel="Project",
    project_root=find_project_root,
    api=lambda: ApiSource(build=project_svc.docs, xml_dir=find_project_root() / "build/docs/api-site/xml"),
    report=console.success,
    group_cls=_help_group,
)
```

- [ ] **Step 2: Write `docs/reference/DOCS_BUNDLE.md`**

Title `# Documentation bundle`. Four sections, each taken from the SushiStack spec's section 4
and SPEC.md here, restated as fact and not as plan:

1. `## The archive`: the name, the layout of 4.1, the `.sha256` file, reproducibility.
2. `## bundle.json`: the golden document of `tests/docs_bundle/test_bundle_manifest.py` as the
   example, then one table row per field with its rule, `assets` and `source_url` included.
3. `## docs/publish.toml`: the example of 4.3 and one row per key with its type, default and
   rule; the four sections; the exclusion rule.
4. `## The commands`: the table of SPEC.md section 4 and the three limits of its section 6.

- [ ] **Step 3: Update the pages the change made false**

- `docs/README.md`: add to the reference table, above Changelog,
  `| [Documentation bundle](reference/DOCS_BUNDLE.md) | The archive a repository publishes to the documentation site, its `bundle.json` and `docs/publish.toml` |`.
- `docs/architecture/OVERVIEW.md`: change the first paragraph's "three sub-packages" to
  "four"; add to "The surfaces every CLI registers"
  `| [`docs_bundle`](../../sushicore/docs_bundle/README.md) | The `docs` command group and the bundle `docs bundle` writes |`;
  in "Rules the code keeps", add `docs_bundle/commands.py` to the modules that import Typer
  inside the function that needs it; change the `describe` wording nowhere else.
- `docs/reference/GLOSSARY.md`: add, in alphabetical place,
  `| Documentation bundle | The archive `docs bundle` writes: the published pages, their assets, the Doxygen XML and `bundle.json` |`
  and `| Publish list | `docs/publish.toml`, where a repository says which sections it publishes |`.
- `docs/CONTRIBUTING.md`: add to "What a change must carry"
  `| Changes a field of `bundle.json` or a key of `docs/publish.toml` | [Documentation bundle](reference/DOCS_BUNDLE.md) and `K_SCHEMA_VERSION`; the site reads both |`.
- `docs/design/REMAINING_WORK.md`: add under "Open programmes" a section
  `### Documentation site, sub-project 1` that names `docs/agent/2026_10_07_DOCS_BUNDLE/SPEC.md`
  and lists what stays open after this plan: the release that carries `docs_bundle`, and the
  seven repositories of sub-project 3.
- `docs/reference/CHANGELOG.md`, under `## Unreleased`, newest first:

```
- 2026-10-07 — docs-bundle: Added the documentation bundle producer and the `docs` command group a CLI registers (`sushicore/docs_bundle/`, `register_docs_commands`, `BundleProducer`).
- 2026-10-07 — describe: Listed a group that runs without a subcommand as a command of its own in the catalogue (`sushicore/describe.py`, `_flatten`).
```

- [ ] **Step 4: Run the checkers**

Run, in the SushiCore repository:

```bash
python tools/documentation/check_docs_layout.py .
python tools/documentation/check_changelog.py .
python tools/documentation/check_source_comments.py .
python -m unittest discover -s tools/tests
```

Expected: `check_changelog.py` prints nothing; the other two print only what they printed
before this plan (record the output of both before step 1 and compare); unittest reports OK.

- [ ] **Step 5: Commit**

```bash
git add sushicore/docs_bundle/README.md docs/reference/DOCS_BUNDLE.md docs/README.md docs/architecture/OVERVIEW.md docs/reference/GLOSSARY.md docs/reference/CHANGELOG.md docs/design/REMAINING_WORK.md docs/CONTRIBUTING.md docs/agent/2026_10_07_DOCS_BUNDLE
git commit -m "docs(docs-bundle): describe the bundle, its contract and its commands"
```

---

### Task 12: `publish.toml` in the documentation tree (SushiSkills)

**Files (in `D:/Projects/sushiskills`):**
- Modify: `skills/documentation/SKILL.md` (the tree block)
- Modify: `tools/documentation/check_docs_layout.py` (`K_DOCS_ENTRIES`)
- Test: `tools/tests/test_check_docs_layout.py`

**Interfaces:**
- Produces: `rule_docs_entries` accepts `docs/publish.toml`.

- [ ] **Step 1: Write the failing test**

Add `rule_docs_entries` to the import list of `tools/tests/test_check_docs_layout.py` and
append this class:

```python
class DocsEntriesTest(unittest.TestCase):
    """Checks which entries may sit directly under docs/."""

    def test_accepts_the_publish_list(self) -> None:
        """Accepts docs/publish.toml and still reports any other loose file."""
        with tempfile.TemporaryDirectory() as folder:
            repository = _repository(
                folder, {"README.md": "# R\n", "publish.toml": "", "notes.txt": ""},
            )
            self.assertEqual(_names(rule_docs_entries(repository)), ["notes.txt"])
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m unittest tools.tests.test_check_docs_layout -v` from the SushiSkills root; if
the package form does not resolve, `python -m unittest discover -s tools/tests -p "test_check_docs_layout.py" -v`.
Expected: FAIL; the names are `["notes.txt", "publish.toml"]`.

- [ ] **Step 3: Accept the entry**

In `tools/documentation/check_docs_layout.py`, add `"publish.toml"` to `K_DOCS_ENTRIES`:

```python
K_DOCS_ENTRIES = frozenset(
    {
        "README.md", "CONTRIBUTING.md", "DOCUMENTATION_STYLE_GUIDE.md", "publish.toml",
        "getting_started", "architecture", "guides", "reference", "design", "agent", "archive",
    }
)
```

In `skills/documentation/SKILL.md`, add one line to the tree block, below
`DOCUMENTATION_STYLE_GUIDE.md`:

```
    publish.toml                  what the repository publishes to docs.sushisystems.io
```

- [ ] **Step 4: Run the tests**

Run: `python -m unittest discover -s tools/tests`
Expected: OK.

- [ ] **Step 5: Commit**

```bash
git add skills/documentation/SKILL.md tools/documentation/check_docs_layout.py tools/tests/test_check_docs_layout.py
git commit -m "feat(documentation): name docs/publish.toml in the docs tree"
```

---

### Task 13: SushiRuntime publishes (the list, the XML, the checker)

**Files (in `D:/Projects/sushiruntime`):**
- Create: `docs/publish.toml`
- Modify: `Doxyfile` (`GENERATE_XML`), `tools/documentation/check_docs_layout.py`
  (`K_DOCS_ENTRIES`, the same line as task 12)
- Modify: `docs/reference/CHANGELOG.md`

**Interfaces:**
- Produces: a repository `python -m sushicore.docs_bundle` can bundle without an API, which is
  this task's check.

- [ ] **Step 1: Confirm the installed SushiCore is the checkout**

Run: `python -c "import sushicore.docs_bundle, os; print(os.path.dirname(sushicore.docs_bundle.__file__))"`
Expected: a path under `D:\Projects\sushicore`. If it prints another path, stop and report;
installing a package is the owner's call.

- [ ] **Step 2: Write `docs/publish.toml`**

```toml
name = "sushiruntime"
title = "SushiRuntime"
summary = "The task runtime the SushiStack applications schedule their work on."
sections = ["getting_started", "guides", "architecture", "reference"]
exclude = [
    "reference/API_MAINPAGE.md",
    "reference/CODE_OF_CONDUCT.md",
    "reference/SECURITY.md",
]
api = true
source_url = "https://github.com/SushiSystems/SushiRuntime"
```

The three exclusions are the front page of the Doxygen site and two repository policy pages.
The owner confirms the summary sentence and the exclusions before the commit.

- [ ] **Step 3: Turn the XML on and accept the entry**

In `Doxyfile`, set `GENERATE_XML = YES` (add the line beside `GENERATE_HTML` if the key is
absent; `XML_OUTPUT` keeps its default, `xml`, so the files land in
`build/docs/api-site/xml`). In `tools/documentation/check_docs_layout.py`, add
`"publish.toml"` to `K_DOCS_ENTRIES` exactly as in task 12.

- [ ] **Step 4: Verify without an API build**

Run:

```bash
python tools/documentation/check_docs_layout.py .
python -m sushicore.docs_bundle --release 0.0.0 --out build/docs/bundle-probe
```

Expected: the checker prints nothing new about `publish.toml`. The second command exits 1 with
`docs/publish.toml sets api = true, and this command builds no API reference.`, which proves
the list was read and every page and link passed; a `PageError` here names a real defect in a
page, to be fixed in the page. Then delete `build/docs/bundle-probe`.

- [ ] **Step 5: Changelog and commit**

Add under `## Unreleased` of `docs/reference/CHANGELOG.md`:

```
- 2026-10-07 — docs: Added the publish list and turned on Doxygen's XML output for the documentation bundle (`docs/publish.toml`, `Doxyfile`).
```

```bash
git add docs/publish.toml Doxyfile tools/documentation/check_docs_layout.py docs/reference/CHANGELOG.md
git commit -m "docs: publish the manual and the API reference as a bundle"
```

---

### Task 14: `sr docs` becomes the registered group (SushiRuntime)

**Files (in `D:/Projects/sushiruntime`):**
- Modify: `cli/sushiruntime/cli.py` (the `docs` command at lines 216-223, the alias row at 272)
- Modify: `cli/tests/test_cli.py` (`K_VISIBLE`, one new test), `docs/guides/CLI_GUIDE.md`,
  `docs/reference/CHANGELOG.md`

**Interfaces:**
- Consumes: `sushicore.docs_bundle.ApiSource`, `register_docs_commands`; `project_svc.docs() ->
  int`; `find_project_root() -> Path`.
- Produces: `sr docs`, `sr docs bundle --release X.Y.Z [--out DIR]`, and `sr doxygen` still
  running the API build.

- [ ] **Step 1: Write the failing test**

In `cli/tests/test_cli.py`, add `"docs bundle"` to `K_VISIBLE` after `"docs"`, and append:

```python
def test_docs_runs_the_api_build_and_bundle_is_its_subcommand(monkeypatch, tmp_path):
    """`sr docs` still builds the reference, and `sr docs bundle` asks for a release."""
    monkeypatch.setattr(project, "docs", lambda: 6)
    monkeypatch.setattr(cli, "find_project_root", lambda: tmp_path)
    runner = CliRunner()
    assert runner.invoke(app, ["docs"]).exit_code == 6
    assert runner.invoke(app, ["doxygen"]).exit_code == 6
    assert runner.invoke(app, ["docs", "bundle"]).exit_code == 2
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest cli/tests/test_cli.py -q`
Expected: the catalogue test fails, because `K_VISIBLE` now names `docs bundle` and `sr` has
no such command yet. The new test may pass for the wrong reason at this point: `sr docs bundle`
exits 2 as an unexpected argument. Step 4 is what proves it.

- [ ] **Step 3: Register the group**

In `cli/sushiruntime/cli.py`, add the import
`from sushicore.docs_bundle import ApiSource, register_docs_commands`, delete the `docs`
command (the `@app.command("docs", ...)` block), and put in its place:

```python
K_API_XML = "build/docs/api-site/xml"


def _api_source() -> ApiSource:
    """Returns how `sr` builds the API reference and where Doxygen leaves its XML."""
    return ApiSource(build=project_svc.docs, xml_dir=find_project_root() / K_API_XML)


def _docs_alias() -> None:
    """Builds the API reference; the callback behind the old spelling `sr doxygen`."""
    raise typer.Exit(project_svc.docs())


register_docs_commands(
    app,
    program=PROFILE.program,
    panel=K_PROJECT,
    project_root=find_project_root,
    api=_api_source,
    report=lambda line: console.success(line),
    group_cls=_help_group,
)
```

Change the alias row to `_AliasRow(app, "doxygen", _docs_alias, "sr doxygen"),`.

`project_svc.docs` is read when `_api_source` runs, so the test's `monkeypatch` reaches it.

- [ ] **Step 4: Run SushiRuntime's CLI tests**

Run: `python -m pytest cli/tests -q`, then `sr docs bundle --help` from the repository root.
Expected: every test passes, and the help page lists `--release` and `--out`.
`test_aliases.py::test_doxygen_still_runs_docs` patches the docs
service; if it patched the old `docs` function object in `cli`, repoint it at `project.docs`.

- [ ] **Step 5: Document and commit**

In `docs/guides/CLI_GUIDE.md`, under the `docs` command, add `sr docs bundle --release X.Y.Z`
with its `--out` option, what it writes and where, and a link to
`docs/reference/DOCS_BUNDLE.md` in the SushiCore repository as a code span. Add under
`## Unreleased` of `docs/reference/CHANGELOG.md`:

```
- 2026-10-07 — cli: Added `sr docs bundle` and made `docs` a command group registered from SushiCore (`cli/sushiruntime/cli.py`, `register_docs_commands`).
```

```bash
git add cli/sushiruntime/cli.py cli/tests/test_cli.py cli/tests/test_aliases.py docs/guides/CLI_GUIDE.md docs/reference/CHANGELOG.md
git commit -m "feat(cli): add sr docs bundle"
```

`cli/pyproject.toml` still says `sushicore>=0.7.0`. The floor rises to the SushiCore release
that carries `docs_bundle` in the commit that follows that release; the release is the owner's.

---

### Task 15: The real bundle (acceptance)

**Files:** none changed unless a page has a broken link.

- [ ] **Step 1: Build the bundle**

Run, in `D:/Projects/sushiruntime`: `sr docs bundle --release 1.0.0`
(`1.0.0` is the `version` of `cli/pyproject.toml` on 2026-10-07; use the current one.)
Expected: Doxygen runs, then two lines: the archive path ending in
`build\docs\bundle\docs-bundle-1.0.0.tar.gz (N pages)` and `sha256 <64 hex digits>`.
Doxygen is at `D:\Projects\sushistack\dependencies\tools\doxygen\doxygen.exe` on this machine;
`sr docs` finds it through `doxygen_exe` or `PATH`. If it is not found, report the message and
stop; do not install anything.

- [ ] **Step 2: Inspect it**

```bash
python -c "import tarfile,json,sys; t=tarfile.open(sys.argv[1]); m=json.load(t.extractfile('bundle.json')); print(sorted(m)); print(len(m['pages']), 'pages', len(m['assets']), 'assets', m['api'], m['faq']); print(sum(n.startswith('api/xml/') for n in t.getnames()), 'xml files'); print([n for n in t.getnames() if 'design' in n or 'agent' in n or 'archive' in n])" build/docs/bundle/docs-bundle-1.0.0.tar.gz
```

Expected: the eleven keys of the contract; a page count that matches the published pages; an
`api` object; `faq` is `None` until sub-project 3 writes the FAQ; a non-zero XML count; an empty
list on the last line.

- [ ] **Step 3: Prove the failure path**

Add a line `[gone](NOWHERE.md)` to `docs/guides/INTEGRATION.md`, run
`python -m sushicore.docs_bundle --release 0.0.0 --out build/docs/bundle-probe`, and confirm
exit code 1 with `INTEGRATION.md:<line>: links to NOWHERE.md, which does not exist`. Restore
the file with `git checkout -- docs/guides/INTEGRATION.md` only after confirming with
`git diff --stat` that the added line is its sole change. Delete `build/docs/bundle-probe`.

- [ ] **Step 4: Report**

Write `docs/agent/2026_10_07_DOCS_BUNDLE/REPORT.md` in the SushiCore repository: what each task
changed, the output of every command above, pasted, and what was not done. Update the status
line of `SPEC.md` here and the table in SushiStack's `docs/design/REMAINING_WORK.md`.

---

## Self-review

- **Spec coverage.** SPEC.md section 2: tasks 1 to 8 and 10, one file each. Section 3: task 10's
  `__init__.py`. Section 4: task 10's command tests. Section 5: task 9. Section 6: the limits
  are stated in task 11's reference page; no code. Section 7: task 15. The SushiStack spec's
  4.1 to 4.4: tasks 4, 5, 7, 8; D9: tasks 10 and 14; D10: task 4; the `docs/` tree entry:
  tasks 12 and 13.
- **Not covered here, on purpose.** The release workflow step that attaches the bundle and the
  manifest pull request (sub-project 3). `hub`, `st`, `se`, `sa`, `sb` and `sd` registering the
  group (sub-project 3). The FAQ pages.
- **Counts.** Tests added in SushiCore: 5 + 18 + 4 + 10 + 2 + 6 + 3 + 10 + 1 + 7 + 2 + 3 = 71.
