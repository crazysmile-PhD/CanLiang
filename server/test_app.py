import os
import importlib

# Ensure environment variable so server.app can import
os.environ.setdefault('BETTERGI_PATH', '/tmp')

app_module = importlib.import_module('server.app')
parse_duration = app_module.parse_duration
analyse_all_logs = app_module.analyse_all_logs
app = app_module.app


def test_parse_duration_hours_only():
    assert parse_duration('1小时') == (1, 0)


def test_parse_duration_minutes_only():
    assert parse_duration('30分钟') == (0, 30)


def test_parse_duration_hours_minutes():
    assert parse_duration('1小时30分钟') == (1, 30)


def test_parse_duration_zero_minutes():
    assert parse_duration('0分钟') == (0, 0)


def test_analyse_all_logs_aggregates_duration(tmp_path, monkeypatch):
    log1 = (
        "[10:00:00.000] [INFO] Class\n"
        "主窗体实例化\n"
        "[11:00:00.000] [INFO] Class\n"
        "主窗体退出\n"
    )
    log2 = (
        "[12:00:00.000] [INFO] Class\n"
        "主窗体实例化\n"
        "[12:30:00.000] [INFO] Class\n"
        "主窗体退出\n"
    )

    (tmp_path / 'log1.log').write_text(log1, encoding='utf-8')
    (tmp_path / 'log2.log').write_text(log2, encoding='utf-8')

    monkeypatch.setattr(app_module, 'BGI_LOG_DIR', str(tmp_path))

    with app.app_context():
        data = analyse_all_logs().get_json()

    assert data['duration'] == '1小时30分钟'
