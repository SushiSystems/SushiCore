"""Snapshotting the environment a build runs under.

A parent process cannot ``call vcvars64.bat`` and inherit the result: the batch
file sets its variables in its own shell, which then exits. So the shell is run
as a child, its environment is dumped and parsed, and that dictionary is handed
to every cmake/ctest subprocess. The snapshot is cached on disk keyed by the
configuration that produced it, so an unchanged config skips the shell entirely.

The primitives below are the parts that are the same wherever this is done.
:class:`StackBuildEnv` composes them the way a module that *consumes* the shared
toolchain needs; SushiRuntime, which *selects* one, composes them itself.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Mapping, Sequence


def merge_env(base: Mapping[str, str], overlay: Mapping[str, str]) -> dict[str, str]:
    """Merge *overlay* into *base*, prepending PATH into the base's case variant.

    PATH is collapsed into the *single* case variant the base already uses (for
    instance Windows' "Path"). Writing the overlay's "PATH" as a new key while
    base keeps "Path" leaves two conflicting entries; Windows then honours only
    one of them for child processes, so toolchain directories added to the other
    silently vanish from DLL and executable resolution.
    """
    merged = dict(base)
    path_key = next((k for k in merged if k.upper() == "PATH"), None)
    for k, v in overlay.items():
        if k.upper() == "PATH":
            target = path_key or k
            existing = merged.get(target, "")
            merged[target] = v + os.pathsep + existing if existing else v
            path_key = target
        else:
            merged[k] = v
    return merged


def prepend_path(env: dict[str, str], var: str, dirs: Sequence[str]) -> None:
    """Prepend *dirs* to the (case-insensitive) *var* path entry of *env*."""
    if not dirs:
        return
    key = next((k for k in env if k.upper() == var.upper()), var)
    existing = env.get(key, "")
    env[key] = os.pathsep.join(list(dirs) + ([existing] if existing else []))


def parse_windows_set(output: str) -> dict[str, str]:
    """Parse the KEY=VALUE lines that cmd.exe's ``set`` prints."""
    env: dict[str, str] = {}
    for line in output.splitlines():
        key, sep, value = line.partition("=")
        if sep and key:
            env[key] = value
    return env


def snapshot_windows(cfg, console) -> dict[str, str] | None:
    """Run vcvars64 in a child shell and return the environment it produced.

    None when no vcvars is configured or it fails, which callers treat as "use
    the current environment" rather than an error: a machine with MSVC already
    on PATH needs no snapshot.
    """
    vcvars = cfg.expand(cfg.vs_vcvars)
    if not (vcvars and Path(vcvars).is_file()):
        return None
    console.info("Loading Visual Studio environment (vcvars64)...")
    # Pass the whole command as a single string, NOT as ["cmd", "/c", script]:
    # with a list, subprocess re-quotes each element and mangles the inner quotes
    # around the (space-containing) vcvars path, so cmd.exe sees the quoted path
    # as one unknown token and returns non-zero -- silently dropping the VS
    # environment.
    script = 'cmd /c call "' + vcvars + '" && set'
    result = subprocess.run(script, capture_output=True, text=True)
    if result.returncode != 0:
        console.warn("vcvars64 returned non-zero; using current env.")
        return None
    return parse_windows_set(result.stdout)


def read_cache(cache_file: Path, key: str) -> dict[str, str] | None:
    """The cached snapshot when it was produced by *key*, else None."""
    if not cache_file.is_file():
        return None
    try:
        cached = json.loads(cache_file.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(cached, dict) or cached.get("key") != key:
        return None
    env = cached.get("env")
    return env if isinstance(env, dict) else None


def write_cache(cache_file: Path, key: str, env: Mapping[str, str]) -> None:
    """Store *env* under *key*. Failing to write is not failing to build."""
    try:
        cache_file.write_text(json.dumps({"key": key, "env": dict(env)}))
    except OSError:
        pass


class StackBuildEnv:
    """The build environment for a module that consumes the shared toolchain.

    SushiEngine, SushiAI and SushiBLAS each carried a copy of this. Stripped of
    comments the three were the same code but for one expression -- the cache
    key, which lists the sibling checkouts -- and those the profile already
    names. So even the one difference was not one.

    @param profile    Supplies the siblings that belong in the cache key.
    @param console    The CLI's console module.
    @param find_root  The CLI's project-root resolver.
    @param cache_name Filename of the on-disk snapshot, inside the build dir.
    """

    __slots__ = ("_profile", "_console", "_find_root", "_cache_name")

    def __init__(self, *, profile, console, find_root,
                 cache_name: str = ".sushi_env.json") -> None:
        self._profile = profile
        self._console = console
        self._find_root = find_root
        self._cache_name = cache_name

    def cache_key(self, cfg) -> str:
        """Hash of everything that would change the snapshot.

        The sibling directories are in here because moving one changes which
        toolchain bundle gets injected. They come from the profile rather than
        being listed again, which is exactly where the three copies differed.
        """
        material = {"platform": cfg.platform, "vs_vcvars": cfg.vs_vcvars}
        for name in self._profile.siblings:
            material[name + "_dir"] = getattr(cfg, name + "_dir", "")
        return hashlib.sha256(
            json.dumps(material, sort_keys=True).encode()
        ).hexdigest()

    def inject_toolchain(self, cfg, env: dict[str, str]) -> None:
        """Add the shared bundled clang++ bin/lib to a build or run environment.

        Neither platform ships a system SYCL compiler: these modules build with
        the intel/llvm clang++ provisioned into the shared SushiStack dependency
        tree, so that bin must be on PATH -- and on Linux its lib on
        LD_LIBRARY_PATH -- for the compiler and its SYCL runtime libraries to
        resolve at build and run time.
        """
        try:
            root = self._find_root()
        except SystemExit:
            return
        bundle = cfg.deps_dir(root) / "toolchains" / "llvm-sycl"
        if (bundle / "bin").is_dir():
            prepend_path(env, "PATH", [str(bundle / "bin")])
        if not cfg.is_windows and (bundle / "lib").is_dir():
            prepend_path(env, "LD_LIBRARY_PATH", [str(bundle / "lib")])

        # On Windows the runtime DLL pulls in vcpkg-installed dependencies
        # (hwloc), so the vcpkg installed bin must be on PATH for the runtime
        # DLL to load.
        if cfg.is_windows:
            vcpkg = cfg.resolved_vcpkg(root)
            if vcpkg:
                vcpkg_bin = Path(vcpkg) / "installed" / cfg.vcpkg_triplet / "bin"
                if vcpkg_bin.is_dir():
                    prepend_path(env, "PATH", [str(vcpkg_bin)])

    def load(self, cfg, build_dir: Path) -> dict[str, str]:
        """Return the environment for build, test and run subprocesses.

        Falls back to the current ``os.environ`` when no toolchain script is
        configured: a machine with clang++ and MSVC already on PATH needs no
        snapshot, and that is not an error.
        """
        build_dir.mkdir(parents=True, exist_ok=True)
        cache_file = build_dir / self._cache_name
        key = self.cache_key(cfg)

        cached = read_cache(cache_file, key)
        if cached is not None:
            env = merge_env(os.environ, cached)
            self.inject_toolchain(cfg, env)
            return env

        snapshot = snapshot_windows(cfg, self._console) if cfg.is_windows else None
        if not snapshot:
            env = dict(os.environ)
            self.inject_toolchain(cfg, env)
            return env

        write_cache(cache_file, key, snapshot)
        env = merge_env(os.environ, snapshot)
        self.inject_toolchain(cfg, env)
        return env
