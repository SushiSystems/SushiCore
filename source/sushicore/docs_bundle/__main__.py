# __main__.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
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
