import csv
import json

data = [
    {"項目": "蘋果", "數量": 10, "備註": "紅色"},
    {"項目": "香蕉", "數量": 5, "備註": "黃色"},
    {"項目": "葡萄", "數量": 8, "備註": "紫色"},
]

fieldnames = ["項目", "數量", "備註"]

# Write CSV with comma delimiter and UTF-8 with BOM
with open('sample_stats.csv', 'w', encoding='utf-8-sig', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)

# Write JSON preserving Chinese characters
with open('sample_stats.json', 'w', encoding='utf-8') as jsonfile:
    json.dump(data, jsonfile, ensure_ascii=False, indent=2)
    jsonfile.write('\n')
