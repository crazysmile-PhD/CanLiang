"""Webhook controller module."""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional, Protocol

from app.infrastructure.database import DatabaseManager

logger = logging.getLogger(__name__)


class SupportsWebhookStorage(Protocol):
    """Protocol describing the storage dependency used by ``WebhookController``."""

    def save_webhook_data(self, payload: Dict[str, Any]) -> bool:
        ...

    def get_webhook_data(self, limit: int) -> list[Dict[str, Any]]:
        ...


def _validate_event_field(payload: Dict[str, Any]) -> Optional[str]:
    """Validate that the payload includes the ``event`` field."""

    if "event" not in payload or payload["event"] in (None, ""):
        return "缺少必需的event字段"
    return None


class WebhookController:
    """Handle webhook persistence and retrieval."""

    def __init__(
        self,
        log_dir: str,
        db_manager: Optional[SupportsWebhookStorage] = None,
        db_manager_factory: type[DatabaseManager] = DatabaseManager,
    ) -> None:
        db_path = os.path.join(log_dir, "CanLiangData.db")
        self.db_manager: SupportsWebhookStorage = db_manager or db_manager_factory(db_path)

    def save_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Persist webhook payload with defensive error handling."""

        error = _validate_event_field(payload)
        if error:
            return {"success": False, "message": error}

        try:
            if self.db_manager.save_webhook_data(payload):
                return {"success": True, "message": "数据保存成功"}
            return {"success": False, "message": "数据保存失败"}
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("保存webhook数据时发生错误: %s", exc)
            return {"success": False, "message": f"服务器内部错误: {exc}"}

    def get_webhook_data(self, limit: int = 100) -> Dict[str, Any]:
        """Return the latest webhook rows."""

        try:
            data_list = self.db_manager.get_webhook_data(limit)
            return {"success": True, "data": data_list, "count": len(data_list)}
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("获取webhook数据时发生错误: %s", exc)
            return {
                "success": False,
                "message": f"获取数据失败: {exc}",
                "data": [],
                "count": 0,
            }
