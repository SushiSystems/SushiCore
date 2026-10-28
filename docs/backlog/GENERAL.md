# General

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-1 | P2 | decision | Correct `AGENTS.md` and name the skills this repository follows | `AGENTS.md` names this repository's own commands and folders and the skills it follows |  |  | 2026-10-19 |
| RW-2 | P2 | decision | Choose a Python-library exception to the layout, or move to it | the layout rule names an exception for a Python library, or `pyproject.toml`, the package and `tests/` follow the rule (Lay L13, Lay L18) |  |  | 2026-10-19 |
| RW-3 | P2 | decision | Keep Python 3.10 or raise the floor to 3.11 | `pyproject.toml` and the test matrix of `.github/workflows/ci.yml` name one floor (Code C18) |  |  | 2026-10-19 |
| RW-4 | P2 | decision | Decide what becomes of the provisioning reviews | the reviews in the untracked `.superpowers/` are written into tracked reports or discarded, and the owner has ruled whether the provisioning, module adoption… |  |  | 2026-10-19 |
| RW-5 | P2 | decision | Choose one policy for a bad appearance value | an unknown `theme`, `icons`, `color` and `background` value is handled the same way (Cli C7) |  |  | 2026-10-19 |
| RW-6 | P2 | decision | Choose how doctor groups are contributed and how `--yes` is spelled | the owner has ruled whether a module contributes its groups through `ModuleProvision` and whether `--yes` takes `-y` here as in `hub` (Cli C16, Cli C17) |  |  | 2026-10-19 |
| RW-7 | P2 | decision | Decide whether the Windows GPU installer is deleted | `source/sushicore/provision/gpu/windows_installer.py` is deleted, or kept with a caller |  | `docs/design/GPU_TOOLKIT_SELECTION/README.md` | 2026-10-19 |
| RW-46 | P2 | decision | Decide how a third-party licence is shown and accepted | the owner has ruled how the oneAPI, winget and CUDA licences reach the user before setup accepts them (Lic L9, Lic L10) |  |  | 2026-10-19 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
