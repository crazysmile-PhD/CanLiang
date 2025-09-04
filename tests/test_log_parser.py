import os
import sys
import pandas as pd
import pytest

# Ensure BETTERGI_PATH is set so modules that expect it can import
os.environ.setdefault('BETTERGI_PATH', '.')

# Add the mini module directory to the Python path and import as LogAnalyzer
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'mini'))
import app as LogAnalyzer  # type: ignore


@pytest.fixture(autouse=True)
def reset_dataframes():
    """Reset global dataframes before each test to avoid cross-test contamination."""
    LogAnalyzer.item_dataframe = pd.DataFrame(columns=['物品名称', '时间', '日期'])
    LogAnalyzer.duration_dataframe = pd.DataFrame(columns=['日期', '持续时间（秒）'])
    yield


def test_parse_log_counts_items_and_duration():
    """Sample log with multiple segments and a forbidden item should return expected counts and duration."""
    log = (
        "[00:00:00.000] [Info] Log\n"
        "交互或拾取：\"ItemA\"\n"
        "[00:04:00.000] [Info] Log\n"
        "交互或拾取：\"调查\"\n"  # forbidden item should be ignored
        "[00:05:00.000] [Info] Log\n"
        "交互或拾取：\"ItemB\"\n"
        "[00:20:00.000] [Info] Log\n"
        "交互或拾取：\"ItemC\"\n"
        "[00:20:30.000] [Info] Log\n"
        "交互或拾取：\"ItemD\"\n"
    )
    result = LogAnalyzer.parse_log(log, '20240101')

    assert result['item_count'] == {'ItemA': 1, 'ItemB': 1, 'ItemC': 1, 'ItemD': 1}
    assert result['cache_dict']['物品名称'] == ['ItemA', 'ItemB', 'ItemC', 'ItemD']
    assert result['cache_dict']['时间'] == ['00:00:00.000', '00:05:00.000', '00:20:00.000', '00:20:30.000']
    # Duration currently includes the gap between segments
    assert result['duration'] == 930


def test_parse_log_caches_duplicate_entries():
    """Items already cached should not appear again in cache_dict."""
    log = (
        "[00:00:00.000] [Info] Log\n"
        "交互或拾取：\"ItemX\"\n"
    )
    first = LogAnalyzer.parse_log(log, '20240102')
    # Update cache to simulate global storage
    LogAnalyzer.item_dataframe = pd.concat(
        [LogAnalyzer.item_dataframe, pd.DataFrame(first['cache_dict'])], ignore_index=True
    )
    second = LogAnalyzer.parse_log(log, '20240102')

    assert first['cache_dict']['物品名称'] == ['ItemX']
    assert second['cache_dict']['物品名称'] == []
    assert second['duration'] == 0


def test_parse_log_time_gap_over_300_seconds():
    """Ensure long time gaps are handled when computing durations."""
    log = (
        "[00:00:00.000] [Info] Log\n"
        "交互或拾取：\"Item1\"\n"
        "[00:01:00.000] [Info] Log\n"
        "交互或拾取：\"Item2\"\n"
        "[00:10:00.000] [Info] Log\n"
        "交互或拾取：\"Item3\"\n"
        "[00:10:10.000] [Info] Log\n"
        "交互或拾取：\"Item4\"\n"
    )
    result = LogAnalyzer.parse_log(log, '20240103')

    assert result['item_count']['Item1'] == 1
    assert result['item_count']['Item4'] == 1
    assert result['duration'] == 550
