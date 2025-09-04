#!/usr/bin/env python3
"""Utility to upgrade legacy BetterGI logs to the new event format.

The script scans a log directory, converts files detected as old format,
and creates a ``.bak`` backup before rewriting the upgraded content.
"""
import argparse
import os
import re
import shutil


NEW_PATTERN = re.compile(r"\[\d{2}:\d{2}:\d{2}\.\d{3}\]")
LEGACY_LINE = re.compile(r"(\d{2}:\d{2}:\d{2}\.\d{3})\s+(\w+)\s+(\w+)\s+(.*)")


def detect_version(content: str) -> str:
    return "new" if NEW_PATTERN.search(content) else "old"


def convert_legacy(content: str) -> str:
    converted = []
    for line in content.splitlines():
        if not line.strip():
            continue
        match = LEGACY_LINE.match(line)
        if not match:
            raise ValueError("unconvertible")
        ts, level, log_type, details = match.groups()
        converted.append(f"[{ts}] [{level}] {log_type} {details}")
    return "\n".join(converted)


def upgrade_file(path: str) -> None:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if detect_version(content) == "new":
        return
    try:
        converted = convert_legacy(content)
    except ValueError:
        print(f"跳过无法转换的日志: {os.path.basename(path)}")
        return
    backup = path + ".bak"
    shutil.copy2(path, backup)
    with open(path, "w", encoding="utf-8") as f:
        f.write(converted)
    print(f"已升级 {os.path.basename(path)}，备份保存至 {backup}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Upgrade legacy BetterGI logs")
    parser.add_argument("log_dir", nargs="?", default=None, help="目录，默认为BETTERGI_PATH/log")
    args = parser.parse_args()
    log_dir = args.log_dir or os.path.join(os.getenv("BETTERGI_PATH", ""), "log")
    if not os.path.isdir(log_dir):
        print(f"日志目录不存在: {log_dir}")
        return
    for name in os.listdir(log_dir):
        if name.endswith(".log"):
            upgrade_file(os.path.join(log_dir, name))


if __name__ == "__main__":
    main()
