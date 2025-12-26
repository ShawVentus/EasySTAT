import sys
import os
from dotenv import load_dotenv
import pandas as pd
import json
from typing import Type, Dict, Any, Union, ClassVar, List, Optional

load_dotenv()

# 动态添加路径
backend_path = os.getenv('FINANCIAL_PROGRAM_BACKEND_PATH', '/Users/mac/dev/personal/br_competition/OpenRepo/Financial_Program/backend')
if backend_path not in sys.path:
    sys.path.append(backend_path)

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from financial_crew.utils.data_bus import data_bus

# 尝试导入 crawler 模块，如果失败则打印警告
try:
    from crawler.crawler import fetch_flow_data
except ImportError as e:
    print(f"警告: 无法导入 crawler.crawler: {e}")
    fetch_flow_data = None

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
    
    # 市场类型映射常量 (使用 ClassVar 避免 Pydantic 误认为模型字段)
    MARKET_MAPPING: ClassVar[Dict[str, int]] = {
        "All_Stocks": 1, 
        "SH&SZ_A_Shares": 2, 
        "SH_A_Shares": 3,
        "STAR_Market": 4, 
        "SZ_A_Shares": 5, 
        "ChiNext_Market": 6,
        "SH_B_Shares": 7,
        "SZ_B_Shares": 8
    }
    
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
        if fetch_flow_data is None:
            return json.dumps({"error": "无法导入 crawler 模块，请检查路径配置"}, ensure_ascii=False)

        try:
            # 1. 映射参数
            is_stock_flow = flow_type == "Stock_Flow"
            flow_choice = 1 if is_stock_flow else 2
            market_choice = self.MARKET_MAPPING.get(market_type, 1)
            
            # 只有板块资金流 (flow_choice=2) 需要 detail_choice=1
            detail_choice = 1 if not is_stock_flow else None
            
            # 2. 执行采集
            data = fetch_flow_data(
                flow_type, market_type, period, 
                pages=1,
                flow_choice=flow_choice, 
                market_choice=market_choice,
                detail_choice=detail_choice
            )
            
            if not data:
                return json.dumps({
                    "error": f"未采集到 {flow_type} 的有效数据", 
                    "status": "failed"
                }, ensure_ascii=False)

            # 3. 生成数据 Key（统一格式，不再区分 hybrid）
            data_key = f"flow_{flow_type.lower()}_{market_type.lower()}_{period}"
            
            # 4. 转换为 DataFrame 并保存到数据总线
            df = pd.DataFrame(data)
            ref = data_bus.save(data_key, df, category="capital_flow")
            
            print(f"[CrawlerTool] 资金流数据采集成功: {data_key}, 共 {len(df)} 条记录")
            return json.dumps(ref, ensure_ascii=False)
            
        except Exception as e:
            print(f"[CrawlerTool] 采集异常: {e}")
            return json.dumps({"error": f"采集失败: {str(e)}"}, ensure_ascii=False)
