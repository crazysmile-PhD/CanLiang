import os
import re
import json
from datetime import datetime, timedelta
from collections import defaultdict
from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取日志目录路径
BGI_LOG_DIR = os.path.join(os.getenv('BETTERGI_PATH'), 'log')
# 调度器日志目录，可以通过环境变量覆盖
SCHEDULER_LOG_DIR = os.getenv('SCHEDULER_LOG_DIR') or \
    os.path.join(os.getenv('BETTERGI_PATH'), 'scheduler')

# 创建Flask应用实例，设置静态文件夹路径为'static'
app = Flask(__name__, static_folder='static')

# 需要过滤的物品列表
FORBIDDEN_ITEMS = ['调查', '直接拾取']


def format_timedelta(seconds):
    """
    将秒数转换为中文 x小时y分钟 格式
    
    Args:
        seconds: 秒数，可以是整数或None
        
    Returns:
        str: 格式化后的时间字符串，如 "5小时30分钟"
    """
    if seconds is None:
        return "0分钟"
        
    # 计算小时和分钟
    hours, remainder = divmod(int(seconds), 3600)
    minutes, _ = divmod(remainder, 60)
    
    # 拼接字符串（忽略零值部分）
    parts = []
    if hours > 0:
        parts.append(f"{hours}小时")
    if minutes > 0:
        parts.append(f"{minutes}分钟")
    
    return ''.join(parts) if parts else "0分钟"


def parse_duration(duration_str):
    """
    解析时间字符串，提取小时和分钟数
    
    Args:
        duration_str: 格式为 "X小时Y分钟" 的字符串
        
    Returns:
        tuple: (小时数, 分钟数)
    """
    match = re.match(r"(\d+)小时(\d+)分钟", duration_str)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        return hours, minutes
    else:
        return 0, 0


def parse_log(log_content):
    """
    解析日志内容，提取日志类型、交互物品等信息，并统计相关信息。
    支持多次主窗体实例化/退出，自动计算所有段的总时长。
    
    Args:
        log_content: 日志文件内容
        
    Returns:
        dict: 包含解析结果的字典
    """
    log_pattern = r'\[([^]]+)\] \[([^]]+)\] ([^\n]+)\n?([^\n[]*)'  
    matches = re.findall(log_pattern, log_content)
    
    type_count = {}
    interaction_items = []
    item_count = {}
    duration = 0
    
    current_start = None  # 当前段开始时间
    
    for match in matches:
        timestamp = match[0]  # 时间戳
        level = match[1]      # 日志级别
        log_type = match[2]   # 类名
        details = match[3].strip()  # 日志内容文本
        
        # 类型统计
        type_count[log_type] = type_count.get(log_type, 0) + 1
        
        # 提取拾取内容
        if '交互或拾取' in details:
            item = details.split('：')[1].strip('"')
            interaction_items.append(item)
            item_count[item] = item_count.get(item, 0) + 1
        
        # 处理时间段
        elif '主窗体实例化' in details:
            current_start = datetime.strptime(timestamp, '%H:%M:%S.%f')
        
        elif ('主窗体退出' in details or '将执行 关机' in details) and current_start:
            current_end = datetime.strptime(timestamp, '%H:%M:%S.%f')
            delta = (current_end - current_start).total_seconds()
            duration += int(delta)
            current_start = None  # 清除开始时间，准备下一段
    
    return {
        'type_count': type_count,
        'interaction_items': interaction_items,
        'interaction_count': len(interaction_items),
        'item_count': item_count,
        'delta_time': format_timedelta(duration)
    }


def read_log_file(file_path):
    """
    读取指定路径的日志文件并解析内容。
    
    Args:
        file_path: 日志文件路径
        
    Returns:
        dict: 解析后的日志信息字典，若发生错误则返回错误信息
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            log_content = file.read()
        return parse_log(log_content)
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
    # 获取所有以'better-genshin-impact'开头的日志文件，并提取日期部分
    log_files = [f.replace('better-genshin-impact', '').replace('.log', '') 
                for f in os.listdir(BGI_LOG_DIR) 
                if f.startswith('better-genshin-impact')]
    
    filtered_logs = []
    for file in log_files:
        file_path = os.path.join(BGI_LOG_DIR, f"better-genshin-impact{file}.log")
        result = read_log_file(file_path)
        
        if "error" in result:
            continue
            
        # 过滤掉不需要的物品
        items = result['item_count'].copy()
        for forbidden_item in FORBIDDEN_ITEMS:
            if forbidden_item in items:
                del items[forbidden_item]
                
        # 只保留有物品的日志
        if items:
            filtered_logs.append(file)
            
    return filtered_logs


def filter_forbidden_items(items):
    """
    从物品列表中过滤掉禁止的物品
    
    Args:
        items: 物品计数字典
        
    Returns:
        dict: 过滤后的物品计数字典
    """
    filtered_items = items.copy()
    for item in FORBIDDEN_ITEMS:
        if item in filtered_items:
            del filtered_items[item]
    return filtered_items


def parse_scheduler_line(line):
    """Parse a single scheduler log line.

    The parser is lenient and attempts to extract fields from either JSON
    formatted lines or plain text lines with ``key=value`` pairs.

    Returns a dictionary with ``group``, ``duration``, ``status`` and
    ``artifacts`` (a dict) when those fields can be found.
    """
    try:
        data = json.loads(line)
    except Exception:
        data = {}
        group_match = re.search(r'group[:=]([\w-]+)', line)
        if group_match:
            data['group'] = group_match.group(1)

        duration_match = re.search(r'duration[:=]([0-9.]+)', line)
        if duration_match:
            data['duration'] = float(duration_match.group(1))

        status_match = re.search(r'status[:=](success|failure)', line)
        if status_match:
            data['status'] = status_match.group(1)

        artifacts_match = re.search(r'artifacts[:=]({.*})', line)
        if artifacts_match:
            try:
                data['artifacts'] = json.loads(artifacts_match.group(1))
            except Exception:
                parts = re.findall(r'(\w+):(\d+)', artifacts_match.group(1))
                data['artifacts'] = {k: int(v) for k, v in parts}
    else:
        data.setdefault('artifacts', {})

    return data


def parse_scheduler_logs(window):
    """Aggregate scheduler logs within a given time window."""
    start_date = datetime.now().date() - timedelta(days=window - 1)
    stats_per_group = {}

    if not SCHEDULER_LOG_DIR or not os.path.isdir(SCHEDULER_LOG_DIR):
        return []

    for filename in sorted(os.listdir(SCHEDULER_LOG_DIR)):
        # Extract date from filename (e.g., scheduler-20240520.log)
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename) or \
            re.search(r'(\d{8})', filename)
        if not date_match:
            continue
        date_str = date_match.group(1)
        try:
            if '-' in date_str:
                file_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                file_date = datetime.strptime(date_str, '%Y%m%d').date()
        except ValueError:
            continue
        if file_date < start_date:
            continue

        path = os.path.join(SCHEDULER_LOG_DIR, filename)
        try:
            with open(path, 'r', encoding='utf-8') as fh:
                for line in fh:
                    data = parse_scheduler_line(line)
                    group = data.get('group')
                    if not group:
                        continue
                    duration = float(data.get('duration', 0))
                    status = data.get('status')
                    artifacts = data.get('artifacts', {})

                    group_stats = stats_per_group.setdefault(
                        group,
                        {
                            'group': group,
                            'durations': [],
                            'success_count': 0,
                            'failure_count': 0,
                            'artifacts': defaultdict(int),
                            'last_duration': 0,
                        },
                    )

                    group_stats['durations'].append(duration)
                    group_stats['last_duration'] = duration
                    if status == 'success':
                        group_stats['success_count'] += 1
                    elif status == 'failure':
                        group_stats['failure_count'] += 1
                    for a_type, count in artifacts.items():
                        try:
                            group_stats['artifacts'][a_type] += int(count)
                        except Exception:
                            pass
        except FileNotFoundError:
            continue

    results = []
    for data in stats_per_group.values():
        durations = data['durations']
        avg_duration = sum(durations) / len(durations) if durations else 0
        results.append(
            {
                'group': data['group'],
                'last_duration': data['last_duration'],
                'avg_duration': avg_duration,
                'success_count': data['success_count'],
                'failure_count': data['failure_count'],
                'artifacts': dict(data['artifacts']),
            }
        )

    return results


# 路由定义


@app.route('/<path:filename>')
def serve_static(filename):
    """
    提供静态资源的路由，返回指定的静态文件。
    """
    return send_from_directory('static', filename)


@app.route('/api/LogList', methods=['GET'])
def get_log_list_api():
    """
    提供日志文件列表的API接口。
    
    Returns:
        JSON: 包含日志文件列表的JSON响应
    """
    log_list = get_log_list()
    log_list.reverse()  # 最新的日志排在前面
    return jsonify({'list': log_list})


@app.route('/api/stats', methods=['GET'])
def scheduler_stats():
    """Return aggregated scheduler statistics."""
    window = request.args.get('window', '7')
    try:
        window = int(window)
    except ValueError:
        return jsonify({'error': 'invalid window'}), 400
    if window not in (1, 7, 30):
        return jsonify({'error': 'invalid window'}), 400

    stats = parse_scheduler_logs(window)
    return jsonify(stats)


@app.route('/api/analyse', methods=['GET'])
def analyse_log():
    """
    提供日志分析的API接口，返回指定日期的日志分析结果。
    
    Returns:
        JSON: 包含日志分析结果的JSON响应
    """
    date = request.args.get('date', 'all')
    
    if date == 'all':
        return analyse_all_logs()
    else:
        return analyse_single_log(date)


def analyse_all_logs():
    """
    分析所有日志文件并汇总结果
    
    Returns:
        JSON: 包含所有日志分析结果的JSON响应
    """
    total_hours = 0
    total_minutes = 0
    
    total_response = {
        "duration": "",
        "item_count": defaultdict(int)  # 自动初始化新 key 为 0
    }
    
    for filename in os.listdir(BGI_LOG_DIR):
        if not filename.endswith(".log"):
            continue
            
        file_path = os.path.join(BGI_LOG_DIR, filename)
        result = read_log_file(file_path)
        
        if "error" in result:
            continue
            
        # 过滤物品
        items = filter_forbidden_items(result['item_count'])
        
        sample_response = {
            'item_count': items,
            'duration': result['delta_time']
        }
        
        # 累加 item_count
        for key, value in sample_response["item_count"].items():
            total_response["item_count"][key] += value
        
        # 累加 duration
        hours, minutes = parse_duration(sample_response["duration"])
        total_hours += hours
        total_minutes += minutes
    
    # 处理分钟进位
    total_hours += total_minutes // 60
    total_minutes = total_minutes % 60
    
    # 设置总 duration 字符串
    total_response["duration"] = f"{total_hours}小时{total_minutes}分钟"
    
    return jsonify(total_response)


def analyse_single_log(date):
    """
    分析单个日志文件
    
    Args:
        date: 日志日期
        
    Returns:
        JSON: 包含单个日志分析结果的JSON响应
    """
    file_path = os.path.join(BGI_LOG_DIR, f"better-genshin-impact{date}.log")
    result = read_log_file(file_path)
    
    if "error" in result:
        return jsonify(result), 400
        
    # 过滤物品
    items = filter_forbidden_items(result['item_count'])
    
    response = {
        'item_count': items,
        'duration': result['delta_time']
    }
    
    return jsonify(response)


# 启动Flask应用
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=3000)
