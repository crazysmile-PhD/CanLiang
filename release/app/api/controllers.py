"""
控制器模块
封装接口的业务逻辑
"""
import logging
from typing import Dict, List, Any

import argparse
import os
import threading
import time

import numpy as np
from flask import Response

from app.infrastructure.manager import LogDataManager
from app.infrastructure.database import DatabaseManager
from app.infrastructure.utils import check_dict_empty
from app.api.preview import (
    DEFAULT_PREVIEW_MODE,
    PreviewModeError,
    ensure_browser_capable_mode,
    normalize_preview_mode,
    preview_mode_requires_external_client,
    preview_mode_is_disabled,
    preview_mode_supports_browser,
)

try:  # OpenCV 在CI环境中可能不可用
    import cv2  # type: ignore
except ImportError:  # pragma: no cover - 依赖缺失时退化为占位实现
    import sys
    import types

    class _FakeEncodedArray:
        def __init__(self, array: np.ndarray) -> None:
            self._buffer = np.asarray(array, dtype=np.uint8)

        def tobytes(self) -> bytes:
            return self._buffer.tobytes()

    def _fake_imencode(ext: str, frame: np.ndarray, params=None):  # pragma: no cover
        return True, _FakeEncodedArray(frame)

    def _fake_cvt_color(frame: np.ndarray, _code: int):  # pragma: no cover
        return np.array(frame, copy=True)

    def _fake_rectangle(image: np.ndarray, pt1, pt2, color, _thickness):  # pragma: no cover
        x1, y1 = pt1
        x2, y2 = pt2
        image[max(0, y1):max(0, y2), max(0, x1):max(0, x2)] = color
        return image

    def _fake_destroy_all_windows():  # pragma: no cover
        return None

    class _FakeCuda:  # pragma: no cover
        @staticmethod
        def getCudaEnabledDeviceCount() -> int:
            return 0

    cv2 = types.ModuleType("cv2")  # type: ignore
    cv2.IMWRITE_JPEG_QUALITY = 1  # type: ignore[attr-defined]
    cv2.COLOR_BGRA2BGR = 0  # type: ignore[attr-defined]
    cv2.imencode = _fake_imencode  # type: ignore[attr-defined]
    cv2.cvtColor = _fake_cvt_color  # type: ignore[attr-defined]
    cv2.rectangle = _fake_rectangle  # type: ignore[attr-defined]
    cv2.destroyAllWindows = _fake_destroy_all_windows  # type: ignore[attr-defined]
    cv2.cuda = _FakeCuda()  # type: ignore[attr-defined]
    sys.modules["cv2"] = cv2

try:  # Windows API 仅在Windows平台可用
    import win32api  # type: ignore
    import win32con  # type: ignore
    import win32gui  # type: ignore
    import win32process  # type: ignore
    import win32ui  # type: ignore
except ImportError:  # pragma: no cover - Linux环境下缺失pywin32
    win32api = win32con = win32gui = win32process = win32ui = None  # type: ignore

try:
    import psutil  # 添加psutil导入用于系统信息获取
except ImportError:  # pragma: no cover - 理论上应存在
    psutil = None  # type: ignore


def _blank_frame(width: int = 640, height: int = 480) -> np.ndarray:
    """返回一个纯黑帧，用于缺失底层依赖时的降级处理。"""

    return np.zeros((height, width, 3), dtype=np.uint8)


WINDOWS_CAPTURE_AVAILABLE = all(
    module is not None for module in (win32api, win32con, win32gui, win32process, win32ui)
)


def _desktop_hwnd() -> int | None:
    """返回桌面窗口句柄，若依赖缺失则返回None。"""

    if not WINDOWS_CAPTURE_AVAILABLE:
        return None
    try:
        return win32gui.GetDesktopWindow()  # type: ignore[union-attr]
    except Exception:
        return None


logger = logging.getLogger(__name__)

class LogController:
    """
    日志控制器
    处理日志相关的业务逻辑
    """
    
    def __init__(self, log_dir: str):
        """
        初始化日志控制器
        
        Args:
            log_dir: 日志目录路径
        """
        self.log_manager = LogDataManager(log_dir)
    
    def get_log_list(self) -> Dict[str, List[str]]:
        """
        获取日志文件列表
        
        Returns:
            Dict[str, List[str]]: 包含日志文件列表的字典，格式：{'list': ['20250501']}
        """
        try:
            if not self.log_manager.log_list:
                log_list = self.log_manager.get_log_list()
            else:
                log_list = self.log_manager.log_list
            
            # 最新的日志排在前面
            log_list.reverse()
            return {'list': log_list}
        except Exception as e:
            logger.error(f"获取日志列表时发生错误: {e}")
            return {'list': []}
    
    def get_log_data(self) -> Dict[str, Any]:
        """
        获取日志分析数据
        
        Returns:
            Dict[str, Any]: 包含持续时间和物品数据的字典，格式：{
                'duration': duration_dict,
                'item': item_dict
            }
        """
        try:
            # 检查数据是否为空，如果为空则重新加载
            duration_data = self.log_manager.get_duration_data()
            item_data = self.log_manager.get_item_data()
            
            return {
                'duration': duration_data,
                'item': item_data
            }
        except Exception as e:
            logger.error(f"获取日志数据时发生错误: {e}")
            return {
                'duration': {'日期': [], '持续时间': []},
                'item': {'物品名称': [], '时间': [], '日期': [], '归属配置组': []}
            }


class WebhookController:
    """
    Webhook控制器
    处理webhook相关的业务逻辑
    """
    
    def __init__(self, log_dir: str):
        """
        初始化webhook控制器
        
        Args:
            log_dir: 日志目录路径
        """
        # 初始化数据库管理器
        db_path = os.path.join(log_dir, 'CanLiangData.db')
        self.db_manager = DatabaseManager(db_path)
    
    def save_data(self, dict_list: Dict) -> Dict[str, Any]:
        """
        保存webhook数据
        
        Args:
            dict_list: 包含webhook数据的字典，必须包含'event'字段
            
        Returns:
            Dict[str, Any]: 操作结果，包含success状态和message信息
        """
        try:
            # 验证必需字段
            if 'event' not in dict_list:
                return {
                    'success': False,
                    'message': '缺少必需的event字段'
                }
            
            # 保存数据到数据库
            success = self.db_manager.save_webhook_data(dict_list)
            
            if success:
                return {
                    'success': True,
                    'message': '数据保存成功'
                }
            else:
                return {
                    'success': False,
                    'message': '数据保存失败'
                }
                
        except Exception as e:
            logger.error(f"保存webhook数据时发生错误: {e}")
            return {
                'success': False,
                'message': f'服务器内部错误: {str(e)}'
            }
    
    def get_webhook_data(self, limit: int = 100) -> Dict[str, Any]:
        """
        获取webhook数据列表
        
        Args:
            limit: 返回记录数限制
            
        Returns:
            Dict[str, Any]: 包含数据列表的字典
        """
        try:
            data_list = self.db_manager.get_webhook_data(limit)
            return {
                'success': True,
                'data': data_list,
                'count': len(data_list)
            }
        except Exception as e:
            logger.error(f"获取webhook数据时发生错误: {e}")
            return {
                'success': False,
                'message': f'获取数据失败: {str(e)}',
                'data': [],
                'count': 0
            }
    


class StreamController:
    """
    推流控制器
    处理屏幕捕获和实时推流功能
    """
    
    def __init__(
        self,
        target_app: str = "yuanshen.exe",
        preview_mode: str = DEFAULT_PREVIEW_MODE,
    ):
        """
        初始化推流控制器

        Args:
            target_app: 目标应用程序名称，默认为yuanshen.exe
        """
        self.target_app = target_app
        self.set_preview_mode(preview_mode)
        self.is_streaming = False
        self.hwnd = None
        self._gpu_available = False

        if cv2 is not None:
            try:  # pragma: no cover - GPU可用性与运行环境相关
                self._gpu_available = cv2.cuda.getCudaEnabledDeviceCount() > 0  # type: ignore[attr-defined]
            except Exception:
                self._gpu_available = False
        
    def set_preview_mode(self, preview_mode: str) -> None:
        """Update the controller preview mode using canonical validation."""

        self.preview_mode = normalize_preview_mode(preview_mode)

    def _ensure_preview_available(self) -> None:
        """Validate that the current preview mode supports MJPEG streaming."""

        if preview_mode_is_disabled(self.preview_mode):
            raise PreviewModeError(
                "实时预览已被禁用，请使用 --preview-mode 启用。",
                preview_mode=self.preview_mode,
            )

        if preview_mode_requires_external_client(self.preview_mode):
            raise PreviewModeError(
                "Sunshine 模式仅支持 Sunshine 客户端，不提供浏览器内预览。",
                preview_mode=self.preview_mode,
            )

        ensure_browser_capable_mode(self.preview_mode)

    def find_window_by_process_name(self, process_name: str) -> int:
        """
        根据进程名查找窗口句柄

        Args:
            process_name: 进程名称

        Returns:
            int: 窗口句柄，如果未找到返回0
        """
        if not WINDOWS_CAPTURE_AVAILABLE:
            logger.warning("当前环境缺少Windows窗口枚举依赖，无法查找进程 %s 的窗口", process_name)
            return 0

        def enum_windows_proc(hwnd, lParam):
            """枚举窗口回调函数"""
            if win32gui.IsWindowVisible(hwnd):
                try:
                    # 获取窗口对应的进程ID
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    
                    # 尝试获取进程句柄，使用更低的权限要求
                    process_handle = None
                    current_process_name = None
                    
                    try:
                        # 首先尝试使用最小权限
                        process_handle = win32api.OpenProcess(
                            win32con.PROCESS_QUERY_LIMITED_INFORMATION, 
                            False, 
                            pid
                        )
                        # 获取进程路径和名称
                        process_path = win32process.GetModuleFileNameEx(process_handle, 0)
                        current_process_name = os.path.basename(process_path).lower()
                    except:
                        # 如果最小权限失败，尝试使用标准权限
                        try:
                            process_handle = win32api.OpenProcess(
                                win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, 
                                False, 
                                pid
                            )
                            process_path = win32process.GetModuleFileNameEx(process_handle, 0)
                            current_process_name = os.path.basename(process_path).lower()
                        except:
                            # 如果都失败，尝试使用psutil作为备选方案
                            try:
                                import psutil
                                process = psutil.Process(pid)
                                current_process_name = process.name().lower()
                            except:
                                # 如果所有方法都失败，跳过这个进程
                                pass
                    
                    # 关闭进程句柄（如果成功打开了）
                    if process_handle:
                        win32api.CloseHandle(process_handle)
                    
                    # 检查进程名是否匹配
                    if current_process_name and current_process_name == process_name.lower():
                        logger.debug(f"找到匹配的进程: {current_process_name}, 窗口句柄: {hwnd}")
                        lParam.append(hwnd)
                        return False  # 停止枚举
                        
                except Exception as e:
                    logger.debug(f"枚举窗口时发生错误: {e}")
                    pass
            return True
        
        logger.debug(f"开始查找进程: {process_name}")
        windows = []
        win32gui.EnumWindows(enum_windows_proc, windows)
        
        if windows:
            logger.debug(f"成功找到进程 {process_name} 的窗口句柄: {windows[0]}")
        else:
            logger.warning(f"未找到进程 {process_name} 的窗口")
            
        return windows[0] if windows else 0
    
    def capture_window(self, hwnd: int) -> np.ndarray:
        """
        捕获指定窗口的屏幕内容

        Args:
            hwnd: 窗口句柄

        Returns:
            np.ndarray: 捕获的图像数据
        """
        try:
            if not WINDOWS_CAPTURE_AVAILABLE:
                logger.warning("缺少Windows捕获依赖，返回占位帧")
                return _blank_frame()

            desktop = _desktop_hwnd()
            is_desktop = desktop is not None and hwnd == desktop

            # 检查是否为桌面窗口
            if is_desktop:
                # 桌面截图：使用主显示器的完整屏幕
                return self._capture_desktop()
            else:
                # 普通窗口截图
                return self._capture_normal_window(hwnd)
                
        except Exception as e:
            logger.error(f"捕获窗口时发生错误: {e}")
            return np.zeros((480, 640, 3), dtype=np.uint8)
    
    def _capture_desktop(self) -> np.ndarray:
        """
        捕获桌面屏幕内容（主显示器），支持DPI感知

        Returns:
            np.ndarray: 捕获的图像数据
        """
        try:
            if not WINDOWS_CAPTURE_AVAILABLE or cv2 is None:
                logger.warning("桌面捕获依赖缺失，返回占位帧")
                return _blank_frame()

            # 设置DPI感知，确保获取真实的屏幕尺寸
            try:
                import ctypes
                from ctypes import wintypes
                
                # 设置进程DPI感知
                ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
            except:
                # 如果设置失败，尝试旧版本的DPI感知设置
                try:
                    ctypes.windll.user32.SetProcessDPIAware()
                except:
                    pass
            
            # 获取真实的屏幕尺寸（考虑DPI缩放）
            screen_width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
            screen_height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
            screen_left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
            screen_top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
            
            # 如果虚拟屏幕尺寸为0，则使用主屏幕尺寸
            if screen_width == 0 or screen_height == 0:
                screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
                screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
                screen_left = 0
                screen_top = 0
            
            # logger.info(f"屏幕尺寸: {screen_width}x{screen_height}, 偏移: ({screen_left}, {screen_top})")
            
            # 获取桌面设备上下文
            desktop_dc = win32gui.GetDC(0)  # 获取整个屏幕的DC
            img_dc = win32ui.CreateDCFromHandle(desktop_dc)
            mem_dc = img_dc.CreateCompatibleDC()
            
            # 创建位图对象
            screenshot = win32ui.CreateBitmap()
            screenshot.CreateCompatibleBitmap(img_dc, screen_width, screen_height)
            mem_dc.SelectObject(screenshot)
            
            # 截图到内存设备上下文，考虑虚拟屏幕偏移
            mem_dc.BitBlt((0, 0), (screen_width, screen_height), img_dc, (screen_left, screen_top), win32con.SRCCOPY)
            
            # 获取位图数据
            bmpstr = screenshot.GetBitmapBits(True)
            
            # 转换为numpy数组
            img = np.frombuffer(bmpstr, dtype='uint8')
            img.shape = (screen_height, screen_width, 4)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            # 清理资源
            mem_dc.DeleteDC()
            img_dc.DeleteDC()
            win32gui.ReleaseDC(0, desktop_dc)
            win32gui.DeleteObject(screenshot.GetHandle())
            
            return img
            
        except Exception as e:
            logger.error(f"捕获桌面时发生错误: {e}")
            # 返回黑色图像作为fallback
            return _blank_frame(1280, 720)
    
    def _capture_normal_window(self, hwnd: int) -> np.ndarray:
        """
        捕获普通窗口的屏幕内容，支持DPI感知
        
        Args:
            hwnd: 窗口句柄
            
        Returns:
            np.ndarray: 捕获的图像数据
        """
        try:
            if not WINDOWS_CAPTURE_AVAILABLE or cv2 is None:
                logger.warning("窗口捕获依赖缺失，返回占位帧")
                return _blank_frame()

            # 验证窗口句柄有效性
            if not hwnd or hwnd == 0:
                logger.warning("窗口句柄无效（为空或0）")
                return _blank_frame()

            # 检查窗口是否存在且有效
            if not win32gui.IsWindow(hwnd):
                logger.warning(f"窗口句柄 {hwnd} 不是有效的窗口")
                return _blank_frame()

            # 检查窗口是否可见
            if not win32gui.IsWindowVisible(hwnd):
                logger.warning(f"窗口句柄 {hwnd} 对应的窗口不可见")
                return _blank_frame()
            
            # 设置DPI感知
            try:
                import ctypes
                # 设置进程DPI感知
                ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
            except:
                try:
                    ctypes.windll.user32.SetProcessDPIAware()
                except:
                    pass
            
            # 获取窗口矩形
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top
            
            # 检查窗口尺寸是否有效
            if width <= 0 or height <= 0:
                logger.warning(f"窗口尺寸无效: {width}x{height}")
                return _blank_frame()
            
            # logger.info(f"窗口尺寸: {width}x{height}, 位置: ({left}, {top})")
            
            # 获取窗口设备上下文
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            
            # 创建位图对象
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)
            
            # 截图到内存设备上下文
            saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
            
            # 获取位图信息
            bmpstr = saveBitMap.GetBitmapBits(True)
            
            # 转换为numpy数组
            img = np.frombuffer(bmpstr, dtype='uint8')
            img.shape = (height, width, 4)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            # 如果是指定应用，添加黑色遮罩
            if self.target_app == 'yuanshen.exe':
                # 基准分辨率 3840x2160
                base_width, base_height = 3840, 2160
                
                # 计算缩放比例
                scale_x = width / base_width
                scale_y = height / base_height
                
                # 第一个遮罩区域：左上角(222,374)，右下角(583,448)
                mask1_x1 = int(222 * scale_x)
                mask1_y1 = int(374 * scale_y)
                mask1_x2 = int(583 * scale_x)
                mask1_y2 = int(448 * scale_y)
                
                # 第二个遮罩区域：左上角(3346,2087)，右下角(3731,2149)
                mask2_x1 = int(3346 * scale_x)
                mask2_y1 = int(2087 * scale_y)
                mask2_x2 = int(3731 * scale_x)
                mask2_y2 = int(2149 * scale_y)
                
                # 确保坐标在图像范围内
                mask1_x1 = max(0, min(mask1_x1, width))
                mask1_y1 = max(0, min(mask1_y1, height))
                mask1_x2 = max(0, min(mask1_x2, width))
                mask1_y2 = max(0, min(mask1_y2, height))
                
                mask2_x1 = max(0, min(mask2_x1, width))
                mask2_y1 = max(0, min(mask2_y1, height))
                mask2_x2 = max(0, min(mask2_x2, width))
                mask2_y2 = max(0, min(mask2_y2, height))
                
                # 绘制黑色遮罩
                if mask1_x2 > mask1_x1 and mask1_y2 > mask1_y1:
                    cv2.rectangle(img, (mask1_x1, mask1_y1), (mask1_x2, mask1_y2), (0, 0, 0), -1)
                
                if mask2_x2 > mask2_x1 and mask2_y2 > mask2_y1:
                    cv2.rectangle(img, (mask2_x1, mask2_y1), (mask2_x2, mask2_y2), (0, 0, 0), -1)
            
            # 清理资源
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwndDC)
            
            return img
            
        except Exception as e:
            logger.error(f"捕获普通窗口时发生错误: {e}")
            return _blank_frame()

    def _capture_desktop_optimized(self) -> np.ndarray:
        """为性能测试提供的兼容方法，内部复用桌面捕获实现。"""

        return self._capture_desktop()

    def _capture_normal_window_optimized(self, hwnd: int) -> np.ndarray:
        """为性能测试提供的兼容方法，内部复用窗口捕获实现。"""

        return self._capture_normal_window(hwnd)

    def _cleanup_resources(self) -> None:
        """清理捕获过程中可能创建的系统资源。"""

        if WINDOWS_CAPTURE_AVAILABLE:
            try:
                win32gui.EnumWindows(lambda *_: True, None)  # type: ignore[union-attr]
            except Exception:
                pass
        if cv2 is not None:
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass

    def generate_frames(self):
        """
        生成视频帧的生成器函数
        支持客户端断开连接自动停止推流

        Yields:
            bytes: MJPEG格式的视频帧
        """
        try:
            self._ensure_preview_available()

            if preview_mode_supports_browser(self.preview_mode):
                logger.info(
                    "预览模式 %s 尚未实现专用管线，使用 MJPEG 回退。",
                    self.preview_mode,
                )

            if cv2 is None:
                raise RuntimeError("OpenCV不可用，无法进行视频推流")

            if not WINDOWS_CAPTURE_AVAILABLE:
                logger.warning("缺少Windows推流依赖，生成占位黑屏帧")
                self.is_streaming = True
                while self.is_streaming:
                    frame = _blank_frame()
                    ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    if ret:
                        frame_bytes = buffer.tobytes()
                        yield (
                            b'--frame\r\n'
                            b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
                        )
                    time.sleep(1/30)
                return

            # 查找目标窗口
            if self.target_app == '桌面.exe':
                self.hwnd = _desktop_hwnd()
            else:
                self.hwnd = self.find_window_by_process_name(self.target_app)

            if not self.hwnd:
                logger.warning(f"未找到进程 {self.target_app} 的窗口")
                # 如果找不到窗口，返回黑屏
                self.is_streaming = True
                while self.is_streaming:
                    try:
                        # 返回黑屏
                        frame = _blank_frame()
                        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                        if ret:
                            frame_bytes = buffer.tobytes()
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                        time.sleep(1/30)
                    except GeneratorExit:
                        # 客户端断开连接，主动停止推流
                        logger.info(f"检测到客户端断开连接，停止推流 - 目标应用: {self.target_app}")
                        self.is_streaming = False
                        break
                    except Exception as e:
                        logger.error(f"生成黑屏帧时发生错误: {e}")
                        time.sleep(0.1)
                return

            
            self.is_streaming = True
            logger.info(f"开始推流 - 目标应用: {self.target_app}")
            
            while self.is_streaming:
                try:
                    # 重新验证窗口句柄有效性（窗口可能被关闭）
                    if self.target_app != '桌面.exe':
                        if (not WINDOWS_CAPTURE_AVAILABLE or
                                not win32gui.IsWindow(self.hwnd) or  # type: ignore[union-attr]
                                not win32gui.IsWindowVisible(self.hwnd)):  # type: ignore[union-attr]
                            logger.warning(f"窗口句柄 {self.hwnd} 已失效，重新查找窗口")
                            self.hwnd = self.find_window_by_process_name(self.target_app)
                            if not self.hwnd:
                                logger.warning(f"无法重新找到进程 {self.target_app} 的窗口，返回黑屏")
                                frame = _blank_frame()
                                self.is_streaming = False
                            else:
                                frame = self.capture_window(self.hwnd)
                        else:
                            frame = self.capture_window(self.hwnd)
                    else:
                        # 桌面窗口
                        frame = self.capture_window(self.hwnd)
                    
                    # 编码为JPEG
                    ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    if ret:
                        frame_bytes = buffer.tobytes()
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    
                    # 控制帧率（约30fps）
                    time.sleep(1/30)
                    
                except GeneratorExit:
                    # 客户端断开连接，主动停止推流
                    logger.info(f"检测到客户端断开连接，停止推流 - 目标应用: {self.target_app}")
                    self.is_streaming = False
                    break
                except Exception as e:
                    logger.error(f"生成视频帧时发生错误: {e}")
                    time.sleep(0.1)
        
        finally:
            # 确保推流状态被正确设置为停止
            if self.is_streaming:
                self.is_streaming = False
                logger.info(f"推流已停止 - 目标应用: {self.target_app}")
    
    def start_stream(self) -> Response:
        """
        启动视频流

        Returns:
            Response: Flask Response对象，包含MJPEG视频流
        """
        self._ensure_preview_available()
        return Response(
            self.generate_frames(),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )
    
    def stop_stream(self):
        """
        停止视频流
        """
        self.is_streaming = False
        logger.info("视频流已停止")
    
    def get_stream_info(self) -> Dict[str, Any]:
        """
        获取推流信息

        Returns:
            Dict[str, Any]: 推流状态信息
        """
        desktop = _desktop_hwnd()
        return {
            'target_app': self.target_app,
            'is_streaming': self.is_streaming,
            'window_found': bool(
                self.hwnd and desktop is not None and self.hwnd != desktop
            ),
            'hwnd': self.hwnd,
            'preview_mode': self.preview_mode,
        }
    
    def get_available_programs(self) -> List[str]:
        """
        获取当前桌面上可以被推流的程序窗口列表

        Returns:
            List[str]: 可推流的程序名称列表（.exe文件名）
        """
        if not WINDOWS_CAPTURE_AVAILABLE:
            logger.warning("当前环境缺少窗口枚举依赖，返回空程序列表")
            return []

        def enum_windows_proc(hwnd, lParam:list):
            """枚举窗口回调函数"""
            if win32gui.IsWindowVisible(hwnd):
                try:
                    # 获取窗口标题（允许空标题，但记录用于调试）
                    window_title = win32gui.GetWindowText(hwnd)
                    
                    # 获取窗口对应的进程ID
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    
                    # 尝试获取进程句柄，使用更低的权限要求
                    process_handle = None
                    process_name = None
                    
                    try:
                        # 首先尝试使用最小权限
                        process_handle = win32api.OpenProcess(
                            win32con.PROCESS_QUERY_LIMITED_INFORMATION, 
                            False, 
                            pid
                        )
                        # 获取进程路径和名称
                        process_path = win32process.GetModuleFileNameEx(process_handle, 0)
                        process_name = os.path.basename(process_path).lower()
                    except:
                        # 如果最小权限失败，尝试使用标准权限
                        try:
                            process_handle = win32api.OpenProcess(
                                win32con.PROCESS_QUERY_INFORMATION, 
                                False, 
                                pid
                            )
                            process_path = win32process.GetModuleFileNameEx(process_handle, 0)
                            process_name = os.path.basename(process_path).lower()
                        except:
                            # 如果都失败了，尝试通过psutil获取进程名称
                            try:
                                import psutil
                                process = psutil.Process(pid)
                                process_name = process.name().lower()
                            except:
                                # 最后的备选方案：跳过这个进程
                                return True
                    
                    if process_name:
                        # 系统进程黑名单（更完整的列表）
                        system_processes = {
                            'dwm.exe', 'winlogon.exe', 'csrss.exe', 'explorer.exe',
                            'svchost.exe', 'lsass.exe', 'smss.exe', 'wininit.exe',
                            'services.exe', 'spoolsv.exe', 'conhost.exe', 'dllhost.exe',
                            'rundll32.exe', 'taskhostw.exe', 'sihost.exe', 'ctfmon.exe',
                            'fontdrvhost.exe', 'winlogon.exe', 'lsm.exe','nvidia overlay.exe',
                            'textinputhost.exe'
                        }
                        
                        # 只包含.exe文件，排除系统进程
                        if (process_name.endswith('.exe') and 
                            process_name not in system_processes and
                            not process_name.startswith('windows') and
                            not process_name.startswith('microsoft')):
                            
                            # 检查窗口尺寸，放宽尺寸要求
                            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                            width = right - left
                            height = bottom - top
                            
                            # 降低尺寸要求（50x50像素），并允许最小化的窗口
                            # if width >= 50 and height >= 50:
                                # 记录调试信息
                            # logger.debug(f"找到程序: {process_name}, 标题: '{window_title}', 尺寸: {width}x{height}")
                            lParam.append(process_name)
                            # else:
                            #     logger.debug(f"程序 {process_name} 因尺寸过小被过滤: {width}x{height}")
                        else:
                            # logger.debug(f"程序 {process_name} 被系统进程过滤器排除")
                            pass
                    
                    # 关闭进程句柄（如果成功打开了）
                    if process_handle:
                        win32api.CloseHandle(process_handle)
                    
                except Exception as e:
                    # 记录无法访问的进程（通常是权限问题）
                    logger.debug(f"无法访问进程信息: {e}")
                    pass
            return True
        
        try:
            programs = []
            # logger.info("开始扫描桌面程序...")
            win32gui.EnumWindows(enum_windows_proc, programs)
            
            # 去重并排序
            unique_programs = list(set(programs))
            unique_programs.sort()
            
            logger.debug(f"扫描完成，找到 {len(unique_programs)} 个可推流的程序: {unique_programs}")
            return unique_programs
            
        except Exception as e:
            logger.error(f"获取程序列表时发生错误: {e}")
            return []


class SystemInfoController:
    """
    系统信息控制器
    用于获取系统资源使用情况
    """
    
    def __init__(self):
        """
        初始化系统信息控制器
        """
        pass
    
    def get_memory_usage(self) -> float:
        """
        获取内存利用率百分比
        
        Returns:
            float: 内存利用率百分比，保留1位小数
        """
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            return round(memory_percent, 1)
        except Exception as e:
            logger.error(f"获取内存使用率时发生错误: {e}")
            return 0.0
    
    def get_cpu_usage(self, interval: float = 1.0) -> float:
        """
        获取CPU利用率百分比
        
        Args:
            interval: 采样间隔时间（秒），默认1秒
            
        Returns:
            float: CPU利用率百分比，保留1位小数
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=interval)
            return round(cpu_percent, 1)
        except Exception as e:
            logger.error(f"获取CPU使用率时发生错误: {e}")
            return 0.0
    
    def get_system_info(self) -> Dict[str, float]:
        """
        获取系统信息汇总
        
        Returns:
            Dict[str, float]: 包含内存和CPU使用率的字典，格式：{
                'memory_usage': 内存使用率百分比,
                'cpu_usage': CPU使用率百分比
            }
        """
        try:
            memory_usage = self.get_memory_usage()
            cpu_usage = self.get_cpu_usage()
            
            return {
                'memory_usage': memory_usage,
                'cpu_usage': cpu_usage
            }
        except Exception as e:
            logger.error(f"获取系统信息时发生错误: {e}")
            return {
                'memory_usage': 0.0,
                'cpu_usage': 0.0
            }

