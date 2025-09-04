import re
import os
import json
import csv
from collections import defaultdict
from datetime import datetime, date
from typing import Optional
import fcntl


class StatisticsAggregator:
    """\u7edf\u8ba1\u7e3d\u548c\u5668\u7528\u4e8e\u8ddf\u8e2a ConfigGroup 執\u884c\u60c5\u6cc1"""

    def __init__(self, base_dir: str = "/log/statistics") -> None:
        self.base_dir = base_dir
        self.running = {}  # runId -> info
        self.completed = []  # list of finished runs
        self.products = defaultdict(lambda: defaultdict(int))  # runId -> productType -> qty

    def config_group_start(self, config_group_id: str, run_id: str,
                           timestamp: Optional[datetime] = None,
                           status: str = "start") -> None:
        ts = timestamp or datetime.utcnow()
        self.running[run_id] = {
            "runId": run_id,
            "configGroupId": config_group_id,
            "start": ts.isoformat(),
            "status": status,
        }

    def product_emitted(self, config_group_id: str, run_id: str,
                        product_type: str, qty: int,
                        timestamp: Optional[datetime] = None,
                        status: str = "emitted") -> None:
        ts = timestamp or datetime.utcnow()
        # 累\u8a08\u7522\u51fa次\u6578
        self.products[run_id][product_type] += qty

    def config_group_end(self, config_group_id: str, run_id: str,
                         status: str, timestamp: Optional[datetime] = None) -> None:
        ts = timestamp or datetime.utcnow()
        info = self.running.pop(run_id, {
            "runId": run_id,
            "configGroupId": config_group_id,
            "start": None,
        })
        info["end"] = ts.isoformat()
        info["status"] = status
        if info.get("start"):
            start_dt = datetime.fromisoformat(info["start"])
            info["duration"] = (ts - start_dt).total_seconds()
        else:
            info["duration"] = None
        self.completed.append(info)

    def flush(self, flush_date: Optional[date] = None) -> None:
        """\u5c07\u7d2f\u8a08\u6578\u64da\u8f38\u51fa\u81f3 JSONL \u8207 CSV"""
        if not self.completed:
            return
        flush_date = flush_date or date.today()
        os.makedirs(self.base_dir, exist_ok=True)
        json_path = os.path.join(self.base_dir, f"summary-{flush_date:%Y-%m-%d}.jsonl")
        csv_path = os.path.join(self.base_dir, f"summary-{flush_date:%Y-%m-%d}.csv")

        # JSONL 追\u52a0
        with open(json_path, "a", encoding="utf-8") as jf:
            fcntl.flock(jf, fcntl.LOCK_EX)
            for run in self.completed:
                entry = dict(run)
                entry["products"] = self.products.get(run["runId"], {})
                jf.write(json.dumps(entry, ensure_ascii=False) + "\n")
            fcntl.flock(jf, fcntl.LOCK_UN)

        # CSV 追\u52a0
        with open(csv_path, "a", newline="", encoding="utf-8") as cf:
            fcntl.flock(cf, fcntl.LOCK_EX)
            writer = csv.writer(cf)
            if cf.tell() == 0:
                writer.writerow([
                    "runId", "configGroupId", "start", "end",
                    "duration", "status", "productType", "qty",
                ])
            for run in self.completed:
                products = self.products.get(run["runId"], {})
                if not products:
                    writer.writerow([
                        run["runId"], run["configGroupId"], run.get("start"),
                        run.get("end"), run.get("duration"), run.get("status"),
                        "", "",
                    ])
                else:
                    for ptype, qty in products.items():
                        writer.writerow([
                            run["runId"], run["configGroupId"], run.get("start"),
                            run.get("end"), run.get("duration"), run.get("status"),
                            ptype, qty,
                        ])
            fcntl.flock(cf, fcntl.LOCK_UN)

        # 清\u7406空間
        for run in self.completed:
            self.products.pop(run["runId"], None)
        self.completed.clear()


# 全\u5c40\u7d2f\u8a08\u5668
aggregator = StatisticsAggregator()


def ConfigGroupStart(configGroupId: str, runId: str,
                     status: str = "start", timestamp: Optional[datetime] = None) -> None:
    aggregator.config_group_start(configGroupId, runId, timestamp, status)


def ProductEmitted(configGroupId: str, runId: str, productType: str, qty: int,
                   timestamp: Optional[datetime] = None, status: str = "emitted") -> None:
    aggregator.product_emitted(configGroupId, runId, productType, qty, timestamp, status)


def ConfigGroupEnd(configGroupId: str, runId: str, status: str,
                   timestamp: Optional[datetime] = None) -> None:
    aggregator.config_group_end(configGroupId, runId, status, timestamp)


def flush_statistics() -> None:
    """\u5c07\u5168\u5c40\u6578\u64da\u5beb\u5165總\u7d71\u8868"""
    aggregator.flush()


def parse_log(log_content):
    log_pattern = r'\[([^]]+)\] \[([^]]+)\] ([^\n]+)\n?([^\n[]*)'
    matches = re.findall(log_pattern, log_content)

    type_count = {}
    interaction_items = []

    for match in matches:
        timestamp = match[0]
        level = match[1]
        log_type = match[2]
        details = match[3].strip()

        # 统计每种类型的出现次数
        if log_type in type_count:
            type_count[log_type] += 1
        else:
            type_count[log_type] = 1

        # 提取交互或拾取的物品
        if '交互或拾取' in details:
            item = details.split('：')[1].strip('"')
            interaction_items.append(item)

    return {
        'type_count': type_count,
        'interaction_items': interaction_items,
        'interaction_count': len(interaction_items)
    }


def read_log_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            log_content = file.read()
        return parse_log(log_content)
    except FileNotFoundError:
        print("错误: 文件未找到!")
    except Exception as e:
        print(f"错误: 发生了一个未知错误: {e}")
    return None


if __name__ == "__main__":
    file_path = r"D:\software\BetterGI\log\better-genshin-impact20250430.log"
    result = read_log_file(file_path)
    if result:
        print("每种类型的出现次数:")
        for log_type, count in result['type_count'].items():
            print(f"{log_type}: {count} 次")
        print("\n交互或拾取的物品:")
        print(result['interaction_items'])
        print(f"\n交互或拾取的物品总数: {result['interaction_count']} 个")

        # 统计交互或拾取物品中每个字符串出现的次数
        item_count = {}
        for item in result['interaction_items']:
            if item in item_count:
                item_count[item] += 1
            else:
                item_count[item] = 1

        print("\n每个交互或拾取物品出现的次数:")
        for item, count in item_count.items():
            print(f"{item}: {count} 次")
