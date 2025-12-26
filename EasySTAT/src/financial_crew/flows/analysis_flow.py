from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel, Field
from financial_crew.crew import FinancialCrew
import sys
import json
from typing import List, Dict, Any

class AnalysisState(BaseModel):
    """Flow 状态管理"""
    user_query: str = ""
    final_report: str = ""
    # 中间结果
    capital_flow_data: List[Dict[str, Any]] = []
    technical_indicators: Dict[str, Any] = {}
    volatility_data: Dict[str, Any] = {}

class FinancialAnalysisFlow(Flow[AnalysisState]):
    """金融分析主流程"""

    @start()
    def execute_crew(self):
        """执行金融分析 Crew"""
        print(f"启动金融分析流程，用户请求: {self.state.user_query}")
        
        # 实例化 Crew
        crew_instance = FinancialCrew()
        
        # 启动 Crew
        result = crew_instance.crew().kickoff(inputs={"user_query": self.state.user_query})
        
        # 保存最终报告
        self.state.final_report = result.raw
        
        # 尝试提取中间结果
        # 注意：这里依赖 crew.py 中 Task 的定义顺序
        # 0: fetch_capital_flow_task (JSON List)
        # 1: fetch_ohlcv_task (JSON)
        # 2: calculate_indicators_task (JSON)
        # 3: analyze_capital_flow_task (Text)
        # 4: volatility_modeling_task (JSON)
        # 5: generate_report_task (Markdown)
        
        try:
            tasks_outputs = result.tasks_outputs
            
            # 提取资金流数据 (Task 0)
            if len(tasks_outputs) > 0:
                try:
                    raw = tasks_outputs[0].raw
                    # 尝试解析 JSON，如果 raw 是字符串
                    if isinstance(raw, str):
                        # 清理可能的 markdown 代码块标记
                        clean_raw = raw.replace("```json", "").replace("```", "").strip()
                        self.state.capital_flow_data = json.loads(clean_raw)
                    elif isinstance(raw, list):
                        self.state.capital_flow_data = raw
                except Exception as e:
                    print(f"解析资金流数据失败: {e}")

            # 提取技术指标 (Task 2)
            if len(tasks_outputs) > 2:
                try:
                    raw = tasks_outputs[2].raw
                    if isinstance(raw, str):
                        clean_raw = raw.replace("```json", "").replace("```", "").strip()
                        self.state.technical_indicators = json.loads(clean_raw)
                    elif isinstance(raw, dict):
                        self.state.technical_indicators = raw
                except Exception as e:
                    print(f"解析技术指标失败: {e}")

            # 提取波动率数据 (Task 4)
            if len(tasks_outputs) > 4:
                try:
                    raw = tasks_outputs[4].raw
                    if isinstance(raw, str):
                        clean_raw = raw.replace("```json", "").replace("```", "").strip()
                        self.state.volatility_data = json.loads(clean_raw)
                    elif isinstance(raw, dict):
                        self.state.volatility_data = raw
                except Exception as e:
                    print(f"解析波动率数据失败: {e}")
                    
        except Exception as e:
            print(f"提取中间结果失败: {e}")

        print("金融分析流程执行完成")
        return result.raw

def kickoff():
    """CLI 入口"""
    if len(sys.argv) > 1:
        query = sys.argv[1]
    else:
        query = "分析今日热门股票"
    
    flow = FinancialAnalysisFlow()
    flow.state.user_query = query
    result = flow.kickoff()
    print("\n\n########################")
    print("## 最终分析报告 ##")
    print("########################\n")
    print(result)
