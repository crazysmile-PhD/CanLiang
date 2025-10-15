import pytest

from app.api.controllers import SystemInfoController


def test_system_info_controller_returns_metrics(monkeypatch):
    class DummyMemory:
        percent = 57.3

    def fake_virtual_memory():
        return DummyMemory()

    def fake_cpu_percent(interval=1.0):
        return 41.8

    controller = SystemInfoController()
    monkeypatch.setattr('psutil.virtual_memory', fake_virtual_memory)
    monkeypatch.setattr('psutil.cpu_percent', fake_cpu_percent)

    assert controller.get_memory_usage() == pytest.approx(57.3, rel=1e-3)
    assert controller.get_cpu_usage(interval=0.5) == pytest.approx(41.8, rel=1e-3)

    summary = controller.get_system_info()
    assert summary == {'memory_usage': 57.3, 'cpu_usage': 41.8}


def test_system_info_handles_errors(monkeypatch):
    controller = SystemInfoController()

    def raise_mem():
        raise RuntimeError('mem error')

    def raise_cpu(interval=1.0):
        raise RuntimeError('cpu error')

    monkeypatch.setattr('psutil.virtual_memory', raise_mem)
    monkeypatch.setattr('psutil.cpu_percent', raise_cpu)

    assert controller.get_memory_usage() == 0.0
    assert controller.get_cpu_usage() == 0.0
    summary = controller.get_system_info()
    assert summary['memory_usage'] == 0.0
    assert summary['cpu_usage'] == 0.0
