"""
OHLCVTool 单元测试 (集成 AKShare)
"""
import sys
import os
import json
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd

# 添加 src 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from financial_crew.tools.ohlcv_tool import OHLCVTool

class TestOHLCVTool(unittest.TestCase):
    
    def setUp(self):
        self.tool = OHLCVTool()

    @patch('financial_crew.tools.ohlcv_tool.fetch_stock_data')
    def test_fetch_single_stock_success(self, mock_fetch_stock_data):
        """测试成功获取单只股票数据"""
        # 模拟 AKShare 返回数据
        mock_df = pd.DataFrame({
            "Date": ["2023-01-01", "2023-01-02"],
            "Open": [10.0, 11.0],
            "Close": [11.0, 12.0],
            "High": [12.0, 13.0],
            "Low": [9.0, 10.0],
            "Volume": [1000, 2000],
            "stock_code": ["600519", "600519"]
        })
        mock_fetch_stock_data.return_value = mock_df
        
        result = self.tool._run(stock_code="600519")
        data = json.loads(result)
        
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        # 验证列名映射
        self.assertIn("Open", data[0])
        self.assertIn("Close", data[0])
        self.assertEqual(data[0]["Open"], 10.0)
        self.assertEqual(data[0]["stock_code"], "600519")

    @patch('financial_crew.tools.ohlcv_tool.fetch_stock_data')
    def test_fetch_batch_stocks(self, mock_fetch_stock_data):
        """测试批量获取股票数据"""
        mock_df = pd.DataFrame({
            "Date": ["2023-01-01"],
            "Open": [10.0],
            "Close": [11.0],
            "High": [12.0],
            "Low": [9.0],
            "Volume": [1000],
            "stock_code": ["600519"]
        })
        mock_fetch_stock_data.return_value = mock_df
        
        result = self.tool._run(stock_code="600519,000001")
        data = json.loads(result)
        
        # 应该调用两次 fetch_stock_data
        self.assertEqual(mock_fetch_stock_data.call_count, 2)
        self.assertEqual(len(data), 2) # 两个股票各一条数据

    def test_invalid_input(self):
        """测试无效输入"""
        # 实际网络请求测试 (可选，如果环境允许)
        pass

if __name__ == '__main__':
    unittest.main()
