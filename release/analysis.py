from flask import jsonify

from flask import jsonify

from log_parser import item_dataframe, duration_dataframe


def format_timedelta(seconds):
    """将秒数转换为中文 x小时y分钟 格式"""
    if seconds is None:
        return "0分钟"
    hours, remainder = divmod(int(seconds), 3600)
    minutes, _ = divmod(remainder, 60)
    parts = []
    if hours > 0:
        parts.append(f"{hours}小时")
    if minutes > 0:
        parts.append(f"{minutes}分钟")
    return ''.join(parts) if parts else "0分钟"


def analyse_all_logs():
    """分析所有日志文件并汇总结果"""
    if duration_dataframe.empty or item_dataframe.empty:
        return jsonify({'duration': '0分钟', 'item_count': {}})
    total_duration = duration_dataframe['持续时间（秒）'].sum()
    total_item_count = item_dataframe['物品名称'].value_counts().to_dict()
    return jsonify({
        'duration': format_timedelta(total_duration),
        'item_count': total_item_count
    })


def analyse_single_log(date):
    """分析单个日志文件"""
    filtered_item_df = item_dataframe[item_dataframe['日期'] == date]
    filtered_duration_df = duration_dataframe[duration_dataframe['日期'] == date]
    if filtered_duration_df.empty or filtered_item_df.empty:
        return jsonify({'duration': '0分钟', 'item_count': {}})
    total_duration = filtered_duration_df['持续时间（秒）'].sum()
    total_item_count = filtered_item_df['物品名称'].value_counts().to_dict()
    return jsonify({
        'duration': format_timedelta(total_duration),
        'item_count': total_item_count
    })


def analyse_item_history(item_name):
    """分析物品历史数据"""
    if item_dataframe.empty:
        return jsonify({'msg': 'no data.'})
    filter_dataframe = item_dataframe[item_dataframe['物品名称'] == item_name]
    data_counts = filter_dataframe['日期'].value_counts().to_dict()
    return jsonify({'data': data_counts})


def analyse_duration_history():
    if duration_dataframe.empty:
        return jsonify({'msg': 'no data.'})
    total_seconds = duration_dataframe.groupby(duration_dataframe['日期'])['持续时间（秒）'].sum()
    total_minutes = (total_seconds // 60).astype(int)
    data_counts = total_minutes.to_dict()
    return jsonify({'data': data_counts})


def analyse_all_items():
    if item_dataframe.empty:
        return jsonify({'msg': 'no data.'})
    data_counts = item_dataframe['日期'].value_counts().to_dict()
    return jsonify({'data': data_counts})
