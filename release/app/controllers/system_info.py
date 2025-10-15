"""System information controller."""
from __future__ import annotations

import logging
from typing import Dict, Protocol

import psutil

logger = logging.getLogger(__name__)


class SystemMetrics(Protocol):
    """Protocol describing the psutil subset we depend on."""

    def virtual_memory(self):  # pragma: no cover - protocol definition
        ...

    def cpu_percent(self, interval: float = 1.0) -> float:  # pragma: no cover - protocol definition
        ...


class SystemInfoController:
    """Expose system metrics via dependency injection friendly methods."""

    def __init__(self, metrics: SystemMetrics = psutil) -> None:
        self._metrics = metrics

    def get_memory_usage(self) -> float:
        try:
            memory = self._metrics.virtual_memory()
            return round(float(memory.percent), 1)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("获取内存使用率时发生错误: %s", exc)
            return 0.0

    def get_cpu_usage(self, interval: float = 1.0) -> float:
        try:
            cpu_percent = self._metrics.cpu_percent(interval=interval)
            return round(float(cpu_percent), 1)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("获取CPU使用率时发生错误: %s", exc)
            return 0.0

    def get_system_info(self) -> Dict[str, float]:
        try:
            return {
                "memory_usage": self.get_memory_usage(),
                "cpu_usage": self.get_cpu_usage(),
            }
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("获取系统信息时发生错误: %s", exc)
            return {"memory_usage": 0.0, "cpu_usage": 0.0}
