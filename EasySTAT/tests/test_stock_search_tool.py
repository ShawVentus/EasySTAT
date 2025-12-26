"""
StockSearchTool 单元测试
"""
import sys
import os
import json
import unittest
from unittest.mock import patch
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from financial_crew.tools.stock_search_tool import StockSearchTool

class TestStockSearchTool(unittest.TestCase):
    
    def setUp(self):
        self.tool = StockSearchTool()

    @patch('financial_crew.tools.stock_search_tool.fetch_all_stocks')
    def test_search_success(self, mock_fetch_all_stocks):
        """测试成功搜索股票"""
        mock_df = pd.DataFrame({
            "代码": ["600519", "000001"],
            "名称": ["贵州茅台", "平安银行"],
            "最新价": [1800.0, 10.0],
            "涨跌幅": [1.0, -0.5]
        })
        mock_fetch_all_stocks.return_value = mock_df
        
        result = self.tool._run(query="茅台")
        data = json.loads(result)
        
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["代码"], "600519")
        self.assertEqual(data[0]["名称"], "贵州茅台")

    @patch('financial_crew.tools.stock_search_tool.fetch_all_stocks')
    def test_search_no_result(self, mock_fetch_all_stocks):
        """测试未搜索到结果"""
        mock_df = pd.DataFrame({
            "代码": ["600519"],
            "名称": ["贵州茅台"],
            "最新价": [1800.0],
            "涨跌幅": [1.0]
        })
        mock_fetch_all_stocks.return_value = mock_df
        
        result = self.tool._run(query="苹果")
        data = json.loads(result)
        
        self.assertEqual(len(data["data"]), 0)
        self.assertIn("未找到", data["message"])

if __name__ == '__main__':
    unittest.main()
