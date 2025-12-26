"""
端到端集成测试：验证 Agent 能否通过自然语言调用新集成的 AKShare 工具

测试场景：
1. 股票搜索：通过名称查找代码
2. K 线数据获取：使用真实股票代码获取数据
3. 宏观数据获取：查询 GDP、CPI 等指标
"""
import sys
import os

# 添加 src 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from financial_crew.crew import FinancialCrew

def test_stock_search():
    """测试场景 1：股票名称搜索"""
    print("\n" + "="*60)
    print("【测试 1】股票名称搜索")
    print("="*60)
    
    crew = FinancialCrew()
    
    # 模拟用户输入"我想查一下茅台的股票代码"
    result = crew.crew().kickoff(inputs={
        "user_query": "帮我查一下茅台的股票代码是什么"
    })
    
    print(f"\n结果：\n{result}")
    return result

def test_ohlcv_data():
    """测试场景 2：K 线数据获取"""
    print("\n" + "="*60)
    print("【测试 2】K 线数据获取")
    print("="*60)
    
    crew = FinancialCrew()
    
    # 模拟用户输入"帮我获取贵州茅台最近的 K 线数据"
    result = crew.crew().kickoff(inputs={
        "user_query": "帮我获取 600519 贵州茅台最近的 K 线数据"
    })
    
    print(f"\n结果：\n{result}")
    return result

def test_macro_data():
    """测试场景 3：宏观经济数据获取"""
    print("\n" + "="*60)
    print("【测试 3】宏观经济数据获取")
    print("="*60)
    
    crew = FinancialCrew()
    
    # 模拟用户输入"帮我查一下最近的中国 GDP 和 CPI 数据"
    result = crew.crew().kickoff(inputs={
        "user_query": "帮我查一下最近的中国 GDP 数据"
    })
    
    print(f"\n结果：\n{result}")
    return result

if __name__ == "__main__":
    print("\n🚀 开始 AKShare 集成端到端测试\n")
    
    try:
        # 测试 1：股票搜索
        test_stock_search()
        
        print("\n" + "⏸️  暂停 10 秒避免限流..." + "\n")
        import time
        time.sleep(10)
        
        # 测试 2：OHLCV 数据
        test_ohlcv_data()
        
        print("\n" + "⏸️  暂停 10 秒避免限流..." + "\n")
        time.sleep(10)
        
        # 测试 3：宏观数据
        test_macro_data()
        
        print("\n✅ 所有测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
