import pytest

from app.api.controllers import StreamController


def test_stream_controller_initial_state():
    controller = StreamController(target_app='test.exe')

    info = controller.get_stream_info()
    assert info['target_app'] == 'test.exe'
    assert info['is_streaming'] is False
    assert info['window_found'] is False


def test_stream_controller_stop_updates_state():
    controller = StreamController(target_app='test.exe')
    controller.is_streaming = True
    controller.hwnd = 123

    controller.stop_stream()

    assert controller.is_streaming is False
    assert controller.get_stream_info()['is_streaming'] is False


def test_generate_frames_returns_black_screen_when_window_missing(monkeypatch):
    controller = StreamController(target_app='missing.exe')

    # Ensure find_window_by_process_name returns 0 to simulate missing window
    monkeypatch.setattr(controller, 'find_window_by_process_name', lambda _name: 0)

    generator = controller.generate_frames()
    first_frame = next(generator)

    assert isinstance(first_frame, (bytes, bytearray))
    assert first_frame.startswith(b'--frame')
    assert controller.is_streaming is True

    # Close generator to trigger cleanup
    generator.close()
    assert controller.is_streaming is False
