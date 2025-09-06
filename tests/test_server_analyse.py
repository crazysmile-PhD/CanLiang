import importlib.util
import os

spec = importlib.util.spec_from_file_location("server_analyse", os.path.join("server", "analyse.py"))
server_analyse = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server_analyse)

parse_log = server_analyse.parse_log
read_log_file = server_analyse.read_log_file


def sample_log():
    return (
        "[00:00:00.000] [INFO] ClassA\n"
        "交互或拾取：\"苹果\"\n"
        "[00:01:00.000] [INFO] ClassB\n"
        "交互或拾取：\"梨子\"\n"
    )


def test_parse_log_counts_types_and_items():
    result = parse_log(sample_log())
    assert result["type_count"] == {"ClassA": 1, "ClassB": 1}
    assert result["interaction_items"] == ["苹果", "梨子"]
    assert result["interaction_count"] == 2


def test_read_log_file(tmp_path):
    file_path = tmp_path / "log.log"
    file_path.write_text(sample_log(), encoding="utf-8")
    result = read_log_file(str(file_path))
    assert result["interaction_items"] == ["苹果", "梨子"]
