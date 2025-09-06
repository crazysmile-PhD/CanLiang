import os
import sys

# Ensure the repository root is on the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Provide a dummy BETTERGI_PATH so mini.app can be imported
os.environ.setdefault("BETTERGI_PATH", "/tmp")

from mini.app import parse_log


def test_duration_multiple_runs_with_gaps():
    log_content = (
        "[00:00:00.000] [INFO] TypeA\n"
        "[00:02:00.000] [INFO] TypeA\n"
        "[00:12:00.000] [INFO] TypeA\n"
        "[00:15:00.000] [INFO] TypeA\n"
    )

    result = parse_log(log_content, "2024-01-01")

    # 第一段持续2分钟，第二段持续3分钟，总计300秒
    assert result["duration"] == 300


def test_duration_three_runs_with_gaps():
    log_content = (
        "[00:00:00.000] [INFO] TypeA\n"
        "[00:01:00.000] [INFO] TypeA\n"
        "[00:07:00.000] [INFO] TypeA\n"
        "[00:09:00.000] [INFO] TypeA\n"
        "[00:15:00.000] [INFO] TypeA\n"
        "[00:17:30.000] [INFO] TypeA\n"
    )

    result = parse_log(log_content, "2024-01-02")

    # 三段持续时间分别为1分钟、2分钟和2.5分钟，总计330秒
    assert result["duration"] == 330

