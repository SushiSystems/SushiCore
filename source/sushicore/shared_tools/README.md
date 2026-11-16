# sushicore.shared_tools

Copies the shared `tools/` of a SushiCore release tag into a repository and records them in
a lock file under `tools/`. The commands, the exit codes and the lock are in
[Shared tools](../../../docs/reference/SHARED_TOOLS.md).

## What it owns

| Name | File | Does |
| --- | --- | --- |
| `SharedToolsError` and its subclasses | `errors.py` | The failures the commands report as one line |
| `GitReader`, `tracked_files` | `git_reader.py` | Read a tag's files, history and commit through git |
| `find_checkout` | `checkout_finder.py` | `--from`, the sibling, or the fetched copy |
| `LicenceToolkit`, `load_toolkit` | `licence_toolkit.py` | Load the tag's own license block writer |
| `HeaderMerger` | `header_merger.py` | Put a shared file under the repository's license header |
| `SharedToolsLock`, `read_lock` | `lock_file.py` | Write, read and compare the lock |
| `read_pre_move_digests`, `is_pre_move_copy` | `pre_move_digests.py`, `pre_move_digests.toml` | The frozen digests of the files SushiSkills held before the move; such a file is stale, not a local edit |
| `write_digests` | `pre_move_digest_writer.py` | Wrote the frozen digest file once; not run again |
| `SharedToolsSync`, `K_EXCLUDED` | `sync_service.py` | The sync itself |
| `register_shared_tools_commands`, `main` | `commands.py`, `__main__.py` | The `sync` and `check` commands |

## What it depends on

`sushicore.errors`, `sushicore.workspace.read_toml` and `sushicore.provision.sushi_sources.resolve`.
`commands.py` imports Typer inside `register_shared_tools_commands`.
