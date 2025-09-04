import os
import re
import logging
from datetime import datetime
import pandas as pd


class LogAnalyzer:
    def __init__(self, log_dir, forbidden_items=None):
        self.log_dir = log_dir
        self.forbidden_items = forbidden_items or ['调查', '直接拾取']
        self.item_dataframe = pd.DataFrame(columns=['物品名称', '时间', '日期'])
        self.duration_dataframe = pd.DataFrame(columns=['日期', '持续时间（秒）'])
        self.log_list = None
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def format_timedelta(seconds):
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

    def parse_log(self, log_content, date_str):
        log_pattern = r'\[([^]]+)\] \[([^]]+)\] ([^\n]+)\n?([^\n[]*)'
        matches = re.findall(log_pattern, log_content)

        item_count = {}
        duration = 0
        cache_dict = {'物品名称': [], '时间': [], '日期': []}

        current_start = None
        current_end = None

        for match in matches:
            timestamp = match[0]
            details = match[3].strip()

            if any(keyword in details for keyword in self.forbidden_items):
                continue

            current_time = datetime.strptime(timestamp, '%H:%M:%S.%f')

            if '交互或拾取' in details:
                item = details.split('：')[1].strip('"')
                item_count[item] = item_count.get(item, 0) + 1

                existing_row = self.item_dataframe[
                    (self.item_dataframe['物品名称'] == item) &
                    (self.item_dataframe['时间'] == timestamp) &
                    (self.item_dataframe['日期'] == date_str)
                ]
                if existing_row.empty:
                    cache_dict['物品名称'].append(item)
                    cache_dict['时间'].append(timestamp)
                    cache_dict['日期'].append(date_str)

            if not current_start:
                current_start = current_time
                current_end = current_time
            else:
                delta = (current_time - current_end).total_seconds()
                if delta <= 300:
                    current_end = current_time
                else:
                    if delta > 0:
                        duration += int(delta)
                    current_start = current_time
                    current_end = current_time

        if current_start and current_end and current_start != current_end:
            delta = (current_end - current_start).total_seconds()
            duration += int(delta)

        return {'item_count': item_count, 'duration': duration, 'cache_dict': cache_dict}

    def read_log_file(self, file_path, date_str):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                log_content = file.read()
            return self.parse_log(log_content, date_str)
        except FileNotFoundError:
            return {"error": "文件未找到"}
        except Exception as e:
            return {"error": f"发生了一个未知错误: {e}"}

    def get_log_list(self):
        if self.log_list is not None:
            return self.log_list

        log_files = [
            f.replace('better-genshin-impact', '').replace('.log', '')
            for f in os.listdir(self.log_dir)
            if f.startswith('better-genshin-impact')
        ]

        filtered_logs = []
        duration_dict = {'日期': [], '持续时间（秒）': []}
        cached_dict = {'物品名称': [], '时间': [], '日期': []}

        for file in log_files:
            file_path = os.path.join(self.log_dir, f"better-genshin-impact{file}.log")
            result = self.read_log_file(file_path, file)
            if "error" in result:
                continue

            items = result['item_count'].copy()
            for forbidden_item in self.forbidden_items:
                if forbidden_item in items:
                    del items[forbidden_item]

            if items:
                filtered_logs.append(file)
                duration_dict['日期'].append(file)
                duration_dict['持续时间（秒）'].append(result['duration'])
                cached_dict['物品名称'].extend(result['cache_dict']['物品名称'])
                cached_dict['时间'].extend(result['cache_dict']['时间'])
                cached_dict['日期'].extend(result['cache_dict']['日期'])

        self.duration_dataframe = pd.DataFrame(duration_dict)
        self.item_dataframe = pd.DataFrame(cached_dict)
        self.log_list = filtered_logs
        return filtered_logs

    def analyse_all_logs(self):
        if self.duration_dataframe.empty or self.item_dataframe.empty:
            return {'duration': '0分钟', 'item_count': {}}
        total_duration = self.duration_dataframe['持续时间（秒）'].sum()
        total_item_count = self.item_dataframe['物品名称'].value_counts().to_dict()
        return {
            'duration': self.format_timedelta(total_duration),
            'item_count': total_item_count
        }

    def analyse_single_log(self, date):
        filtered_item_df = self.item_dataframe[self.item_dataframe['日期'] == date]
        filtered_duration_df = self.duration_dataframe[self.duration_dataframe['日期'] == date]
        if filtered_duration_df.empty or filtered_item_df.empty:
            return {'duration': '0分钟', 'item_count': {}}
        total_duration = filtered_duration_df['持续时间（秒）'].sum()
        total_item_count = filtered_item_df['物品名称'].value_counts().to_dict()
        return {
            'duration': self.format_timedelta(total_duration),
            'item_count': total_item_count
        }

    def analyse_item_history(self, item_name):
        if self.item_dataframe.empty:
            return {'msg': 'no data.'}
        filter_dataframe = self.item_dataframe[self.item_dataframe['物品名称'] == item_name]
        data_counts = filter_dataframe['日期'].value_counts().to_dict()
        return {'data': data_counts}

    def analyse_duration_history(self):
        if self.duration_dataframe.empty:
            return {'msg': 'no data.'}
        total_seconds = self.duration_dataframe.groupby(self.duration_dataframe['日期'])['持续时间（秒）'].sum()
        total_minutes = (total_seconds // 60).astype(int)
        data_counts = total_minutes.to_dict()
        return {'data': data_counts}

    def analyse_all_items(self):
        if self.item_dataframe.empty:
            return {'msg': 'no data.'}
        data_counts = self.item_dataframe['日期'].value_counts().to_dict()
        return {'data': data_counts}
