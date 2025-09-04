import os
import re
from datetime import datetime

import pandas as pd

from config import BGI_LOG_DIR, logger

# 需要过滤的物品列表
FORBIDDEN_ITEMS = ['调查', '直接拾取']
item_dataframe = pd.DataFrame(columns=['物品名称', '时间', '日期'])
duration_dataframe = pd.DataFrame(columns=['日期', '持续时间（秒）'])
log_list = None


def parse_log(log_content, date_str):
    """
    解析日志内容，提取日志类型、交互物品等信息，并统计相关信息。
    支持多次主窗体实例化/退出，自动计算所有段的总时长。

    Args:
        log_content: 日志文件内容
        date_str: 日期字符串

    Returns:
        dict: 包含解析结果的字典
    """
    global item_dataframe, duration_dataframe
    log_pattern = r'\[([^]]+)\] \[([^]]+)\] ([^\n]+)\n?([^\n[]*)'
    matches = re.findall(log_pattern, log_content)

    item_count = {}
    duration = 0
    cache_dict = {
        '物品名称': [],
        '时间': [],
        '日期': []
    }

    current_start = None  # 当前段开始时间
    current_end = None

    for match in matches:
        timestamp = match[0]  # 时间戳
        level = match[1]  # 日志级别
        log_type = match[2]  # 类名
        details = match[3].strip()  # 日志内容文本

        # 过滤禁用的关键词
        if any(keyword in details for keyword in FORBIDDEN_ITEMS):
            continue

        # 转换时间戳
        current_time = datetime.strptime(timestamp, '%H:%M:%S.%f')

        # 提取拾取内容
        if '交互或拾取' in details:
            item = details.split('：')[1].strip('"')
            item_count[item] = item_count.get(item, 0) + 1

            existing_row = item_dataframe[
                (item_dataframe['物品名称'] == item) &
                (item_dataframe['时间'] == timestamp) &
                (item_dataframe['日期'] == date_str)
            ]

            if existing_row.empty:
                cache_dict['物品名称'].append(item)
                cache_dict['时间'].append(timestamp)
                cache_dict['日期'].append(date_str)

        # 处理时间段
        if not current_start:
            current_start = current_time
            current_end = current_time
        else:
            delta = (current_time - current_end).total_seconds()
            if delta <= 300:
                current_end = current_time
            else:
                if delta <= 0:
                    logger.critical(
                        f"时间段错误,请检查。有关参数：{timestamp, details, date_str, current_start, current_end, delta}")
                else:
                    duration += int(delta)
                current_start = current_time
                current_end = current_time

    if current_start and current_end and current_start != current_end:
        delta = (current_end - current_start).total_seconds()
        duration += int(delta)

    return {
        'item_count': item_count,
        'duration': duration,
        'cache_dict': cache_dict
    }


def read_log_file(file_path, date_str):
    """
    读取指定路径的日志文件并解析内容。

    Args:
        file_path: 日志文件路径
        date_str: 日期字符串

    Returns:
        dict: 解析后的日志信息字典，若发生错误则返回错误信息
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            log_content = file.read()
        return parse_log(log_content, date_str)
    except FileNotFoundError:
        return {"error": "文件未找到"}
    except Exception as e:
        return {"error": f"发生了一个未知错误: {e}"}


def get_log_list():
    """
    获取日志文件列表，并过滤掉不包含交互物品的日志文件。

    Returns:
        list: 过滤后的日志文件名列表
    """
    log_files = [f.replace('better-genshin-impact', '').replace('.log', '')
                 for f in os.listdir(BGI_LOG_DIR)
                 if f.startswith('better-genshin-impact')]

    filtered_logs = []
    duration_dict = {
        '日期': [],
        '持续时间（秒）': []
    }
    cached_dict = {
        '物品名称': [],
        '时间': [],
        '日期': []
    }
    for file in log_files:
        file_path = os.path.join(BGI_LOG_DIR, f"better-genshin-impact{file}.log")
        result = read_log_file(file_path, file)

        if "error" in result:
            continue

        items = result['item_count'].copy()
        for forbidden_item in FORBIDDEN_ITEMS:
            if forbidden_item in items:
                del items[forbidden_item]

        if items:
            filtered_logs.append(file)
            duration_dict['日期'].append(file)
            duration_dict['持续时间（秒）'].append(result['duration'])
            cached_dict['物品名称'].extend(result['cache_dict']['物品名称'])
            cached_dict['时间'].extend(result['cache_dict']['时间'])
            cached_dict['日期'].extend(result['cache_dict']['日期'])
    global duration_dataframe, item_dataframe
    duration_dataframe = pd.DataFrame(duration_dict)
    item_dataframe = pd.DataFrame(cached_dict)
    return filtered_logs
