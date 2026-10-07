# user_environment.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Reads and writes the user's persistent environment variables.

Windows keeps them in the registry under ``HKEY_CURRENT_USER\\Environment``. Elsewhere they are
``export`` lines in one managed block of ``~/.profile``.
"""

from __future__ import annotations

import os
import re
from contextlib import closing
from pathlib import Path
from typing import Callable, Protocol, final

_IS_WINDOWS = os.name == "nt"

#: The registry key under ``HKEY_CURRENT_USER`` that holds the user's variables.
_REGISTRY_KEY = "Environment"

#: The first and last line of the block this module owns in a profile file.
BLOCK_BEGIN = "# sushisystems environment: begin"
BLOCK_END = "# sushisystems environment: end"

_EXPORT_LINE = re.compile(r'^export ([A-Za-z_][A-Za-z0-9_]*)="(.*)"$')
_ESCAPED = re.compile(r'\\([\\"$`])')
_NEEDS_ESCAPE = re.compile(r'([\\"$`])')


class EnvironmentKey(Protocol):
    """The opened registry key a :class:`RegistryEnvironment` reads and writes."""

    def query(self, name: str) -> str | None:
        """Return the value stored under *name*, or None when there is none."""

    def set(self, name: str, value: str) -> None:
        """Store *value* under *name*."""

    def delete(self, name: str) -> None:
        """Delete *name*; a name that is absent is not an error."""

    def close(self) -> None:
        """Release the key."""


class UserEnvironment(Protocol):
    """A store of the variables every new process of the user starts with."""

    def read(self, name: str) -> str | None:
        """Return the stored value of *name*, or None when it is not set."""

    def write(self, name: str, value: str) -> None:
        """Set *name* to *value* for processes started from now on."""

    def remove(self, name: str) -> None:
        """Unset *name* for processes started from now on."""


@final
class RegistryEnvironment:
    """Keeps the user's variables in the Windows registry."""

    def __init__(
        self,
        open_key: Callable[[], EnvironmentKey] | None = None,
        broadcast: Callable[[], None] | None = None,
    ) -> None:
        """Bind the store to a key opener and to the call that announces a change.

        Args:
            open_key: Opens the key for reading and writing; the user's real key when None.
            broadcast: Tells running programs the environment changed; the real
                ``WM_SETTINGCHANGE`` broadcast when None.
        """
        self._open_key = open_key or _open_user_key
        self._broadcast = broadcast or _broadcast_setting_change

    def read(self, name: str) -> str | None:
        """Return the stored value of *name*, or None when it is not set."""
        with closing(self._open_key()) as key:
            return key.query(name)

    def write(self, name: str, value: str) -> None:
        """Set *name* to *value* and announce the change."""
        with closing(self._open_key()) as key:
            key.set(name, value)
        self._broadcast()

    def remove(self, name: str) -> None:
        """Unset *name* and announce the change."""
        with closing(self._open_key()) as key:
            key.delete(name)
        self._broadcast()


@final
class ProfileEnvironment:
    """Keeps the user's variables as ``export`` lines in one block of a profile file."""

    def __init__(self, path: Path | None = None) -> None:
        """Bind the store to *path*, ``~/.profile`` when None."""
        self._path = path or Path.home() / ".profile"

    def read(self, name: str) -> str | None:
        """Return the stored value of *name*, or None when it is not set."""
        return self._load()[1].get(name)

    def write(self, name: str, value: str) -> None:
        """Set *name* to *value*, replacing the line that already sets it."""
        before, variables, after = self._load()
        variables[name] = value
        self._store(before, variables, after)

    def remove(self, name: str) -> None:
        """Unset *name*, and drop the block with its markers when it holds nothing."""
        before, variables, after = self._load()
        if variables.pop(name, None) is not None:
            self._store(before, variables, after)

    def _load(self) -> tuple[list[str], dict[str, str], list[str]]:
        """Return the lines before the block, the block's variables and the lines after."""
        if not self._path.is_file():
            return [], {}, []
        lines = self._path.read_text(encoding="utf-8").splitlines()
        if BLOCK_BEGIN not in lines:
            return lines, {}, []
        begin = lines.index(BLOCK_BEGIN)
        end = lines.index(BLOCK_END, begin) if BLOCK_END in lines[begin:] else len(lines)
        variables: dict[str, str] = {}
        for line in lines[begin + 1:end]:
            match = _EXPORT_LINE.match(line)
            if match:
                variables[match.group(1)] = _ESCAPED.sub(r"\1", match.group(2))
        return lines[:begin], variables, lines[end + 1:]

    def _store(self, before: list[str], variables: dict[str, str], after: list[str]) -> None:
        """Write the file back with the block rebuilt from *variables*."""
        block: list[str] = []
        if variables:
            exports = [_export_line(name, value) for name, value in variables.items()]
            block = [BLOCK_BEGIN, *exports, BLOCK_END]
        lines = [*before, *block, *after]
        text = "\n".join(lines) + "\n" if lines else ""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(text, encoding="utf-8", newline="\n")


def _export_line(name: str, value: str) -> str:
    """Return the ``export`` line that sets *name* to *value* inside double quotes."""
    escaped = _NEEDS_ESCAPE.sub(r"\\\1", value)
    return f'export {name}="{escaped}"'


def default_environment() -> UserEnvironment:
    """Return the store this platform keeps the user's variables in."""
    return RegistryEnvironment() if _IS_WINDOWS else ProfileEnvironment()


def read_user_variable(name: str, store: UserEnvironment | None = None) -> str | None:
    """Return the user's persistent value of *name*, or None when it is not set.

    Args:
        store: Where to read; :func:`default_environment` when None.
    """
    return (store or default_environment()).read(name)


def write_user_variable(name: str, value: str, store: UserEnvironment | None = None) -> None:
    """Set the user's persistent variable *name* to *value*.

    Args:
        store: Where to write; :func:`default_environment` when None.
    """
    (store or default_environment()).write(name, value)


def remove_user_variable(name: str, store: UserEnvironment | None = None) -> None:
    """Unset the user's persistent variable *name*.

    Args:
        store: Where to write; :func:`default_environment` when None.
    """
    (store or default_environment()).remove(name)


@final
class _WinregKey:
    """Adapts an opened ``winreg`` key to :class:`EnvironmentKey`."""

    def __init__(self) -> None:
        """Open ``HKEY_CURRENT_USER\\Environment`` for reading and writing."""
        import winreg
        self._winreg = winreg
        self._key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REGISTRY_KEY, 0,
            winreg.KEY_READ | winreg.KEY_SET_VALUE,
        )

    def query(self, name: str) -> str | None:
        """Return the value stored under *name*, or None when there is none."""
        try:
            value, _kind = self._winreg.QueryValueEx(self._key, name)
        except FileNotFoundError:
            return None
        return str(value)

    def set(self, name: str, value: str) -> None:
        """Store *value* under *name* as a plain string."""
        self._winreg.SetValueEx(self._key, name, 0, self._winreg.REG_SZ, value)

    def delete(self, name: str) -> None:
        """Delete *name*; a name that is absent is not an error."""
        try:
            self._winreg.DeleteValue(self._key, name)
        except FileNotFoundError:
            return

    def close(self) -> None:
        """Release the key."""
        self._winreg.CloseKey(self._key)


def _open_user_key() -> EnvironmentKey:
    """Open the registry key that holds the user's variables."""
    return _WinregKey()


def _broadcast_setting_change() -> None:
    """Send ``WM_SETTINGCHANGE`` to every top-level window, waiting at most five seconds."""
    import ctypes
    hwnd_broadcast, wm_settingchange, smto_abortifhung = 0xFFFF, 0x001A, 0x0002
    result = ctypes.c_size_t()
    ctypes.windll.user32.SendMessageTimeoutW(
        hwnd_broadcast, wm_settingchange, 0, _REGISTRY_KEY,
        smto_abortifhung, 5000, ctypes.byref(result),
    )
