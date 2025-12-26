"""
MacroTool 单元测试
"""
import sys
import os
import json
import unittest
from unittest.mock import patch
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from financial_crew.tools.macro_tool import MacroTool

class TestMacroTool(unittest.TestCase):
    
    def setUp(self):
        self.tool = MacroTool()

    @patch('financial_crew.tools.macro_tool.fetch_macro_data')
    def test_fetch_gdp(self, mock_fetch_macro_data):
        """测试获取 GDP 数据"""
        mock_df = pd.DataFrame({
            "季度": ["2023年第4季度", "2023年第3季度"],
            "国内生产总值-绝对值": [1000, 900]
        })
        mock_fetch_macro_data.return_value = mock_df
        
        result = self.tool._run(indicator="gdp", limit=1)
        data = json.loads(result)
        
        self.assertEqual(data["indicator"], "gdp")
        self.assertEqual(len(data["data"]), 1)
        self.assertEqual(data["data"][0]["国内生产总值-绝对值"], 1000)

    def test_unsupported_indicator(self):
        """测试不支持的指标"""
        result = self.tool._run(indicator="unknown")
        data = json.loads(result)
        self.assertEqual(data["status"], "failed")

if __name__ == '__main__':
    unittest.main()
