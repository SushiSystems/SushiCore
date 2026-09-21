"""Switches on virtual terminal processing for a Windows console, best effort."""

from __future__ import annotations

import ctypes
import sys

K_STD_OUTPUT_HANDLE = -11
K_STD_ERROR_HANDLE = -12
K_STANDARD_HANDLES = (K_STD_OUTPUT_HANDLE, K_STD_ERROR_HANDLE)
K_ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004


def enable_virtual_terminal(kernel32=None) -> bool:
    """Turn on virtual terminal processing for stdout and stderr and report whether either is on.

    Args:
        kernel32: An object with ``GetStdHandle``, ``GetConsoleMode`` and ``SetConsoleMode``;
            ``default_kernel32()`` when ``None``.

    Returns:
        ``True`` when at least one console handle has the mode on, ``False`` off Windows, when
        every handle is redirected or refused the write, or when the API raised.
    """
    if sys.platform != "win32":
        return False
    try:
        api = kernel32 if kernel32 is not None else default_kernel32()
        turned_on = [_turn_on(api, api.GetStdHandle(which)) for which in K_STANDARD_HANDLES]
    except (OSError, AttributeError):
        return False
    return any(turned_on)


def default_kernel32():
    """Return a private ``kernel32`` whose prototypes keep a 64-bit handle whole.

    Loading its own ``WinDLL`` leaves the prototypes of ``ctypes.windll.kernel32``, which other
    libraries share, untouched.
    """
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetStdHandle.argtypes = [wintypes.DWORD]
    kernel32.GetStdHandle.restype = wintypes.HANDLE
    kernel32.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel32.GetConsoleMode.restype = wintypes.BOOL
    kernel32.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.SetConsoleMode.restype = wintypes.BOOL
    return kernel32


def _turn_on(kernel32, handle) -> bool:
    """Report whether the handle is a console with virtual terminal processing on afterwards."""
    from ctypes import wintypes

    mode = wintypes.DWORD()
    if not kernel32.GetConsoleMode(handle, ctypes.pointer(mode)):
        return False
    if mode.value & K_ENABLE_VIRTUAL_TERMINAL_PROCESSING:
        return True
    return bool(kernel32.SetConsoleMode(handle, mode.value | K_ENABLE_VIRTUAL_TERMINAL_PROCESSING))
