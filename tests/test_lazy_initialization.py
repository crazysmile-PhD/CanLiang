import importlib
import sys
from pathlib import Path


def create_sample_log(path):
    content = (
        "[12:00:00.000] [INFO] Test\n"
        "初始化\n"
        "[12:01:00.000] [INFO] Test\n"
        "交互或拾取：\"苹果\"\n"
    )
    path.write_text(content, encoding="utf-8")


def test_lazy_initialization(tmp_path, monkeypatch):
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    create_sample_log(log_dir / "better-genshin-impact20240101.log")

    monkeypatch.setenv("BETTERGI_PATH", str(tmp_path))

    sys.path.append(str(Path(__file__).resolve().parents[1]))
    app_module = importlib.import_module("mini.app")
    client = app_module.app.test_client()

    assert app_module.log_list is None
    assert app_module.item_dataframe.empty
    assert app_module.duration_dataframe.empty

    analyse_resp = client.get("/api/analyse")
    assert analyse_resp.status_code == 200
    assert analyse_resp.get_json()["item_count"] == {"苹果": 1}

    assert app_module.log_list is not None
    assert not app_module.item_dataframe.empty
    assert not app_module.duration_dataframe.empty

    list_resp = client.get("/api/LogList")
    assert list_resp.status_code == 200
    assert "20240101" in list_resp.get_json()["list"]

