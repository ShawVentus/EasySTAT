import sys
import os

# 添加 src 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from financial_crew.flows.analysis_flow import FinancialAnalysisFlow

def test_flow():
    print("开始测试 FinancialAnalysisFlow...")
    flow = FinancialAnalysisFlow()
    flow.state.user_query = "测试：分析贵州茅台"
    
    try:
        result = flow.kickoff()
        print("\nFlow 执行成功！")
        print("最终报告片段:", result[:100] + "..." if result else "无报告")
        
        print("\n中间数据检查:")
        print(f"- 资金流数据条数: {len(flow.state.capital_flow_data)}")
        print(f"- 技术指标 Keys: {list(flow.state.technical_indicators.keys())}")
        print(f"- 波动率数据 Keys: {list(flow.state.volatility_data.keys())}")
        
    except Exception as e:
        print(f"\nFlow 执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_flow()
