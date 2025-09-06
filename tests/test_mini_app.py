import os
import importlib.util

os.environ.setdefault('BETTERGI_PATH', '/tmp/bgi')

spec = importlib.util.spec_from_file_location("mini_app", os.path.join("mini", "app.py"))
mini_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mini_app)

format_timedelta = mini_app.format_timedelta
parse_log = mini_app.parse_log

def test_format_timedelta():
    assert format_timedelta(None) == "0分钟"
    assert format_timedelta(65) == "1分钟"
    assert format_timedelta(3600 + 180) == "1小时3分钟"

def test_parse_log_filters_and_counts_items():
    log_content = (
        "[00:00:00.000] [INFO] ClassA\n"
        "start\n"
        "[00:01:00.000] [INFO] ClassB\n"
        "交互或拾取：\"苹果\"\n"
        "[00:02:00.000] [INFO] ClassC\n"
        "交互或拾取：\"调查\"\n"
        "[00:02:30.000] [INFO] ClassD\n"
        "交互或拾取：\"苹果\"\n"
    )
    result = parse_log(log_content, "20250101")
    assert result["item_count"] == {"苹果": 2}
    assert result["duration"] == 150
