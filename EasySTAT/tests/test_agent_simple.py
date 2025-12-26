"""
简化版 Agent 测试：只测试新集成的 AKShare 工具，不涉及 CrawlerTool

测试场景：
1. 股票搜索 + K线数据
2. 宏观数据查询
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from crewai import Agent, Task, Crew
from financial_crew.tools.ohlcv_tool import OHLCVTool
from financial_crew.tools.macro_tool import MacroTool
from financial_crew.tools.stock_search_tool import StockSearchTool

def test_stock_search_and_ohlcv():
    """测试股票搜索 + K线数据获取"""
    print("\n" + "="*60)
    print("【测试】股票搜索 + K线数据获取")
    print("="*60)
    
    # 创建一个简单的 Agent
    data_agent = Agent(
        role="金融数据采集专家",
        goal="根据用户需求获取股票数据",
        backstory="你精通 AKShare 数据接口",
        tools=[StockSearchTool(), OHLCVTool()],
        verbose=True
    )
    
    # 创建任务
    task = Task(
        description='用户想查询"茅台"的股票代码，并获取最近5天的 K 线数据',
        expected_output='股票代码和 K 线数据的 JSON',
        agent=data_agent
    )
    
    # 执行
    crew = Crew(agents=[data_agent], tasks=[task], verbose=True)
    result = crew.kickoff()
    
    print(f"\n✅ 结果：\n{result}")
    return result

def test_macro_data():
    """测试宏观数据查询"""
    print("\n" + "="*60)
    print("【测试】宏观数据查询")
    print("="*60)
    
    # 创建 Agent
    data_agent = Agent(
        role="宏观经济数据分析师",
        goal="获取宏观经济数据",
        backstory="你能获取 GDP、CPI 等宏观指标",
        tools=[MacroTool()],
        verbose=True
    )
    
    # 创建任务
    task = Task(
        description='获取中国最近的 GDP 数据（最近 3 条记录）',
        expected_output='GDP 数据的 JSON',
        agent=data_agent
    )
    
    # 执行
    crew = Crew(agents=[data_agent], tasks=[task], verbose=True)
    result = crew.kickoff()
    
    print(f"\n✅ 结果：\n{result}")
    return result

if __name__ == "__main__":
    print("\n🚀 开始简化版 AKShare 工具集成测试\n")
    
    try:
        # 测试 1：股票搜索 + K线
        test_stock_search_and_ohlcv()
        
        print("\n" + "⏸️  暂停 10 秒避免限流..." + "\n")
        import time
        time.sleep(10)
        
        # 测试 2：宏观数据
        test_macro_data()
        
        print("\n✅ 所有测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
