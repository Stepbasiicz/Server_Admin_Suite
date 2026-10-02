# -*- coding: utf-8 -*-
"""
Single-Instance Application Lock for Windows.
Prevents multiple instances using Windows Named Mutex and brings existing window to focus.
"""

import sys
import os
import ctypes
from typing import Optional

MUTEX_NAME = "Global\\Soft4UApp_ServerAdminSuite_SingleInstance_Mutex_2026"


class SingleInstanceLock:
    """Manages single-instance execution via Windows Named Mutex."""

    def __init__(self, mutex_name: str = MUTEX_NAME):
        self.mutex_name = mutex_name
        self.mutex_handle = None
        self.is_already_running = False

    def acquire(self) -> bool:
        """
        Attempt to create/acquire mutex.
        Returns True if this is the ONLY running instance, False if another is already open.
        """
        if sys.platform != "win32":
            return True

        try:
            ERROR_ALREADY_EXISTS = 183
            kernel32 = ctypes.windll.kernel32
            self.mutex_handle = kernel32.CreateMutexW(None, False, self.mutex_name)
            last_error = kernel32.GetLastError()

            if last_error == ERROR_ALREADY_EXISTS:
                self.is_already_running = True
                self._bring_existing_to_front()
                return False

            return True
        except Exception:
            return True

    def _bring_existing_to_front(self):
        """Find existing window by title and bring to foreground."""
        try:
            from version import APP_TITLE
            user32 = ctypes.windll.user32
            hwnd = user32.FindWindowW(None, APP_TITLE)
            if hwnd:
                SW_RESTORE = 9
                user32.ShowWindow(hwnd, SW_RESTORE)
                user32.SetForegroundWindow(hwnd)
        except Exception:
            pass

    def release(self):
        """Release mutex upon application exit."""
        if self.mutex_handle and sys.platform == "win32":
            try:
                ctypes.windll.kernel32.CloseHandle(self.mutex_handle)
            except Exception:
                pass
            self.mutex_handle = None
