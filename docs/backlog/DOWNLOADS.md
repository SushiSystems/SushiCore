# Downloads

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-44 | P2 | open | Pin a version and a digest for every download | every download in `base.deps.toml` and the fragments, `git` and `doxygen` among them, has a version key and a `sha256` (Code C6) |  |  | 2026-10-19 |
| RW-45 | P2 | open | Verify shell pipelines and clones | the oneAPI apt key and the vcpkg, AdaptiveCpp and Unified Runtime clones are checked against a pinned key or commit (Code C6) |  |  | 2026-10-19 |
| RW-105 | P2 | open | Pin the LLVM 17.0.6 installer and the oneAPI offline installer | base.deps.toml pins both with a version, a url and a digest from a published checksum or a reviewed hash |  | `source/sushicore/provision/toolchains/oneapi.py` | 2026-11-17 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
| KI-17 | dependency | ROCm SDK tarballs are used unverified | none |  | `source/sushicore/provision/gpu/rocm_toolkit_installer.py` | 2026-10-19 |
