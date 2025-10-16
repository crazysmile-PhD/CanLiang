"""Unit tests for the lightweight controller facade.

These tests focus on the pure-Python behaviour that should work in the
headless CI environment.  All interactions with the heavy dependencies are
stubbed so the logic around validation, error handling and fallbacks can be
verified.
"""

from __future__ import annotations

import numpy as np
import pytest

from app.api import controllers as controllers_module


class _StubLogManager:
    """In-memory substitute for :class:`LogDataManager`."""

    def __init__(self, _log_dir: str):
        self.log_list: list[str] = []
        self._duration = {
            "日期": ["20250101"],
            "持续时间": [3600],
        }
        self._items = {
            "物品名称": ["摩拉"],
            "时间": ["10:00:00"],
            "日期": ["20250101"],
            "归属配置组": ["自动拾取"],
        }

    def get_log_list(self) -> list[str]:
        return ["20240101", "20240102", "20240103"]

    def get_duration_data(self):
        return self._duration

    def get_item_data(self):
        return self._items


def test_log_controller_returns_reversed_log_list(monkeypatch):
    """The log list should be returned in reverse chronological order."""

    monkeypatch.setattr(
        controllers_module,
        "LogDataManager",
        _StubLogManager,
    )

    controller = controllers_module.LogController("/tmp/logs")
    response = controller.get_log_list()

    assert response == {"list": ["20240103", "20240102", "20240101"]}


def test_log_controller_handles_manager_failure(monkeypatch):
    """Errors raised by the manager should be converted into a safe payload."""

    class _BrokenManager(_StubLogManager):
        def get_log_list(self):  # pragma: no cover - trivial override
            raise RuntimeError("boom")

    monkeypatch.setattr(controllers_module, "LogDataManager", _BrokenManager)

    controller = controllers_module.LogController("/tmp/logs")
    response = controller.get_log_list()

    assert response == {"list": []}


def test_log_controller_returns_cached_metrics(monkeypatch):
    """`get_log_data` should surface the cached analytics dictionaries."""

    monkeypatch.setattr(controllers_module, "LogDataManager", _StubLogManager)

    controller = controllers_module.LogController("/tmp/logs")
    payload = controller.get_log_data()

    assert payload["duration"]["持续时间"] == [3600]
    assert payload["item"]["物品名称"] == ["摩拉"]


def test_log_controller_gracefully_handles_metric_failure(monkeypatch):
    """An exception while collecting metrics should return empty structures."""

    class _FailingMetrics(_StubLogManager):
        def get_duration_data(self):  # pragma: no cover - trivial override
            raise RuntimeError("duration failed")

    monkeypatch.setattr(controllers_module, "LogDataManager", _FailingMetrics)

    controller = controllers_module.LogController("/tmp/logs")
    payload = controller.get_log_data()

    assert payload["duration"]["日期"] == []
    assert payload["item"]["物品名称"] == []


class _StubDatabase:
    """Trivial stand-in for :class:`DatabaseManager`."""

    def __init__(self, _path: str):
        self.saved_payloads: list[dict] = []
        self._data = [{"event": "start", "message": "ok"}]

    def save_webhook_data(self, payload: dict) -> bool:
        self.saved_payloads.append(payload)
        return True

    def get_webhook_data(self, limit: int):  # pragma: no cover - passthrough
        return list(self._data)


def test_webhook_controller_validates_event_field(monkeypatch):
    monkeypatch.setattr(controllers_module, "DatabaseManager", _StubDatabase)

    controller = controllers_module.WebhookController("/tmp/logs")
    assert controller.save_data({"result": "ok"}) == {
        "success": False,
        "message": "缺少必需的event字段",
    }


def test_webhook_controller_persists_payload(monkeypatch):
    monkeypatch.setattr(controllers_module, "DatabaseManager", _StubDatabase)

    controller = controllers_module.WebhookController("/tmp/logs")
    payload = {"event": "start", "result": "ok"}
    response = controller.save_data(payload)

    assert response == {"success": True, "message": "数据保存成功"}
    assert controller.db_manager.saved_payloads == [payload]


def test_webhook_controller_handles_storage_failure(monkeypatch):
    class _RejectingDatabase(_StubDatabase):
        def save_webhook_data(self, payload):  # pragma: no cover - override
            super().save_webhook_data(payload)
            return False

    monkeypatch.setattr(
        controllers_module,
        "DatabaseManager",
        _RejectingDatabase,
    )

    controller = controllers_module.WebhookController("/tmp/logs")
    payload = {"event": "start"}
    response = controller.save_data(payload)

    assert response == {"success": False, "message": "数据保存失败"}


def test_webhook_controller_get_data_success(monkeypatch):
    class _CustomDatabase(_StubDatabase):
        def get_webhook_data(self, limit: int):
            assert limit == 5
            return [{"event": "done"}]

    monkeypatch.setattr(controllers_module, "DatabaseManager", _CustomDatabase)

    controller = controllers_module.WebhookController("/tmp/logs")
    response = controller.get_webhook_data(limit=5)

    assert response == {
        "success": True,
        "data": [{"event": "done"}],
        "count": 1,
    }


def test_webhook_controller_handles_query_failure(monkeypatch):
    class _ErrorDatabase(_StubDatabase):
        def get_webhook_data(self, limit: int):  # pragma: no cover - override
            raise RuntimeError("boom")

    monkeypatch.setattr(controllers_module, "DatabaseManager", _ErrorDatabase)

    controller = controllers_module.WebhookController("/tmp/logs")
    response = controller.get_webhook_data()

    assert response["success"] is False
    assert response["data"] == []


def test_stream_controller_falls_back_to_blank_frame(monkeypatch):
    monkeypatch.setattr(controllers_module, "WINDOWS_CAPTURE_AVAILABLE", False)

    controller = controllers_module.StreamController()
    frame = controller.capture_window(hwnd=12345)

    assert frame.shape == (480, 640, 3)
    assert isinstance(frame, np.ndarray)
    assert frame.sum() == 0


def test_stream_controller_rejects_disabled_preview():
    controller = controllers_module.StreamController(preview_mode='none')

    with pytest.raises(controllers_module.PreviewModeError) as exc:
        controller.start_stream()

    assert exc.value.preview_mode == 'none'


def test_stream_controller_rejects_sunshine_preview():
    controller = controllers_module.StreamController(preview_mode='sunshine')

    with pytest.raises(controllers_module.PreviewModeError) as exc:
        controller.start_stream()

    assert exc.value.preview_mode == 'sunshine'
