import importlib.util
import os.path
import os
import logging
import subprocess
import sys
from typing import Optional
from flask import Flask, jsonify, request, send_from_directory, current_app
import time
import threading
import argparse

from log_parser import LogAnalyzer

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('BetterGI初始化')

# 全局变量
script_dir = os.path.dirname(os.path.abspath(__file__))

# 获取启动参数
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
    """
    检测BetterGI的安装路径

    返回:
        Optional[str]: 如果找到，返回BetterGI的安装路径；否则返回None
    """
    logger.info("正在检测BetterGI安装路径...")

    if os.name == 'nt':  # Windows系统
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
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
        # 等待一段时间，确保Flask服务器完全启动
        time.sleep(2)
        url = 'http://127.0.0.1:3000'
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

    # 在新线程中执行浏览器打开操作，避免阻塞Flask应用的启动
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

# 创建Flask应用实例，设置静态文件夹路径为'static'
app = Flask(__name__, static_folder='static')

# 实例化日志分析器并存储到应用配置
analyzer = LogAnalyzer(BGI_LOG_DIR)
app.config['analyzer'] = analyzer

# 路由定义
@app.route('/')
def serve_index():
    """
    提供静态资源的路由，返回index.html文件。
    """
    return send_from_directory('static', 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    """
    提供静态资源的路由，返回指定的静态文件。
    """
    return send_from_directory('static', filename)


@app.route('/api/LogList', methods=['GET'])
def get_log_list_api():
    """
    提供日志文件列表的API接口。

    Returns:
        JSON: 包含日志文件列表的JSON响应.例如：{'list': ['20250501']}
    """
    analyzer = current_app.config['analyzer']
    log_list = analyzer.get_log_list()
    return jsonify({'list': list(reversed(log_list))})


@app.route('/api/analyse', methods=['GET'])
def analyse_log():
    """
    提供日志分析的API接口，返回指定日期的日志分析结果。
    请求参数:date='all'
    如果没有all，则返回单个日期的数据。
    Returns:
        JSON: 包含日志分析结果的JSON响应。例如：{
        'duration': string,
        'item_count': {item_name:int}
    }
    """
    analyzer = current_app.config['analyzer']
    date = request.args.get('date', 'all')

    if date == 'all':
        return jsonify(analyzer.analyse_all_logs())
    else:
        return jsonify(analyzer.analyse_single_log(date))


@app.route('/api/item-trend', methods=['GET'])
def item_trend():
    """
    返回单个物品的历史记录。

    Returns:
        JSON: 格式：{
        'data': {‘date':int}
    }
    """
    analyzer = current_app.config['analyzer']
    item_name = request.args.get('item', '')
    if item_name:
        return jsonify(analyzer.analyse_item_history(item_name))
    return jsonify({})


@app.route('/api/duration-trend', methods=['GET'])
def duration_trend():
    """
    返回所有日志中，每天的BGI持续运行时间。

    Returns:
        JSON: 格式：{
        'data': {‘date':int}
    }
    """
    analyzer = current_app.config['analyzer']
    return jsonify(analyzer.analyse_duration_history())


@app.route('/api/total-items-trend', methods=['GET'])
def item_history():
    """
    返回所有日志中，拾取每天拾取总物品的数量。

    Returns:
        JSON: 格式：{
        'data': {‘date':int}
    }
    """
    analyzer = current_app.config['analyzer']
    return jsonify(analyzer.analyse_all_items())


# 启动Flask应用
if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=3000, use_reloader=False)
