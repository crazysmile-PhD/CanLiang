from datetime import datetime, timedelta

import pytest

from app.infrastructure.database import DatabaseManager


@pytest.fixture()
def db_path(tmp_path):
    return tmp_path / 'data' / 'test.db'


@pytest.fixture()
def db_manager(db_path):
    return DatabaseManager(str(db_path))


def test_insert_and_query_log_data(db_manager):
    items = [
        {'name': '物品A', 'timestamp': '12:00:00', 'config_group': '组1'},
        {'name': '物品B', 'timestamp': '12:05:00', 'config_group': '组1'},
    ]

    assert db_manager.insert_log_file_data('20240101', 120, items) is True

    stored_dates = db_manager.get_stored_dates()
    assert '20240101' in stored_dates

    duration = db_manager.get_duration_data(exclude_today=False)
    assert duration['20240101'] == 120

    item_data = db_manager.get_item_data(exclude_today=False)
    assert set(item_data['20240101']['物品名称']) == {'物品A', '物品B'}


def test_delete_log_data(db_manager):
    items = [{'name': '物品A', 'timestamp': '12:00:00', 'config_group': '组1'}]
    db_manager.insert_log_file_data('20240102', 60, items)

    assert db_manager.delete_log_data('20240102') is True
    assert db_manager.get_log_file_info('20240102') is None


def test_save_and_fetch_webhook_data(db_manager):
    payload = {'event': 'TestEvent', 'result': 'ok', 'message': '测试'}
    assert db_manager.save_webhook_data(payload) is True

    data = db_manager.get_webhook_data(limit=10)
    assert len(data) == 1
    assert data[0]['event'] == 'TestEvent'


def test_cleanup_webhook_data(db_manager):
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO post_data (event, create_time) VALUES (?, ?)',
            ('old', (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S')),
        )
        cursor.execute(
            'INSERT INTO post_data (event, create_time) VALUES (?, ?)',
            ('recent', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        )
        conn.commit()

    assert db_manager.cleanup_old_webhook_data(days_to_keep=3) is True

    remaining = db_manager.get_webhook_data(limit=10)
    events = [row['event'] for row in remaining]
    assert 'old' not in events
    assert 'recent' in events
