"""Streaming orchestration built on top of modular collaborators."""
from __future__ import annotations

import logging
import time
from typing import Callable, Iterable, Optional

import cv2
import numpy as np
import win32gui
from flask import Response

from .capture import FrameCapture
from .programs import ProgramLister
from .window_finder import WindowFinder

logger = logging.getLogger(__name__)

FrameEncoder = Callable[[str, np.ndarray, Iterable[int]], tuple[bool, np.ndarray]]


class StreamController:
    """Coordinate window discovery, frame capture and MJPEG streaming."""

    def __init__(
        self,
        target_app: str = "yuanshen.exe",
        *,
        finder: Optional[WindowFinder] = None,
        capture: Optional[FrameCapture] = None,
        encoder: FrameEncoder = cv2.imencode,
        response_class: type[Response] = Response,
        sleeper: Callable[[float], None] = time.sleep,
        program_lister: Optional[ProgramLister] = None,
        desktop_window: Callable[[], int] = win32gui.GetDesktopWindow,
    ) -> None:
        self.target_app = target_app
        self.is_streaming = False
        self.hwnd: Optional[int] = None
        self._finder = finder or WindowFinder()
        self._capture = capture or FrameCapture()
        self._encoder = encoder
        self._response_class = response_class
        self._sleep = sleeper
        self._programs = program_lister or ProgramLister(self._finder)
        self._desktop_window = desktop_window

    # streaming ---------------------------------------------------------------

    def generate_frames(self):
        try:
            self.hwnd = self._resolve_hwnd()
            if not self.hwnd:
                logger.warning("未找到进程 %s 的窗口", self.target_app)
                yield from self._black_frames()
                return

            self.is_streaming = True
            logger.info("开始推流 - 目标应用: %s", self.target_app)
            while self.is_streaming:
                try:
                    if self.target_app != "桌面.exe" and not self._is_window_valid(self.hwnd):
                        logger.warning("窗口句柄 %s 已失效，重新查找窗口", self.hwnd)
                        self.hwnd = self._finder.find(self.target_app)
                        if not self.hwnd:
                            logger.warning("无法重新找到进程 %s 的窗口，返回黑屏", self.target_app)
                            frame = self._capture.blank_frame()
                            self.is_streaming = False
                        else:
                            frame = self._capture.capture(self.hwnd, self.target_app)
                    else:
                        frame = self._capture.capture(self.hwnd, None if self.target_app == "桌面.exe" else self.target_app)

                    ret, buffer = self._encoder(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    if ret:
                        frame_bytes = buffer.tobytes()
                        yield (
                            b"--frame\r\n"
                            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                        )
                    self._sleep(1 / 30)
                except GeneratorExit:
                    logger.info("检测到客户端断开连接，停止推流 - 目标应用: %s", self.target_app)
                    self.is_streaming = False
                    break
                except Exception as exc:
                    logger.error("生成视频帧时发生错误: %s", exc)
                    self._sleep(0.1)
        finally:
            if self.is_streaming:
                self.is_streaming = False
                logger.info("推流已停止 - 目标应用: %s", self.target_app)

    def start_stream(self) -> Response:
        return self._response_class(
            self.generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame"
        )

    def stop_stream(self) -> None:
        self.is_streaming = False
        logger.info("视频流已停止")

    def get_stream_info(self):
        return {
            "target_app": self.target_app,
            "is_streaming": self.is_streaming,
            "window_found": bool(self.hwnd and self.hwnd != self._desktop_window()),
            "hwnd": self.hwnd,
        }

    # program discovery -------------------------------------------------------

    def get_available_programs(self):
        return self._programs.list_programs()

    # helpers -----------------------------------------------------------------

    def _resolve_hwnd(self) -> Optional[int]:
        if self.target_app == "桌面.exe":
            return self._desktop_window()
        return self._finder.find(self.target_app)

    def _black_frames(self):
        self.is_streaming = True
        while self.is_streaming:
            try:
                frame = self._capture.blank_frame()
                ret, buffer = self._encoder(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                    )
                self._sleep(1 / 30)
            except GeneratorExit:
                logger.info("检测到客户端断开连接，停止推流 - 目标应用: %s", self.target_app)
                self.is_streaming = False
                break
            except Exception as exc:
                logger.error("生成黑屏帧时发生错误: %s", exc)
                self._sleep(0.1)

    @staticmethod
    def _is_window_valid(hwnd: Optional[int]) -> bool:
        if hwnd is None:
            return False
        return win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd)
