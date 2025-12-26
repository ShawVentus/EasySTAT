"""
Flow 端到端测试
测试完整的 FinancialAnalysisFlow 执行流程（使用模拟数据）
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# 配置环境变量
os.environ['OPENAI_API_KEY'] = '4c97924ea86e4b40b9cf091dcfd20e44'
os.environ['OPENAI_API_BASE'] = 'https://openapi.dp.tech/openapi/v1'
os.environ['OPENAI_MODEL_NAME'] = 'qwen-plus'

from financial_crew.flows.analysis_flow import FinancialAnalysisFlow

def test_flow_simple():
    """测试 Flow 的简单执行（预期会因 OHLCV 未实现而部分失败）"""
    print("=" * 60)
    print("开始测试 FinancialAnalysisFlow - 简化版")
    print("=" * 60)
    
    try:
        # 创建 Flow 实例
        flow = FinancialAnalysisFlow()
        flow.state.user_query = "分析工业富联的资金流情况"
        
        print(f"\n用户查询: {flow.state.user_query}")
        print("开始执行 Flow...")
        print("注意：由于 OHLCV 未实现，技术分析和建模部分会降级\n")
        
        # 执行 Flow
        result = flow.kickoff()
        
        print("\n" + "=" * 60)
        print("Flow 执行完成")
        print("=" * 60)
        
        # 检查结果
        print(f"\n是否生成最终报告: {'是' if flow.state.final_report else '否'}")
        print(f"报告长度: {len(flow.state.final_report)} 字符")
        if flow.state.final_report:
            print(f"\n报告片段:\n{flow.state.final_report[:300]}...")
        
        print(f"\n资金流数据条数: {len(flow.state.capital_flow_data)}")
        if flow.state.capital_flow_data:
            print(f"第一条数据: {flow.state.capital_flow_data[0]}")
        
        print(f"\n技术指标数据: {flow.state.technical_indicators}")
        print(f"波动率数据: {flow.state.volatility_data}")
        
        print("\n✓ Flow 测试完成\n")
        
    except Exception as e:
        print(f"\n✗ Flow 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_flow_simple()
