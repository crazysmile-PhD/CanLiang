import re


def parse_log(log_content):
    log_pattern = r'\[([^]]+)\] \[([^]]+)\] ([^\n]+)\n?([^\n[]*)'
    matches = re.findall(log_pattern, log_content)

    type_count = {}
    item_count = {}

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
            item_count[item] = item_count.get(item, 0) + 1

    return {
        'type_count': type_count,
        'item_count': item_count,
        'interaction_count': sum(item_count.values()),
        'item_list': list(item_count.keys())
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
        print(result['item_list'])
        print(f"\n交互或拾取的物品总数: {result['interaction_count']} 个")

        print("\n每个交互或拾取物品出现的次数:")
        for item, count in result['item_count'].items():
            print(f"{item}: {count} 次")
