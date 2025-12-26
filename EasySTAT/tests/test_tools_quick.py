"""
快速工具验证：直接测试工具是否可以被 Agent 调用

这个测试直接实例化工具并调用，验证基本功能，不涉及完整的 Crew 流程
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from financial_crew.tools.ohlcv_tool import OHLCVTool
from financial_crew.tools.macro_tool import MacroTool
from financial_crew.tools.stock_search_tool import StockSearchTool

def test_tools_directly():
    """直接测试工具调用"""
    
    print("\n" + "="*60)
    print("【快速验证】直接调用工具")
    print("="*60)
    
    # 测试 1：股票搜索工具
    print("\n1. 测试 StockSearchTool：")
    search_tool = StockSearchTool()
    try:
        result = search_tool._run(query="茅台")
        print(f"✅ StockSearchTool 成功：{result[:200]}...")
    except Exception as e:
        print(f"❌ StockSearchTool 失败：{e}")
    
    # 测试 2：OHLCV 工具
    print("\n2. 测试 OHLCVTool：")
    ohlcv_tool = OHLCVTool()
    try:
        result = ohlcv_tool._run(
            stock_code="600519",
            period="daily",
            start_date="20231201",
            end_date="20231210"
        )
        print(f"✅ OHLCVTool 成功：{result[:200]}...")
    except Exception as e:
        print(f"❌ OHLCVTool 失败：{e}")
    
    # 测试 3：宏观数据工具
    print("\n3. 测试 MacroTool：")
    macro_tool = MacroTool()
    try:
        result = macro_tool._run(indicator="gdp", limit=5)
        print(f"✅ MacroTool 成功：{result[:200]}...")
    except Exception as e:
        print(f"❌ MacroTool 失败：{e}")
    
    print("\n" + "="*60)
    print("✅ 快速验证完成")
    print("="*60)

if __name__ == "__main__":
    test_tools_directly()
