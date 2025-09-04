import argparse
import logging
import os
import subprocess
import sys
import threading
import time
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('BetterGI初始化')

# Parse command line arguments
parser = argparse.ArgumentParser(description='参量质变仪，用于解析BetterGI日志。')
parser.add_argument('-bgi', '--bgi_path', default=None, help='BetterGI程序路径')
parser.add_argument('-port', '--port', default=3000, help='网页前端使用的本地端口号')
parser.add_argument('-no', '--do_not_open_website', action='store_true', help='默认启动时打开网页，传递此参数以禁用')
args = parser.parse_args()
install_path = args.bgi_path
web_port = args.port
do_not_open_website = args.do_not_open_website
send_png_by_webhook_to_Lark = None


def find_bettergi_install_path() -> Optional[str]:
    """检测BetterGI的安装路径"""
    logger.info("正在检测BetterGI安装路径...")

    if os.name == 'nt':  # Windows系统
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall")
            for i in range(0, winreg.QueryInfoKey(key)[0]):
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkey = winreg.OpenKey(key, subkey_name)
                    try:
                        display_name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                        if "BetterGI" in display_name:
                            install_location, _ = winreg.QueryValueEx(subkey, "InstallLocation")
                            winreg.CloseKey(subkey)
                            winreg.CloseKey(key)
                            return install_location
                    except (FileNotFoundError, OSError):
                        pass
                    finally:
                        winreg.CloseKey(subkey)
                except (FileNotFoundError, OSError, WindowsError):
                    continue
            winreg.CloseKey(key)
        except Exception as e:
            logger.error(f"检测BetterGI安装路径时出错: {e}")

    elif os.name == 'posix':  # Linux系统
        try:
            result = subprocess.run(['which', 'BetterGI'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            logger.error(f"检测BetterGI安装路径时出错: {e}")

    return None


def open_browser_after_start():
    """在Flask应用启动后打开浏览器"""

    def target():
        time.sleep(2)  # 等待服务器启动
        url = f'http://127.0.0.1:{web_port}'
        try:
            subprocess.run(['start', url], shell=True, check=True)
            logger.info(f"成功启动浏览器并导航到 {url}")
        except subprocess.CalledProcessError as e:
            logger.error(f"启动浏览器时出现错误: {e}")
        except Exception as e:
            logger.error(f"启动浏览器时出现错误: {e}")
            try:
                subprocess.run(['start', url], check=True)
            except Exception as e:
                logger.error(f"启动浏览器时出现错误: {e}")

    threading.Thread(target=target).start()


if not do_not_open_website:
    open_browser_after_start()

# 检测BetterGI安装路径并设置环境变量
if install_path is None:
    logger.info('正在尝试查找BetterGI安装路径。')
    install_path = find_bettergi_install_path()
    if install_path is None:
        logger.error('未找到BetterGI安装路径。')
        sys.exit(1)
else:
    logger.info(f'已指定BetterGI安装路径为: {install_path}')

# 获取日志目录路径
BGI_LOG_DIR = os.path.join(install_path, 'log')
