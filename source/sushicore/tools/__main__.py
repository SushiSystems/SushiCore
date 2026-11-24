# __main__.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Runs the shared tools on a repository: `python -m sushicore.tools`.

Usage: python -m sushicore.tools check [ROOT] [--skip-history]
       python -m sushicore.tools install-hooks [ROOT]
"""

from __future__ import annotations

import sys
from collections.abc import Sequence

K_USAGE = "usage: python -m sushicore.tools check [ROOT] [--skip-history] | install-hooks [ROOT]"
K_EXIT_USAGE = 2


def main(argv: Sequence[str] | None = None) -> int:
    """Runs one command and returns its exit code."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments or arguments[0] not in ("check", "install-hooks"):
        sys.stderr.write(f"{K_USAGE}\n")
        return K_EXIT_USAGE
    if arguments[0] == "check":
        from .check_all import main as check
        return check(arguments[1:])
    from .hooks.install_hooks import main as install
    return install(arguments[1:])


if __name__ == "__main__":
    sys.exit(main())
