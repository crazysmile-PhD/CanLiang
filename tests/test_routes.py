import os
import sys
import pandas as pd
import pytest

# Ensure required environment variable before importing the application
os.environ.setdefault('BETTERGI_PATH', '/tmp')
# Ensure repository root on path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mini import app as mini_app


@pytest.fixture
def client():
    """Flask test client."""
    mini_app.app.config['TESTING'] = True
    with mini_app.app.test_client() as client:
        yield client


@pytest.fixture
def seed_log_analyzer():
    """Seed deterministic DataFrames for predictable tests."""
    mini_app.item_dataframe = pd.DataFrame({
        '物品名称': ['ItemA', 'ItemB', 'ItemA'],
        '时间': ['00:00:01', '00:01:00', '00:02:00'],
        '日期': ['20250101', '20250101', '20250102']
    })
    mini_app.duration_dataframe = pd.DataFrame({
        '日期': ['20250101', '20250102'],
        '持续时间（秒）': [120, 180]
    })
    mini_app.log_list = ['20250101', '20250102']
    yield
    mini_app.item_dataframe = pd.DataFrame(columns=['物品名称', '时间', '日期'])
    mini_app.duration_dataframe = pd.DataFrame(columns=['日期', '持续时间（秒）'])
    mini_app.log_list = None


def test_log_list(client, seed_log_analyzer):
    resp = client.get('/api/LogList')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {'list': ['20250102', '20250101']}


def test_analyse_all(client, seed_log_analyzer):
    resp = client.get('/api/analyse', query_string={'date': 'all'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {
        'duration': '5分钟',
        'item_count': {'ItemA': 2, 'ItemB': 1}
    }


def test_analyse_single_date(client, seed_log_analyzer):
    resp = client.get('/api/analyse', query_string={'date': '20250101'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {
        'duration': '2分钟',
        'item_count': {'ItemA': 1, 'ItemB': 1}
    }


def test_analyse_single_date_empty(client, seed_log_analyzer):
    resp = client.get('/api/analyse', query_string={'date': '20250103'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {'duration': '0分钟', 'item_count': {}}


def test_analyse_all_empty(client):
    mini_app.item_dataframe = pd.DataFrame(columns=['物品名称', '时间', '日期'])
    mini_app.duration_dataframe = pd.DataFrame(columns=['日期', '持续时间（秒）'])
    resp = client.get('/api/analyse', query_string={'date': 'all'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {'duration': '0分钟', 'item_count': {}}
