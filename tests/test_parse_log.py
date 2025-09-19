import os
import logging
import importlib.util
from datetime import datetime
from pathlib import Path

# Ensure required environment variable exists before importing modules
os.environ.setdefault('BETTERGI_PATH', '/tmp')

REPO_ROOT = Path(__file__).resolve().parents[1]

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

server_module = load_module("tests.server_app_for_parse_log", REPO_ROOT / "server" / "app.py")
mini_module = load_module("tests.mini_app_for_parse_log", REPO_ROOT / "mini" / "app.py")

server_parse_log = server_module.parse_log
server_app = server_module.app
mini_parse_log = mini_module.parse_log
mini_app = mini_module.app


def test_server_parse_log_missing_delimiter(caplog):
    log_content = "[00:00:00.000] [INFO] Test\n交互或拾取 \"Item\"\n"
    with caplog.at_level(logging.WARNING, logger=server_app.logger.name):
        result = server_parse_log(log_content)
    assert result['item_count'] == {}
    assert '分隔符' in caplog.text


def test_mini_parse_log_missing_delimiter(caplog):
    log_content = "[00:00:00.000] [INFO] Test\n交互或拾取 \"Item\"\n"
    with caplog.at_level(logging.WARNING, logger=mini_app.logger.name):
        result = mini_parse_log(log_content, '20240101')
    assert result['item_count'] == {}
    assert result['cache_dict']['物品名称'] == []
    assert '分隔符' in caplog.text


def test_parse_log_handles_cross_midnight_duration():
    log_content = (
        "[23:58:00.000] [INFO] Class\n"
        "主窗体实例化\n"
        "[00:01:00.000] [INFO] Class\n"
        "交互或拾取：\"Item\"\n"
        "[00:02:00.000] [INFO] Class\n"
        "主窗体退出\n"
    )

    expected_start = datetime(2024, 1, 1, 23, 58)
    expected_end = datetime(2024, 1, 2, 0, 2)
    expected_seconds = int((expected_end - expected_start).total_seconds())

    server_result = server_parse_log(log_content)
    assert server_result['delta_time'] == '4分钟'
    hours, minutes = server_module.parse_duration(server_result['delta_time'])
    observed_seconds = hours * 3600 + minutes * 60
    assert observed_seconds == expected_seconds

    original_item_df = mini_module.item_dataframe
    original_duration_df = mini_module.duration_dataframe
    try:
        mini_module.item_dataframe = mini_module.pd.DataFrame(columns=['物品名称', '时间', '日期'])
        mini_module.duration_dataframe = mini_module.pd.DataFrame(columns=['日期', '持续时间（秒）'])
        mini_result = mini_parse_log(log_content, '20240101')
    finally:
        mini_module.item_dataframe = original_item_df
        mini_module.duration_dataframe = original_duration_df

    assert mini_result['duration'] == expected_seconds
    assert mini_result['cache_dict']['时间'] == ['00:01:00.000']
