import sys
import pathlib

def test_emit_product_all_types(tmp_path, monkeypatch):
    monkeypatch.setenv("BETTERGI_PATH", str(tmp_path))
    sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
    from server import events, app

    log_text = (
        "[00:00:01.000] [INFO] Sample\n交互或拾取：\"ItemA\"\n"
        "[00:00:02.000] [INFO] Sample\n交互或拾取：\"ItemB\"\n"
        "[00:00:03.000] [INFO] Sample\n交互或拾取：\"ItemC\"\n"
    )
    log_file = tmp_path / "sample.log"
    log_file.write_text(log_text, encoding="utf-8")

    events.emitted_products.clear()
    app.read_log_file(str(log_file), config_group_id="cfg1", run_id="run1")

    assert [e["productType"] for e in events.emitted_products] == [
        "ItemA",
        "ItemB",
        "ItemC",
    ]
    for e in events.emitted_products:
        assert e["configGroupId"] == "cfg1"
        assert e["runId"] == "run1"
        assert e["qty"] == 1
