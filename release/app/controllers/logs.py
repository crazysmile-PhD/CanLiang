"""Log controller module.

This module exposes a ``LogController`` that coordinates the ``LogDataManager``
while keeping helper utilities local to improve cohesion and testability.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Optional, Protocol

from app.infrastructure.manager import LogDataManager

logger = logging.getLogger(__name__)


class SupportsLogData(Protocol):
    """Protocol describing the minimal ``LogDataManager`` API we rely on."""

    log_list: List[str]

    def get_log_list(self) -> List[str]:
        ...

    def get_duration_data(self) -> Dict[str, Iterable[Any]]:
        ...

    def get_item_data(self) -> Dict[str, Iterable[Any]]:
        ...


def _reverse(items: Iterable[str]) -> List[str]:
    """Return a new reversed list without mutating the original iterable."""

    return list(reversed(list(items)))


class LogController:
    """Coordinates log related queries for the API layer."""

    def __init__(
        self,
        log_dir: str,
        manager: Optional[SupportsLogData] = None,
        manager_factory: type[LogDataManager] = LogDataManager,
    ) -> None:
        self.log_manager: SupportsLogData = manager or manager_factory(log_dir)

    def get_log_list(self) -> Dict[str, List[str]]:
        """Return a DTO containing the available log identifiers."""

        try:
            log_list = self.log_manager.log_list or self.log_manager.get_log_list()
            return {"list": _reverse(log_list)}
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("获取日志列表时发生错误: %s", exc)
            return {"list": []}

    def get_log_data(self) -> Dict[str, Any]:
        """Return aggregated duration and item information for the UI."""

        try:
            duration_data = dict(self.log_manager.get_duration_data())
            item_data = dict(self.log_manager.get_item_data())
            return {"duration": duration_data, "item": item_data}
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("获取日志数据时发生错误: %s", exc)
            return {
                "duration": {"日期": [], "持续时间": []},
                "item": {
                    "物品名称": [],
                    "时间": [],
                    "日期": [],
                    "归属配置组": [],
                },
            }
