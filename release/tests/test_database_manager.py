"""Tests for the SQLite-backed DatabaseManager helpers."""

from __future__ import annotations

import pytest

from app.infrastructure.database import DatabaseManager, LogDatabase


@pytest.fixture()
def db_path(tmp_path):
    return tmp_path / "test.db"


def test_insert_and_query_log_data(db_path):
    manager = DatabaseManager(str(db_path))

    items = [
        {"name": "ItemA", "timestamp": "12:00:00", "config_group": "Group1"},
        {"name": "ItemB", "timestamp": "12:05:00", "config_group": None},
    ]

    assert manager.insert_log_file_data("20250101", 120, items) is True

    # Stored dates should include the inserted value and be queryable again.
    assert manager.get_stored_dates() == ["20250101"]

    duration_map = manager.get_duration_data(exclude_today=False)
    assert duration_map == {"20250101": 120}

    grouped_items = manager.get_item_data(exclude_today=False)
    assert grouped_items["20250101"]["物品名称"] == ["ItemA", "ItemB"]
    assert grouped_items["20250101"]["时间"] == ["12:00:00", "12:05:00"]
    assert grouped_items["20250101"]["归属配置组"] == ["Group1", ""]

    info = manager.get_log_file_info("20250101")
    assert info["duration"] == 120
    assert info["item_count"] == 2

    stats = manager.get_database_stats()
    assert stats == {"log_files_count": 1, "items_count": 2}

    assert manager.delete_log_data("20250101") is True
    assert manager.get_stored_dates() == []
    assert manager.get_database_stats() == {"log_files_count": 0, "items_count": 0}


def test_log_database_serialises_iterables(db_path):
    log_db = LogDatabase(str(db_path))

    class _Item:
        def __init__(self, name: str, timestamp: str, config_group: str | None):
            self.name = name
            self.timestamp = timestamp
            self.config_group = config_group

    objects = [
        _Item("DropA", "10:00:01", "Auto"),
        {"name": "DropB", "timestamp": "10:05:00", "config_group": "Manual"},
        None,
    ]

    assert log_db.store_log_data("20250102", 42, objects) is True
    assert log_db.is_date_stored("20250102") is True

    duration_payload = log_db.get_duration_data(exclude_today=False)
    assert duration_payload == {"日期": ["20250102"], "持续时间": [42]}

    item_payload = log_db.get_item_data(exclude_today=False)
    assert item_payload["物品名称"] == ["DropA", "DropB"]
    assert item_payload["时间"] == ["10:00:01", "10:05:00"]
    assert item_payload["日期"] == ["20250102", "20250102"]
    assert item_payload["归属配置组"] == ["Auto", "Manual"]


def test_webhook_cleanup_and_retrieval(db_path):
    manager = DatabaseManager(str(db_path))

    assert manager.save_webhook_data({"event": "old", "result": "x"}) is True
    assert manager.save_webhook_data({"event": "fresh", "result": "y"}) is True

    # Mark the first row as very old so the cleanup routine removes it.
    with manager.get_connection() as conn:
        conn.execute(
            "UPDATE post_data SET create_time = ? WHERE event = ?",
            ("2000-01-01 00:00:00", "old"),
        )
        conn.commit()

    assert manager.cleanup_old_webhook_data(days_to_keep=1) is True

    records = manager.get_webhook_data(limit=5)
    assert [row["event"] for row in records] == ["fresh"]
    assert records[0]["result"] == "y"

    # Saving another entry should keep the list ordered by recency and obey the limit.
    assert manager.save_webhook_data({"event": "newer", "result": "z"}) is True
    top_record = manager.get_webhook_data(limit=1)[0]
    assert top_record["event"] == "newer"

