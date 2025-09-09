import os
import logging
import importlib.util
from pathlib import Path

# Ensure required environment variable exists before importing modules
os.environ.setdefault('BETTERGI_PATH', '/tmp')

REPO_ROOT = Path(__file__).resolve().parents[1]

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

server_module = load_module("server.app", REPO_ROOT / "server" / "app.py")
mini_module = load_module("mini.app", REPO_ROOT / "mini" / "app.py")

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
