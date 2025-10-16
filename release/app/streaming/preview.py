"""Preview pipeline utilities for different streaming backends.

The preview subsystem is intentionally lightweight so it can be used in unit
and soak tests without requiring the full Sunshine runtime.  Only the Sunshine
variant currently implements behaviour beyond simple bookkeeping.  The engine
keeps a reusable buffer pool and only rebuilds buffers when the incoming frame
resolution changes.  It also records memory statistics that are consumed by the
20 minute soak test defined in :mod:`release.tests.test_performance`.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Deque, List, Optional

import numpy as np

try:  # pragma: no cover - psutil is optional at runtime
    import psutil
except Exception:  # pragma: no cover - the test-suite installs psutil
    psutil = None


logger = logging.getLogger(__name__)


class PreviewMode(str, Enum):
    """Supported preview backends."""

    NONE = "none"
    WEB_RTC = "web-rtc"
    LL_HLS = "ll-hls"
    SUNSHINE = "sunshine"

    @classmethod
    def from_value(cls, value: str | None) -> "PreviewMode":
        if not value:
            return cls.NONE
        try:
            return cls(value)
        except ValueError:
            logger.warning("未知的预览模式 %s，回退到 none", value)
            return cls.NONE


@dataclass(slots=True)
class MetricSample:
    """Snapshot captured during soak tests."""

    timestamp: float
    private_bytes: Optional[int]
    working_set: Optional[int]
    handles: Optional[int]
    frame_delay: Optional[float]


class FrameDelayTracker:
    """Track inter-frame delay to surface preview latency."""

    def __init__(self) -> None:
        self._last_timestamp: Optional[float] = None

    def observe(self, timestamp: float) -> Optional[float]:
        if self._last_timestamp is None:
            self._last_timestamp = timestamp
            return None
        delay = max(0.0, timestamp - self._last_timestamp)
        self._last_timestamp = timestamp
        return delay

    def reset(self) -> None:
        self._last_timestamp = None


class FrameBufferPool:
    """Maintain a pool of reusable frame buffers."""

    def __init__(self, max_buffers: int = 3, dtype: type[np.uint8] = np.uint8) -> None:
        self._max_buffers = max_buffers
        self._dtype = dtype
        self._pool: Deque[np.ndarray] = deque()
        self._lock = threading.Lock()
        self._resolution: Optional[tuple[int, int, int]] = None

    def _reset_resolution(self, shape: tuple[int, int, int]) -> None:
        self._resolution = shape
        self._pool.clear()

    def acquire(self, shape: tuple[int, int, int]) -> np.ndarray:
        with self._lock:
            if self._resolution != shape:
                self._reset_resolution(shape)
            try:
                buffer = self._pool.popleft()
                if buffer.shape != shape:
                    buffer = np.empty(shape, dtype=self._dtype)
            except IndexError:
                buffer = np.empty(shape, dtype=self._dtype)
            return buffer

    def release(self, buffer: np.ndarray) -> None:
        with self._lock:
            if self._resolution and buffer.shape != self._resolution:
                return
            if len(self._pool) < self._max_buffers:
                self._pool.append(buffer)

    def clear(self) -> None:
        with self._lock:
            self._pool.clear()
            self._resolution = None


class BasePreviewEngine:
    """Minimal interface shared by preview implementations."""

    def handle_frame(self, frame: np.ndarray, *, timestamp: Optional[float] = None) -> None:
        raise NotImplementedError

    def stop(self) -> None:  # pragma: no cover - default no-op
        return


class NullPreviewEngine(BasePreviewEngine):
    """Preview engine that simply discards frames."""

    def handle_frame(self, frame: np.ndarray, *, timestamp: Optional[float] = None) -> None:
        return


class SunshinePreviewEngine(BasePreviewEngine):
    """Preview pipeline for Sunshine integrations."""

    def __init__(
        self,
        *,
        sample_interval: float = 5.0,
        max_buffers: int = 3,
        process_factory: Optional[Callable[[], psutil.Process | None]] = None,
        time_source: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._pool = FrameBufferPool(max_buffers=max_buffers)
        self._active_buffer: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        self._latency = FrameDelayTracker()
        self._sample_interval = sample_interval
        self._last_sample_timestamp: Optional[float] = None
        self._samples: List[MetricSample] = []
        self._time_source = time_source
        self._rebuild_count = 0

        if process_factory is None:
            if psutil is None:  # pragma: no cover - defensive guard
                process_factory = lambda: None
            else:
                process_factory = lambda: psutil.Process(os.getpid())
        self._process_factory = process_factory
        self._process = process_factory()

    @property
    def rebuild_count(self) -> int:
        return self._rebuild_count

    @property
    def samples(self) -> List[MetricSample]:
        return list(self._samples)

    def handle_frame(self, frame: np.ndarray, *, timestamp: Optional[float] = None) -> None:
        ts = timestamp if timestamp is not None else self._time_source()
        with self._lock:
            buffer = self._ensure_buffer(frame.shape)
            np.copyto(buffer, frame)
        frame_delay = self._latency.observe(ts)
        self._maybe_sample(ts, frame_delay)

    def _ensure_buffer(self, shape: tuple[int, int, int]) -> np.ndarray:
        if self._active_buffer is not None and self._active_buffer.shape == shape:
            return self._active_buffer

        if self._active_buffer is not None:
            self._pool.release(self._active_buffer)

        buffer = self._pool.acquire(shape)
        if buffer.shape != shape:
            buffer = np.empty(shape, dtype=buffer.dtype)
        self._active_buffer = buffer
        self._rebuild_count += 1
        return buffer

    def _maybe_sample(self, timestamp: float, frame_delay: Optional[float]) -> None:
        if self._last_sample_timestamp is not None and timestamp - self._last_sample_timestamp < self._sample_interval:
            return
        sample = self._collect_metrics(timestamp, frame_delay)
        self._samples.append(sample)
        self._last_sample_timestamp = timestamp

    def _collect_metrics(self, timestamp: float, frame_delay: Optional[float]) -> MetricSample:
        private_bytes = working_set = handles = None

        if self._process is not None:
            try:
                mem_info = self._process.memory_info()
                private_bytes = getattr(mem_info, "private", None)
                working_set = getattr(mem_info, "rss", None)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.debug("无法采集内存指标: %s", exc)
            try:
                handles = self._process.num_handles()
            except AttributeError:
                handles = None
            except Exception as exc:  # pragma: no cover
                logger.debug("无法采集句柄数: %s", exc)

        return MetricSample(
            timestamp=timestamp,
            private_bytes=private_bytes,
            working_set=working_set,
            handles=handles,
            frame_delay=frame_delay,
        )

    def stop(self) -> None:
        with self._lock:
            if self._active_buffer is not None:
                self._pool.release(self._active_buffer)
                self._active_buffer = None
            self._pool.clear()
        self._latency.reset()
        self._last_sample_timestamp = None


class PreviewManager:
    """Factory responsible for building preview engines."""

    def __init__(self, mode: str | PreviewMode = PreviewMode.NONE, **engine_kwargs) -> None:
        self._mode = PreviewMode.from_value(str(mode) if not isinstance(mode, PreviewMode) else mode.value)
        self._engine_kwargs = engine_kwargs

    @property
    def mode(self) -> PreviewMode:
        return self._mode

    def create_engine(self, stream_id: Optional[str] = None) -> BasePreviewEngine:
        if self._mode is PreviewMode.SUNSHINE:
            return SunshinePreviewEngine(**self._engine_kwargs)
        if self._mode in {PreviewMode.WEB_RTC, PreviewMode.LL_HLS}:
            return NullPreviewEngine()
        return NullPreviewEngine()


def run_sunshine_soak_test(
    *,
    duration_seconds: float = 20 * 60,
    frame_interval: float = 1 / 30,
    sample_interval: float = 5.0,
    frame_factory: Optional[Callable[[int], np.ndarray]] = None,
) -> List[MetricSample]:
    """Run a synthetic soak test for Sunshine preview integrations.

    The soak test keeps generating frames for ``duration_seconds`` (20 minutes by
    default).  To keep the test practical the caller can provide a custom frame
    factory; otherwise a black 1280x720 frame is used.
    """

    if frame_interval <= 0:
        raise ValueError("frame_interval must be positive")
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be positive")

    if frame_factory is None:
        frame_factory = lambda _i: np.zeros((720, 1280, 3), dtype=np.uint8)

    engine = SunshinePreviewEngine(sample_interval=sample_interval)
    total_frames = int(duration_seconds / frame_interval)
    if total_frames <= 0:
        total_frames = 1

    timestamp = 0.0
    for index in range(total_frames):
        timestamp += frame_interval
        frame = frame_factory(index)
        engine.handle_frame(frame, timestamp=timestamp)

    engine.stop()
    return engine.samples


__all__ = [
    "BasePreviewEngine",
    "MetricSample",
    "NullPreviewEngine",
    "PreviewManager",
    "PreviewMode",
    "SunshinePreviewEngine",
    "FrameBufferPool",
    "run_sunshine_soak_test",
]
