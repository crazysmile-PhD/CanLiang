import sys
import types
import numpy as np


def _ensure_module(name: str) -> types.ModuleType:
    module = types.ModuleType(name)
    sys.modules[name] = module
    return module


if 'cv2' not in sys.modules:
    cv2_stub = types.ModuleType('cv2')
    cv2_stub.COLOR_BGRA2BGR = 0
    cv2_stub.IMWRITE_JPEG_QUALITY = 1

    def _identity(image, *_args, **_kwargs):
        return image

    def _imencode(_ext, image, _params=None):
        dummy = np.zeros((1,), dtype=np.uint8)
        return True, dummy

    cv2_stub.cvtColor = _identity
    cv2_stub.imencode = _imencode
    sys.modules['cv2'] = cv2_stub


for module_name in [
    'win32gui', 'win32ui', 'win32con', 'win32api', 'win32process'
]:
    if module_name not in sys.modules:
        module = _ensure_module(module_name)
        if module_name == 'win32con':
            module.PROCESS_QUERY_LIMITED_INFORMATION = 0
            module.PROCESS_QUERY_INFORMATION = 0
            module.PROCESS_VM_READ = 0
            module.SRCCOPY = 0
            module.SM_CXVIRTUALSCREEN = 0
            module.SM_CYVIRTUALSCREEN = 0
            module.SM_XVIRTUALSCREEN = 0
            module.SM_YVIRTUALSCREEN = 0
            module.SM_CXSCREEN = 0
            module.SM_CYSCREEN = 0
        elif module_name == 'win32gui':
            module._desktop_handle = object()

            def _return_true(*_args, **_kwargs):
                return True

            def _enum_windows(callback, param):
                return None

            module.EnumWindows = _enum_windows
            module.IsWindowVisible = _return_true
            module.IsWindow = _return_true
            module.GetDesktopWindow = lambda m=module: m._desktop_handle
            module.GetWindowRect = lambda _hwnd: (0, 0, 100, 100)
            module.GetWindowText = lambda _hwnd: ''
            module.GetDC = lambda _hwnd: 0
            module.ReleaseDC = lambda _hwnd, _dc: None
            module.DeleteObject = lambda _obj: None
        elif module_name == 'win32ui':
            class _DummyBitmap:
                def GetHandle(self):
                    return 0

                def GetBitmapBits(self, *_args, **_kwargs):
                    return b''

            class _DummyDC:
                def __init__(self, *_args, **_kwargs):
                    pass

                def CreateCompatibleDC(self):
                    return self

                def SelectObject(self, *_args, **_kwargs):
                    return None

                def BitBlt(self, *_args, **_kwargs):
                    return None

                def DeleteDC(self):
                    return None

            module.CreateDCFromHandle = lambda _handle, m=module: _DummyDC()
            module.CreateBitmap = lambda m=module: _DummyBitmap()
        elif module_name == 'win32api':
            module.OpenProcess = lambda *_args, **_kwargs: None
            module.CloseHandle = lambda *_args, **_kwargs: None
            module.GetSystemMetrics = lambda *_args, **_kwargs: 0
        elif module_name == 'win32process':
            module.GetWindowThreadProcessId = lambda *_args, **_kwargs: (None, 0)
            module.GetModuleFileNameEx = lambda *_args, **_kwargs: ''
