import os
import json
import re
import csv
from collections import defaultdict
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量以获取日志路径
load_dotenv()
LOG_DIR = os.path.join(os.getenv("BETTERGI_PATH"), "log")

STATE_FILE = os.path.join(os.path.dirname(__file__), "parser_state.json")
RUNS_FILE = os.path.join(os.path.dirname(__file__), "runs.jsonl")
SUMMARY_FILE = os.path.join(os.path.dirname(__file__), "summary.csv")

# 事件匹配模式
CONFIG_START_RE = re.compile(r"ConfigGroupStart group=(\S+) run=(\S+)")
CONFIG_END_RE = re.compile(r"ConfigGroupEnd group=(\S+) run=(\S+)")
PRODUCT_RE = re.compile(r"ProductEmitted name=(\S+) run=(\S+) count=(\d+)")
TIMESTAMP_RE = re.compile(r"\[(\d{2}:\d{2}:\d{2}\.\d+)\]")


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"files": {}}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def parse_timestamp(date_prefix: str, line: str) -> datetime:
    ts_match = TIMESTAMP_RE.search(line)
    if not ts_match:
        return None
    time_part = ts_match.group(1)
    dt = datetime.strptime(f"{date_prefix} {time_part}", "%Y%m%d %H:%M:%S.%f")
    return dt


def flush_run(run_id: str, run_data: dict, end_time: datetime):
    run_data["end"] = end_time.isoformat()
    run_data["duration"] = (end_time - run_data["start_dt"]).total_seconds()
    run_data["start"] = run_data["start_dt"].isoformat()
    del run_data["start_dt"]
    run_data["products"] = dict(run_data.get("products", {}))

    with open(RUNS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(run_data, ensure_ascii=False) + "\n")


def write_summary():
    summary = defaultdict(lambda: {"run_count": 0, "total_duration": 0, "product_count": 0})

    if os.path.exists(RUNS_FILE):
        with open(RUNS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                run = json.loads(line)
                group = run["configGroup"]
                s = summary[group]
                s["run_count"] += 1
                s["total_duration"] += run.get("duration", 0)
                s["product_count"] += sum(run.get("products", {}).values())

    with open(SUMMARY_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["config_group", "run_count", "total_duration_sec", "avg_duration_sec", "product_count"])
        for group, data in summary.items():
            avg = data["total_duration"] / data["run_count"] if data["run_count"] else 0
            writer.writerow([group, data["run_count"], int(data["total_duration"]), int(avg), data["product_count"]])


def parse_logs():
    state = load_state()
    state.setdefault("files", {})
    active_runs = {}

    for run_id, run_state in state.get("active_runs", {}).items():
        start_iso = run_state.get("start")
        start_dt = datetime.fromisoformat(start_iso) if start_iso else None
        active_runs[run_id] = {
            "runId": run_state.get("runId", run_id),
            "configGroup": run_state.get("configGroup"),
            "start_dt": start_dt,
            "products": defaultdict(int, run_state.get("products", {})),
        }

    for filename in sorted(os.listdir(LOG_DIR)):
        if not filename.startswith("better-genshin-impact") or not filename.endswith(".log"):
            continue
        date_part = filename.replace("better-genshin-impact", "").replace(".log", "")
        file_path = os.path.join(LOG_DIR, filename)
        offset = state["files"].get(filename, 0)

        with open(file_path, "r", encoding="utf-8") as f:
            f.seek(offset)
            for line in f:
                start_match = CONFIG_START_RE.search(line)
                if start_match:
                    group, run_id = start_match.groups()
                    ts = parse_timestamp(date_part, line)
                    active_runs[run_id] = {
                        "runId": run_id,
                        "configGroup": group,
                        "start_dt": ts,
                        "products": defaultdict(int),
                    }
                    continue

                prod_match = PRODUCT_RE.search(line)
                if prod_match:
                    name, run_id, count = prod_match.groups()
                    if run_id in active_runs:
                        active_runs[run_id]["products"][name] += int(count)
                    continue

                end_match = CONFIG_END_RE.search(line)
                if end_match:
                    group, run_id = end_match.groups()
                    if run_id in active_runs:
                        ts = parse_timestamp(date_part, line)
                        flush_run(run_id, active_runs.pop(run_id), ts)
                    continue

            state["files"][filename] = f.tell()

    state["active_runs"] = {}
    for run_id, run_data in active_runs.items():
        state["active_runs"][run_id] = {
            "runId": run_data["runId"],
            "configGroup": run_data["configGroup"],
            "start": run_data["start_dt"].isoformat() if run_data.get("start_dt") else None,
            "products": dict(run_data.get("products", {})),
        }

    save_state(state)
    write_summary()


if __name__ == "__main__":
    parse_logs()
