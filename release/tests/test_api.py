"""
API层测试模块
测试API接口的功能
"""
import unittest
import json
from unittest.mock import patch, MagicMock
from app import create_app
from app.api.views import init_controllers


class TestAPI(unittest.TestCase):
    """
    API测试类
    """
    
    def setUp(self):
        """
        测试前的设置
        """
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # 模拟初始化控制器
        with patch('app.api.views.LogController') as mock_controller:
            init_controllers('/fake/log/dir', preview_mode='none')
    
    def test_serve_index(self):
        """
        测试首页路由
        """
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.api.views.log_controller')
    def test_get_log_list_api(self, mock_controller):
        """
        测试获取日志列表API
        """
        # 模拟控制器返回数据
        mock_controller.get_log_list.return_value = {'list': ['20250101', '20250102']}
        
        response = self.client.get('/api/LogList')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('list', data)
        self.assertEqual(len(data['list']), 2)
    
    @patch('app.api.views.log_controller')
    def test_analyse_log(self, mock_controller):
        """
        测试日志分析API
        """
        # 模拟控制器返回数据
        mock_data = {
            'duration': {'日期': ['20250101'], '持续时间': [3600]},
            'item': {'物品名称': ['测试物品'], '时间': ['12:00:00'], '日期': ['20250101'], '归属配置组': ['测试组']}
        }
        mock_controller.get_log_data.return_value = mock_data
        
        response = self.client.get('/api/LogData')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('duration', data)
        self.assertIn('item', data)
    
    def test_controller_not_initialized(self):
        """
        测试控制器未初始化的情况
        """
        # 重新创建应用但不初始化控制器
        app = create_app()
        app.config['TESTING'] = True
        client = app.test_client()

        response = client.get('/api/LogList')
        self.assertEqual(response.status_code, 500)

        data = json.loads(response.data)
        self.assertIn('error', data)

    @patch('app.api.views.stream_manager')
    def test_init_controllers_configures_preview_mode(self, mock_manager):
        with patch('app.api.views.LogController'), patch('app.api.views.WebhookController'):
            init_controllers('/fake/log/dir', preview_mode='web-rtc')

        mock_manager.set_preview_mode.assert_called_once_with('web-rtc')

    @patch('app.api.views.stream_manager')
    def test_video_stream_blocked_when_preview_disabled(self, mock_manager):
        mock_manager.get_preview_mode.return_value = 'none'

        response = self.client.get('/api/stream?app=yuanshen.exe')

        self.assertEqual(response.status_code, 503)
        data = json.loads(response.data)
        self.assertEqual(data['preview_mode'], 'none')
        self.assertIn('实时预览已关闭', data['error'])

    @patch('app.api.views.stream_manager')
    def test_video_stream_returns_sunshine_message(self, mock_manager):
        mock_manager.get_preview_mode.return_value = 'sunshine'

        response = self.client.get('/api/stream?app=yuanshen.exe')

        self.assertEqual(response.status_code, 503)
        data = json.loads(response.data)
        self.assertEqual(data['preview_mode'], 'sunshine')
        self.assertIn('Sunshine 模式不提供浏览器内预览', data['error'])

    @patch('app.api.views.stream_manager')
    def test_video_stream_uses_manager_when_preview_enabled(self, mock_manager):
        mock_controller = MagicMock()
        mock_manager.get_preview_mode.return_value = 'web-rtc'
        mock_manager.get_controller.return_value = mock_controller
        mock_controller.start_stream.return_value = 'stream-response'

        response = self.client.get('/api/stream?app=yuanshen.exe')

        self.assertEqual(response.status_code, 200)
        mock_manager.get_controller.assert_called_once_with('yuanshen.exe')
        mock_controller.start_stream.assert_called_once_with()
        self.assertEqual(response.data, b'stream-response')


if __name__ == '__main__':
    unittest.main()
