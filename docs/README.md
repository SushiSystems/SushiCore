# SushiCore manual

Every document of this repository outside the agent work folders and the archive is reachable
from this page. The front door is [`README.md`](../README.md).

## Getting started

| Document | Holds |
| --- | --- |
| [Installing](getting_started/INSTALL.md) | The package, its extras, and how to run the tests and the checkers |

## Architecture

| Document | Holds |
| --- | --- |
| [Overview](architecture/OVERVIEW.md) | What each module of the package owns and which way the imports point |

## Guides

| Document | Holds |
| --- | --- |
| [CLI integration](guides/CLI_INTEGRATION.md) | How a Sushi CLI builds its console and registers the shared surfaces |

## Reference

| Document | Holds |
| --- | --- |
| [Configuration](reference/CONFIGURATION.md) | The `[cli]` table, its precedence and the environment variables the package reads |
| [Dependency fragment](reference/DEPENDENCY_FRAGMENT.md) | The keys of a `sushistack.deps.toml` entry, the pinned SHA-256 among them |
| [JSON events](reference/JSON_EVENTS.md) | The event stream a console writes in machine mode |
| [Changelog](reference/CHANGELOG.md) | What changed, by release |
| [Glossary](reference/GLOSSARY.md) | The words these documents use |
| [Known issues](reference/KNOWN_ISSUES.md) | Defects that are recorded and not yet fixed |

## Module READMEs

| Module | Holds |
| --- | --- |
| [`sushicore/provision`](../sushicore/provision/README.md) | The dependency root, `setup`, `doctor`, `link` and `unlink` |
| [`sushicore/ui`](../sushicore/ui/README.md) | The terminal components and the table |
| [`sushicore/help`](../sushicore/help/README.md) | The help screen |

## Design

| Document | Holds |
| --- | --- |
| [Design map](design/README.md) | Which design document covers which topic |
| [Remaining work](design/REMAINING_WORK.md) | The backlog |

## Changing this repository

| Document | Holds |
| --- | --- |
| [Contributing](CONTRIBUTING.md) | How a change lands and what it must carry |
| [Documentation style guide](DOCUMENTATION_STYLE_GUIDE.md) | How prose is written here |
| [Agent instructions](../AGENTS.md) | The agent instruction file at the repository root; see [Known issues](reference/KNOWN_ISSUES.md) |

Agent work folders are under `agent/`. Finished material is under `archive/` and is not edited.
