# Release train

Releases a chain of Sushi libraries in dependency order. A library pins the libraries below it in
`cli/sushistack.deps.toml`; when one of them is released, each library above it is released after it
with that pin moved.

| Name | File | Does |
| --- | --- | --- |
| `LibraryGraph` | `library_graph.py` | Read which library pins which from the workspace and order a train so each library follows what it pins |
| `Version` | `version.py` | Parse a MAJOR.MINOR.PATCH version and give the next one |
| `bump_text` | `version_text.py` | Rewrite the version a file declares, dotted or as one macro per part |
| `close_changelog` | `changelog_section.py` | Turn the Unreleased section into the section of a release and drop older ones |
| `pin_in_deps`, `pin_in_workflow` | `pin_text.py` | Point a library's pin at a new tag in the pins file and in a workflow |
| `IGit`, `IForge`, `IPackageIndex` | `ports.py` | The seams to git, to the forge that runs CI and to the package index |
| `GitCli` | `git_cli.py` | The git operations through the git command |
| `GhForge` | `gh_forge.py` | Wait for the CI and release workflows of a commit through the gh command |
| `PyPiIndex` | `pypi_index.py` | Wait for a version of a package on PyPI |
| `ReleaseTrain` | `release_train.py` | Walk the train: pin what moved below, bump the version files, close the changelog, wait for CI, tag, wait for the release and the index |
| `ReleaseTrainError` | `errors.py` | A step that failed, naming the library and the step |

The version files of a library are the files its last `chore(release)` commit changed.
