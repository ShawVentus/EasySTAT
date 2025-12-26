"""
CrawlerTool 单元测试
测试资金流数据采集工具的功能
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from financial_crew.tools.crawler_tool import CrawlerTool

def test_crawler_tool():
    """测试 CrawlerTool 的基本功能"""
    print("=" * 50)
    print("开始测试 CrawlerTool")
    print("=" * 50)
    
    tool = CrawlerTool()
    
    # 测试 1: 个股资金流
    print("\n测试 1: 个股资金流采集")
    try:
        result = tool._run(
            flow_type="Stock_Flow",
            market_type="All_Stocks",
            period="today"
        )
        print(f"✓ 采集成功，数据长度: {len(result)} 字符")
        print(f"数据片段: {result[:200]}...")
        
        # 验证返回的是 JSON
        import json
        data = json.loads(result)
        if isinstance(data, list):
            print(f"✓ 返回数据类型正确: list, 条数: {len(data)}")
        elif isinstance(data, dict) and 'error' in data:
            print(f"✗ 采集失败: {data['error']}")
        else:
            print(f"? 返回数据类型: {type(data)}")
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试 2: 板块资金流
    print("\n测试 2: 板块资金流采集")
    try:
        result = tool._run(
            flow_type="Sector_Flow",
            market_type="All_Stocks",
            period="today"
        )
        print(f"✓ 采集成功")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
    
    print("\n" + "=" * 50)
    print("CrawlerTool 测试完成")
    print("=" * 50)

if __name__ == "__main__":
    test_crawler_tool()
