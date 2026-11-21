# Downloads

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-105 | P2 | open | Pin the LLVM 17.0.6 installer and the oneAPI offline installer | base.deps.toml pins both with a version, a url and a digest from a published checksum or a reviewed hash |  | `source/sushicore/provision/toolchains/oneapi.py` | 2026-11-17 |
| RW-124 | P2 | open | Confirm the oneAPI apt key fingerprint against Intel's published value | the fingerprint in base.deps.toml matches a value Intel publishes |  | `source/sushicore/provision/manifests/base.deps.toml` | 2026-11-17 |
| RW-154 | P2 | open | Pin the intel/llvm bundle to a release whose assets are never re-uploaded | The intel-llvm entry names a release whose digests a later fetch still matches, and a drifted digest is told apart from a corrupt download |  | `source/sushicore/provision/manifests/base.deps.toml` | 2026-11-21 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
| KI-17 | dependency | ROCm SDK tarballs are used unverified | none |  | `source/sushicore/provision/gpu/rocm_toolkit_installer.py` | 2026-10-19 |
