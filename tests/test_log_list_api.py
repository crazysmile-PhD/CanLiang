import importlib.util
from pathlib import Path


def _write_log(dir_path: Path, date: str) -> None:
    log_file = dir_path / f"better-genshin-impact{date}.log"
    log_file.write_text(
        "[12:00:00.000] [INFO] Dummy\n交互或拾取：\"苹果\"\n",
        encoding="utf-8",
    )


def test_log_list_consistent_order(tmp_path, monkeypatch):
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    _write_log(log_dir, "20240101")
    _write_log(log_dir, "20240102")
    monkeypatch.setenv("BETTERGI_PATH", str(tmp_path))

    spec = importlib.util.spec_from_file_location(
        "mini.app", Path(__file__).resolve().parents[1] / "mini" / "app.py"
    )
    app_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_module)  # type: ignore[assignment]
    app = app_module.app
    client = app.test_client()

    expected = sorted(["20240101", "20240102"], reverse=True)

    resp1 = client.get("/api/LogList")
    resp2 = client.get("/api/LogList")

    assert resp1.get_json()["list"] == expected
    assert resp2.get_json()["list"] == expected
