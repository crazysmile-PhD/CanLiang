"""Utilities for locating Windows GUI processes."""
from __future__ import annotations

import logging
import os
from typing import Callable, Iterable, List, Optional, Sequence, Tuple

import psutil
import win32api
import win32con
import win32gui
import win32process

logger = logging.getLogger(__name__)

EnumWindows = Callable[[Callable[[int, List[int]], bool], List[int]], None]

_DEFAULT_BLACKLIST = {
    "dwm.exe",
    "winlogon.exe",
    "csrss.exe",
    "explorer.exe",
    "svchost.exe",
    "lsass.exe",
    "smss.exe",
    "wininit.exe",
    "services.exe",
    "spoolsv.exe",
    "conhost.exe",
    "dllhost.exe",
    "rundll32.exe",
    "taskhostw.exe",
    "sihost.exe",
    "ctfmon.exe",
    "fontdrvhost.exe",
    "lsm.exe",
    "nvidia overlay.exe",
    "textinputhost.exe",
}


class WindowFinder:
    """Find windows by process name and enumerate candidates."""

    def __init__(
        self,
        enum_windows: EnumWindows = win32gui.EnumWindows,
        is_window_visible: Callable[[int], bool] = win32gui.IsWindowVisible,
        get_window_thread_process_id: Callable[[int], Tuple[int, int]] = win32process.GetWindowThreadProcessId,
        open_process: Callable[[int, bool, int], int] = win32api.OpenProcess,
        close_handle: Callable[[int], None] = win32api.CloseHandle,
        get_module_file_name_ex: Callable[[int, int], str] = win32process.GetModuleFileNameEx,
        get_window_rect: Callable[[int], Tuple[int, int, int, int]] = win32gui.GetWindowRect,
        psutil_module=psutil,
        system_processes: Optional[Sequence[str]] = None,
    ) -> None:
        self._enum_windows = enum_windows
        self._is_window_visible = is_window_visible
        self._get_window_thread_process_id = get_window_thread_process_id
        self._open_process = open_process
        self._close_handle = close_handle
        self._get_module_file_name_ex = get_module_file_name_ex
        self._get_window_rect = get_window_rect
        self._psutil = psutil_module
        self._blacklist = {p.lower() for p in (system_processes or _DEFAULT_BLACKLIST)}

    def find(self, process_name: str) -> int:
        """Return the first window handle that matches ``process_name``."""

        process_name = process_name.lower()
        for hwnd, name in self.iter_visible_windows():
            if name == process_name:
                logger.debug("找到匹配的进程: %s, 窗口句柄: %s", name, hwnd)
                return hwnd
        logger.warning("未找到进程 %s 的窗口", process_name)
        return 0

    def list_visible_programs(self) -> List[str]:
        """Return sorted candidate program names for streaming."""

        programs: List[str] = []
        for hwnd, process_name in self.iter_visible_windows():
            if self._is_candidate(hwnd, process_name):
                programs.append(process_name)
        unique = sorted(set(programs))
        logger.debug("扫描完成，找到 %s 个可推流的程序: %s", len(unique), unique)
        return unique

    def iter_visible_windows(self) -> Iterable[Tuple[int, str]]:
        """Yield visible window handles and their process names."""

        handles: List[int] = []

        def collect(hwnd: int, acc: List[int]) -> bool:
            if self._is_window_visible(hwnd):
                acc.append(hwnd)
            return True

        self._enum_windows(collect, handles)
        for hwnd in handles:
            name = self._process_name(hwnd)
            if name:
                yield hwnd, name

    # helpers -----------------------------------------------------------------

    def _process_name(self, hwnd: int) -> Optional[str]:
        try:
            _thread_id, pid = self._get_window_thread_process_id(hwnd)
            process_handle = None
            try:
                process_handle = self._open_process(win32con.PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
                process_path = self._get_module_file_name_ex(process_handle, 0)
                return os.path.basename(process_path).lower()
            except Exception:
                try:
                    process_handle = self._open_process(
                        win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ,
                        False,
                        pid,
                    )
                    process_path = self._get_module_file_name_ex(process_handle, 0)
                    return os.path.basename(process_path).lower()
                except Exception:
                    try:
                        process = self._psutil.Process(pid)
                        return process.name().lower()
                    except Exception:
                        logger.debug("无法访问进程信息 pid=%s", pid)
                        return None
            finally:
                if process_handle:
                    self._close_handle(process_handle)
        except Exception as exc:
            logger.debug("枚举窗口时发生错误: %s", exc)
            return None

    def _is_candidate(self, hwnd: int, process_name: str) -> bool:
        if not process_name.endswith(".exe"):
            return False
        if process_name in self._blacklist:
            return False
        if process_name.startswith("windows") or process_name.startswith("microsoft"):
            return False
        try:
            left, top, right, bottom = self._get_window_rect(hwnd)
            width, height = right - left, bottom - top
            return width > 0 and height > 0
        except Exception:
            return True
