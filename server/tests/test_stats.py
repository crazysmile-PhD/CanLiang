import json
import sys
from importlib import reload
from pathlib import Path

import pytest


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('STATS_DATA_DIR', str(tmp_path))
    monkeypatch.setenv('BETTERGI_PATH', str(tmp_path))
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    import server.app as app_module
    reload(app_module)
    (tmp_path / '2023-01-01.jsonl').write_text(json.dumps({'v': 1}) + '\n')
    (tmp_path / '2023-01-02.jsonl').write_text(json.dumps({'v': 2}) + '\n')
    return app_module.app.test_client()


def test_get_stats(client):
    resp = client.get('/api/stats?from=2023-01-01&to=2023-01-02')
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data['data']) == 2


def test_get_stats_invalid_range(client):
    resp = client.get('/api/stats?from=2023-01-02&to=2023-01-01')
    assert resp.status_code == 400


def test_export_csv(client):
    resp = client.get('/api/stats/export?from=2023-01-01&to=2023-01-02&format=csv')
    assert resp.status_code == 200
    assert resp.headers['Content-Disposition'].startswith('attachment;')
    text = resp.get_data(as_text=True)
    assert 'v' in text


def test_export_invalid_format(client):
    resp = client.get('/api/stats/export?from=2023-01-01&to=2023-01-02&format=xml')
    assert resp.status_code == 400
