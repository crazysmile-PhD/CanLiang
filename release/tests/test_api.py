import pytest

from app.api.controllers import LogController, WebhookController


class DummyLogManager:
    def __init__(self, *_args, log_list=None, duration=None, items=None, **_kwargs):
        self.log_list = list(log_list or [])
        self.next_list = list(log_list or [])
        self._duration = duration or {'日期': [], '持续时间': []}
        self._items = items or {'物品名称': [], '时间': [], '日期': [], '归属配置组': []}
        self.get_log_list_called = 0

    def get_log_list(self):
        self.get_log_list_called += 1
        return list(self.next_list)

    def get_duration_data(self):
        return self._duration

    def get_item_data(self):
        return self._items


class DummyDatabaseManager:
    def __init__(self, *_args, **_kwargs):
        self.saved_payloads = []
        self.stored_data = []

    def save_webhook_data(self, payload):
        self.saved_payloads.append(payload)
        return payload.get('event') == 'valid'

    def get_webhook_data(self, limit):
        return self.stored_data[:limit]


@pytest.fixture(autouse=True)
def patch_dependencies(monkeypatch):
    monkeypatch.setattr('app.api.controllers.LogDataManager', DummyLogManager)
    monkeypatch.setattr('app.api.controllers.DatabaseManager', DummyDatabaseManager)


def test_log_controller_returns_reversed_list():
    controller = LogController(log_dir='/tmp/logs')
    controller.log_manager.log_list = ['20240102', '20240101']

    result = controller.get_log_list()

    assert result == {'list': ['20240101', '20240102']}
    assert controller.log_manager.get_log_list_called == 0


def test_log_controller_fetches_when_cache_missing():
    controller = LogController(log_dir='/tmp/logs')
    controller.log_manager.log_list = []
    controller.log_manager.next_list = ['20240101', '20240102']

    result = controller.get_log_list()

    assert result['list'] == ['20240102', '20240101']
    assert controller.log_manager.get_log_list_called == 1


def test_log_controller_returns_cached_data_for_analysis():
    controller = LogController(log_dir='/tmp/logs')
    controller.log_manager.log_list = []
    controller.log_manager._duration = {'日期': ['20240103'], '持续时间': [120]}
    controller.log_manager._items = {'物品名称': ['测试'], '时间': ['10:00'], '日期': ['20240103'], '归属配置组': ['组1']}

    result = controller.get_log_data()

    assert result['duration']['持续时间'] == [120]
    assert result['item']['物品名称'] == ['测试']


def test_webhook_controller_save_data_success():
    controller = WebhookController(log_dir='/tmp/logs')
    payload = {'event': 'valid', 'result': 'ok'}

    response = controller.save_data(payload)

    assert response == {'success': True, 'message': '数据保存成功'}
    assert controller.db_manager.saved_payloads == [payload]


def test_webhook_controller_missing_event_returns_error():
    controller = WebhookController(log_dir='/tmp/logs')

    response = controller.save_data({'result': 'missing'})

    assert response['success'] is False
    assert 'event' in response['message']


def test_webhook_controller_handles_save_failure(monkeypatch):
    controller = WebhookController(log_dir='/tmp/logs')

    def fail_save(_payload):
        raise RuntimeError('db down')

    monkeypatch.setattr(controller.db_manager, 'save_webhook_data', fail_save)

    response = controller.save_data({'event': 'valid'})

    assert response['success'] is False
    assert '服务器内部错误' in response['message']
