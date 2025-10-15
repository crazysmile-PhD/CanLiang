from pathlib import Path

import pytest

from app.infrastructure.manager import LogDataManager


LOG_TEMPLATE = '''[12:00:00.000] [INFO] [TestClass]
配置组 "测试组" 加载完成，共1个脚本，开始执行
[12:00:05.000] [INFO] [TestClass]
交互或拾取："道具A"
[12:05:10.000] [INFO] [TestClass]
配置组 "测试组" 执行结束
[12:05:15.000] [INFO] [TestClass]
交互或拾取："道具B"
'''


@pytest.fixture()
def log_dir(tmp_path):
    (tmp_path / 'logs').mkdir()
    return tmp_path / 'logs'


def write_log(file_path: Path, content: str):
    file_path.write_text(content, encoding='utf-8')


def test_parse_log_extracts_items_and_duration(log_dir):
    manager = LogDataManager(str(log_dir))
    manager.today_str = '20240102'

    result = manager.parse_log(LOG_TEMPLATE, '20240101')

    assert result.item_count == {'道具A': 1, '道具B': 1}
    assert result.duration > 0
    assert any(item.name == '道具A' for item in result.items)


def test_get_log_list_combines_history_and_today(log_dir):
    history_file = log_dir / 'better-genshin-impact20240101.log'
    write_log(history_file, LOG_TEMPLATE)

    today_file = log_dir / 'better-genshin-impact20240102.log'
    write_log(today_file, LOG_TEMPLATE)

    manager = LogDataManager(str(log_dir))
    manager.today_str = '20240102'

    logs = manager.get_log_list()

    assert '20240101' in logs
    assert '20240102' in logs

    duration_data = manager.get_duration_data()
    assert set(duration_data['日期']) == {'20240101', '20240102'}

    item_data = manager.get_item_data()
    assert item_data['物品名称']
