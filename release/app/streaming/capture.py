"""Frame capture utilities abstracted behind a class for dependency injection."""
from __future__ import annotations

import ctypes
import logging
from typing import Dict, Iterable, Tuple

import cv2
import numpy as np
import win32api
import win32con
import win32gui
import win32ui

logger = logging.getLogger(__name__)

Mask = Tuple[Tuple[int, int], Tuple[int, int]]

_DEFAULT_MASKS: Dict[str, Iterable[Mask]] = {
    "yuanshen.exe": (
        ((222, 374), (583, 448)),
        ((3346, 2087), (3731, 2149)),
    ),
}


class FrameCapture:
    """Capture frames from the desktop or a specific window."""

    def __init__(
        self,
        *,
        mask_rules: Dict[str, Iterable[Mask]] | None = None,
        get_desktop_window=win32gui.GetDesktopWindow,
        np_module=np,
        cv2_module=cv2,
        sleep_resolution: Tuple[int, int, int] = (480, 640, 3),
    ) -> None:
        self._get_desktop_window = get_desktop_window
        self._masks = mask_rules or _DEFAULT_MASKS
        self._np = np_module
        self._cv2 = cv2_module
        self._fallback_shape = sleep_resolution

    # public API --------------------------------------------------------------

    def capture(self, hwnd: int, target_app: str | None = None) -> np.ndarray:
        try:
            if hwnd == self._get_desktop_window():
                return self._capture_desktop()
            return self._capture_window(hwnd, target_app)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("捕获窗口时发生错误: %s", exc)
            return self.blank_frame()

    # internal helpers --------------------------------------------------------

    def _capture_desktop(self) -> np.ndarray:
        try:
            self._set_dpi_awareness()
            screen_width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
            screen_height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
            screen_left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
            screen_top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)

            if screen_width == 0 or screen_height == 0:
                screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
                screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
                screen_left = 0
                screen_top = 0

            desktop_dc = win32gui.GetDC(0)
            img_dc = win32ui.CreateDCFromHandle(desktop_dc)
            mem_dc = img_dc.CreateCompatibleDC()
            screenshot = win32ui.CreateBitmap()
            screenshot.CreateCompatibleBitmap(img_dc, screen_width, screen_height)
            mem_dc.SelectObject(screenshot)
            mem_dc.BitBlt((0, 0), (screen_width, screen_height), img_dc, (screen_left, screen_top), win32con.SRCCOPY)
            bmpstr = screenshot.GetBitmapBits(True)
            img = self._np.frombuffer(bmpstr, dtype="uint8")
            img.shape = (screen_height, screen_width, 4)
            img = self._cv2.cvtColor(img, self._cv2.COLOR_BGRA2BGR)
            mem_dc.DeleteDC()
            img_dc.DeleteDC()
            win32gui.ReleaseDC(0, desktop_dc)
            win32gui.DeleteObject(screenshot.GetHandle())
            return img
        except Exception as exc:
            logger.error("捕获桌面时发生错误: %s", exc)
            return self.blank_frame()

    def _capture_window(self, hwnd: int, target_app: str | None) -> np.ndarray:
        if not hwnd:
            logger.warning("窗口句柄无效（为空或0）")
            return self.blank_frame()
        if not win32gui.IsWindow(hwnd):
            logger.warning("窗口句柄 %s 不是有效的窗口", hwnd)
            return self.blank_frame()
        if not win32gui.IsWindowVisible(hwnd):
            logger.warning("窗口句柄 %s 对应的窗口不可见", hwnd)
            return self.blank_frame()

        try:
            self._set_dpi_awareness()
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width, height = right - left, bottom - top
            if width <= 0 or height <= 0:
                logger.warning("窗口尺寸无效: %sx%s", width, height)
                return self.blank_frame()

            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(save_bitmap)
            save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)
            bmpstr = save_bitmap.GetBitmapBits(True)
            img = self._np.frombuffer(bmpstr, dtype="uint8")
            img.shape = (height, width, 4)
            img = self._cv2.cvtColor(img, self._cv2.COLOR_BGRA2BGR)

            if target_app:
                self._apply_masks(target_app.lower(), img)

            win32gui.DeleteObject(save_bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)
            return img
        except Exception as exc:
            logger.error("捕获普通窗口时发生错误: %s", exc)
            return self.blank_frame()

    def _apply_masks(self, target_app: str, img: np.ndarray) -> None:
        masks = self._masks.get(target_app)
        if not masks:
            return
        height, width = img.shape[:2]
        base_width, base_height = 3840, 2160
        scale_x = width / base_width
        scale_y = height / base_height
        for (x1, y1), (x2, y2) in masks:
            mask_x1 = max(0, min(int(x1 * scale_x), width))
            mask_y1 = max(0, min(int(y1 * scale_y), height))
            mask_x2 = max(0, min(int(x2 * scale_x), width))
            mask_y2 = max(0, min(int(y2 * scale_y), height))
            if mask_x2 > mask_x1 and mask_y2 > mask_y1:
                self._cv2.rectangle(img, (mask_x1, mask_y1), (mask_x2, mask_y2), (0, 0, 0), -1)

    @staticmethod
    def _set_dpi_awareness() -> None:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    def blank_frame(self) -> np.ndarray:
        return self._np.zeros(self._fallback_shape, dtype=self._np.uint8)
