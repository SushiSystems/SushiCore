# test_windows_console.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Virtual terminal processing is switched on per console handle, and never through the real API."""

import ctypes
import sys

import pytest

from sushicore import windows_console
from sushicore.windows_console import enable_virtual_terminal


K_VT = 0x0004
K_STDOUT = -11
K_STDERR = -12


class FakeKernel32:
    """Stand in for kernel32: hand out handles, hold one mode per handle, record every write."""

    def __init__(self, modes, refuse_set=(), raises=None):
        """Bind the mode of each handle; a handle absent from ``modes`` is not a console."""
        self.modes = dict(modes)
        self.refuse_set = set(refuse_set)
        self.raises = raises
        self.handles_asked = []
        self.written = []

    def GetStdHandle(self, which):
        """Return a handle named after the standard handle asked for."""
        if self.raises is not None:
            raise self.raises
        self.handles_asked.append(which)
        return {K_STDOUT: 1001, K_STDERR: 1002}[which]

    def GetConsoleMode(self, handle, pointer):
        """Write the handle's mode through the pointer, or fail when it is not a console."""
        if handle not in self.modes:
            return 0
        pointer.contents.value = self.modes[handle]
        return 1

    def SetConsoleMode(self, handle, mode):
        """Record the write and succeed unless the handle is on the refuse list."""
        self.written.append((handle, mode))
        return 0 if handle in self.refuse_set else 1


@pytest.mark.small
def test_both_handles_are_turned_on_with_their_old_mode_or_the_bit():
    fake = FakeKernel32({1001: 0x0003, 1002: 0x0001})
    assert enable_virtual_terminal(fake, "win32") is True
    assert fake.written == [(1001, 0x0003 | K_VT), (1002, 0x0001 | K_VT)]


@pytest.mark.small
def test_a_handle_with_the_bit_already_set_is_not_written_but_counts_as_on():
    fake = FakeKernel32({1001: 0x0003 | K_VT, 1002: 0x0003 | K_VT})
    assert enable_virtual_terminal(fake, "win32") is True
    assert fake.written == []


@pytest.mark.small
def test_a_redirected_handle_is_skipped_and_the_other_still_counts():
    fake = FakeKernel32({1002: 0x0003})
    assert enable_virtual_terminal(fake, "win32") is True
    assert fake.written == [(1002, 0x0003 | K_VT)]


@pytest.mark.small
def test_two_redirected_handles_give_false():
    fake = FakeKernel32({})
    assert enable_virtual_terminal(fake, "win32") is False
    assert fake.written == []


@pytest.mark.small
def test_a_refused_write_does_not_count_as_on():
    fake = FakeKernel32({1001: 0x0003, 1002: 0x0003}, refuse_set={1001, 1002})
    assert enable_virtual_terminal(fake, "win32") is False
    assert len(fake.written) == 2


@pytest.mark.small
def test_an_os_error_from_the_api_gives_false():
    fake = FakeKernel32({1001: 0x0003}, raises=OSError("no console"))
    assert enable_virtual_terminal(fake, "win32") is False


@pytest.mark.small
def test_a_missing_function_gives_false():
    assert enable_virtual_terminal(object(), "win32") is False


@pytest.mark.small
def test_off_windows_nothing_is_called_and_the_result_is_false():
    fake = FakeKernel32({1001: 0x0003, 1002: 0x0003})
    assert enable_virtual_terminal(fake, "linux") is False
    assert fake.handles_asked == [] and fake.written == []


@pytest.mark.medium
@pytest.mark.skipif(sys.platform != "win32", reason="kernel32 exists only on Windows")
def test_the_default_kernel32_declares_a_pointer_wide_handle():
    """Build the default kernel32 and read its prototypes; no Win32 function is called."""
    from ctypes import wintypes

    kernel32 = windows_console.default_kernel32()
    assert kernel32.GetStdHandle.restype is wintypes.HANDLE
    assert ctypes.sizeof(kernel32.GetStdHandle.restype) == ctypes.sizeof(ctypes.c_void_p)
    assert kernel32.GetStdHandle.argtypes == [wintypes.DWORD]
    assert kernel32.GetConsoleMode.argtypes == [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    assert kernel32.SetConsoleMode.argtypes == [wintypes.HANDLE, wintypes.DWORD]
