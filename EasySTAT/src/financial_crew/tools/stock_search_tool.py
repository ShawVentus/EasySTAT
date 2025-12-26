from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import json
import pandas as pd
import akshare as ak
from financial_crew.utils.ak_helper import AKHelper
from financial_crew.utils.cache_manager import get_cache_decorator

cached = get_cache_decorator()

class StockSearchToolInput(BaseModel):
    """股票搜索工具输入参数"""
    query: str = Field(..., description="搜索关键词，如 '茅台', '平安银行'")

class StockSearchTool(BaseTool):
    name: str = "股票代码搜索工具"
    description: str = "通过股票名称模糊搜索股票代码。返回包含代码、名称的列表。"
    args_schema: Type[BaseModel] = StockSearchToolInput

    @AKHelper.handle_api_error
    def _run(self, query: str) -> str:
        """
        执行股票搜索
        
        Args:
            query: 搜索关键词
            
        Returns:
            str: 结果 JSON
        """
        df = fetch_all_stocks()
        
        if df is None or df.empty:
            return json.dumps({"error": "无法获取股票列表", "status": "failed"}, ensure_ascii=False)
            
        # 模糊匹配
        # 假设 df 有 "代码" 和 "名称" 列
        mask = df['名称'].str.contains(query, na=False)
        result_df = df[mask]
        
        if result_df.empty:
             return json.dumps({
                 "message": f"未找到包含 '{query}' 的股票。请检查名称是否正确。由于未获取到有效代码，无法执行后续的数据采集任务。", 
                 "status": "failed",
                 "data": []
             }, ensure_ascii=False)
             
        # 只返回代码和名称，减少 Token 消耗
        final_df = result_df[['代码', '名称', '最新价', '涨跌幅']]
        
        return json.dumps(AKHelper.dataframe_to_records(final_df.head(10)), ensure_ascii=False)

@cached
def fetch_all_stocks() -> pd.DataFrame:
    """
    获取全市场股票列表（带缓存）
    
    Returns:
        pd.DataFrame: 全市场实时行情
    """
    return AKHelper.safe_call(ak.stock_zh_a_spot_em)
