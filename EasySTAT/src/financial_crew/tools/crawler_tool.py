from dotenv import load_dotenv
import pandas as pd
import json
from typing import Type, Dict, Any, Union, ClassVar, List, Optional
import akshare as ak

load_dotenv()

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from financial_crew.utils.data_bus import data_bus

class CrawlerToolInput(BaseModel):
    """
    资金流采集工具输入参数
    
    Attributes:
        flow_type: 资金流类型（个股/板块）
        market_type: 市场类型
        period: 时间周期
    """
    flow_type: str = Field(..., description="资金流类型: 'Stock_Flow' (个股) 或 'Sector_Flow' (板块)")
    market_type: str = Field(..., description="市场类型: 'All_Stocks' (全部A股), 'SH&SZ_A_Shares' (沪深A股) 等")
    period: str = Field(default="today", description="时间周期: 'today', '3d', '5d', '10d'")

class CrawlerTool(BaseTool):
    """
    资金流数据采集工具
    
    主要功能：
        从东方财富采集个股或板块的资金流数据。
        采集后的数据会保存到数据总线，并返回数据引用，确保下游分析工具能正确读取。
    """
    name: str = "资金流数据采集工具"
    description: str = "从东方财富采集个股或板块的资金流数据。返回全市场资金流排行榜（DataFrame 格式）的数据引用。"
    args_schema: Type[BaseModel] = CrawlerToolInput
    
    def _run(self, flow_type: str, market_type: str, period: str = "today") -> str:
        """
        执行资金流数据采集并保存到数据总线
        
        数据存储策略：统一使用 DataFrame 格式存储全市场排行榜数据
        
        Args:
            flow_type: 资金流类型 ('Stock_Flow' 或 'Sector_Flow')
            market_type: 市场类型
            period: 时间周期 ('today', '3d', '5d', '10d')
            
        Returns:
            str: 包含 data_ref 的 JSON 字符串
        """
        try:
            print(f"[CrawlerTool] 开始采集: type={flow_type}, period={period}")
            
            data = None
            
            # 策略分支 1: 个股资金流
            if flow_type == "Stock_Flow":
                if period == "today":
                    # 获取即时个股资金流排名 (包含代码、名称、最新价、主力净流入等)
                    data = ak.stock_fund_flow_individual(symbol="即时")
                elif period == "3d":
                     data = ak.stock_fund_flow_individual(symbol="3日")
                elif period == "5d":
                     data = ak.stock_fund_flow_individual(symbol="5日")
                elif period == "10d":
                     data = ak.stock_fund_flow_individual(symbol="10日")
                else:
                    return json.dumps({"error": f"不支持的时间周期: {period}"}, ensure_ascii=False)

            # 策略分支 2: 板块资金流
            elif flow_type == "Sector_Flow":
                if period == "today":
                    data = ak.stock_sector_fund_flow_rank(indicator="今日")
                elif period == "5d":
                    data = ak.stock_sector_fund_flow_rank(indicator="5日")
                elif period == "10d":
                    data = ak.stock_sector_fund_flow_rank(indicator="10日")
                else:
                     return json.dumps({"error": f"不支持的时间周期: {period}"}, ensure_ascii=False)
            
            else:
                return json.dumps({"error": f"不支持的资金流类型: {flow_type}"}, ensure_ascii=False)
            
            if data is None or data.empty:
                 return json.dumps({
                    "error": f"未采集到 {flow_type} 的有效数据 (Empty DataFrame)", 
                    "status": "failed"
                }, ensure_ascii=False)

            # 3. 生成数据 Key（保持原有命名规范）
            data_key = f"flow_{flow_type.lower()}_{market_type.lower()}_{period}"
            
            # 4. 确保是 DataFrame 并保存到数据总线
            df = pd.DataFrame(data)
            
            # 简单清洗列名，确保兼容性 (可选，但推荐)
            # AKShare 返回的中文列名已经很规范: "序号", "代码", "名称", "最新价", "今日主力净流入-净额" 等
            pass 

            ref = data_bus.save(data_key, df, category="capital_flow")
            
            print(f"[CrawlerTool] 资金流数据采集成功: {data_key}, 共 {len(df)} 条记录")
            return json.dumps(ref, ensure_ascii=False)
            
        except Exception as e:
            print(f"[CrawlerTool] 采集异常: {e}")
            import traceback
            traceback.print_exc()
            return json.dumps({"error": f"采集失败: {str(e)}"}, ensure_ascii=False)
