import asyncio
import json
import os
from typing import Type, Dict, List, Union, Any
import pandas as pd
import akshare as ak
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from financial_crew.utils.ak_helper import AKHelper
from financial_crew.utils.cache_manager import get_cache_decorator

cached = get_cache_decorator()

class MacroToolInput(BaseModel):
    """宏观数据工具输入参数"""
    indicator: Union[str, List[str]] = Field(
        ..., 
        description="宏观指标代码或列表: 'gdp', 'cpi', 'ppi', 'pmi', 'm2', 'lpr', 'shrzgm' (社融), 'rmb' (汇率)"
    )
    limit: int = Field(default=10, description="返回最近多少条数据")

class MacroTool(BaseTool):
    """
    宏观经济数据工具
    
    主要功能：
        支持并发获取多个中国宏观经济指标。
        具备异常降级能力：如果某个指标采集失败，会记录错误并继续处理其他指标。
    """
    name: str = "宏观经济数据工具"
    description: str = "获取中国宏观经济数据。支持单个指标或指标列表。具备并发采集和异常降级能力。"
    args_schema: Type[BaseModel] = MacroToolInput

    def _run(self, indicator: Union[str, List[str]], limit: int = 10) -> str:
        """
        执行宏观数据获取（同步入口，内部调用异步并发逻辑）
        
        Args:
            indicator (Union[str, List[str]]): 单个指标代码或指标代码列表
            limit (int): 每个指标返回的最近数据条数
            
        Returns:
            str: 包含所有指标结果的 JSON 字符串
        """
        # 统一转为列表处理
        indicators = [indicator] if isinstance(indicator, str) else indicator
        
        print(f"[MacroTool] 开始并发采集指标: {indicators}")
        
        try:
            # 兼容处理：检查当前线程是否已有运行中的事件循环
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            if loop.is_running():
                # 如果循环已在运行（如在某些异步框架中），使用 run_coroutine_threadsafe 或直接 await
                # 但在 CrewAI 同步 Tool 中，通常需要阻塞等待
                import nest_asyncio
                nest_asyncio.apply()
                results = asyncio.run(self._fetch_all_concurrently(indicators, limit))
            else:
                results = loop.run_until_complete(self._fetch_all_concurrently(indicators, limit))
                
            return json.dumps(results, ensure_ascii=False)
        except Exception as e:
            print(f"[MacroTool] 运行异常: {e}")
            return json.dumps({"error": f"执行失败: {str(e)}"}, ensure_ascii=False)

    async def _fetch_all_concurrently(self, indicators: List[str], limit: int) -> Dict[str, Any]:
        """
        异步并发获取所有指标
        
        Args:
            indicators (List[str]): 指标列表
            limit (int): 限制条数
            
        Returns:
            Dict[str, Any]: 汇总结果字典
        """
        # 从环境变量读取并发数，默认为 3
        max_concurrent = int(os.getenv('MAX_MACRO_CONCURRENT', '3'))
        semaphore = asyncio.Semaphore(max_concurrent)
        
        tasks = [self._fetch_one_with_retry(ind, limit, semaphore) for ind in indicators]
        results = await asyncio.gather(*tasks)
        
        # 使用字典推导式精简汇总逻辑
        return {ind: res for ind, res in zip(indicators, results)}

    async def _fetch_one_with_retry(self, indicator: str, limit: int, semaphore: asyncio.Semaphore) -> Any:
        """
        带信号量控制的单个指标采集（异常降级处理）
        
        Args:
            indicator (str): 指标代码
            limit (int): 限制条数
            semaphore (asyncio.Semaphore): 并发控制信号量
            
        Returns:
            Any: 采集到的数据列表或错误信息
        """
        async with semaphore:
            try:
                # 将同步调用放入线程池，避免阻塞异步事件循环
                df = await asyncio.to_thread(fetch_macro_data, indicator)
                
                if df is None or df.empty:
                    return {"status": "failed", "reason": "无数据"}
                
                # 优化日期排序逻辑：优先匹配包含“日期”或“时间”的列
                date_col = next((col for col in df.columns if any(kw in col for kw in ["日期", "时间", "月份", "季度"])), None)
                if date_col:
                    df.sort_values(by=date_col, ascending=False, inplace=True)
                
                return {
                    "status": "success",
                    "data": AKHelper.dataframe_to_records(df.head(limit))
                }
            except Exception as e:
                print(f"[MacroTool] 指标 {indicator} 采集失败: {e}")
                return {"status": "failed", "reason": str(e)}

@cached
def fetch_macro_data(indicator: str) -> pd.DataFrame:
    """
    获取宏观数据（带缓存的同步函数）
    
    Args:
        indicator (str): 指标代码
        
    Returns:
        pd.DataFrame: 数据结果
    """
    indicator_map = {
        "gdp": ak.macro_china_gdp,
        "cpi": ak.macro_china_cpi_yearly,
        "ppi": ak.macro_china_ppi_yearly,
        "pmi": ak.macro_china_pmi_yearly,
        "m2": ak.macro_china_m2_yearly,
        "lpr": ak.macro_china_lpr,
        "shrzgm": ak.macro_china_shrzgm,
        "rmb": ak.macro_china_rmb
    }
    
    if indicator not in indicator_map:
        raise ValueError(f"不支持的宏观指标: {indicator}")
        
    # 使用 AKHelper.safe_call 处理网络重试逻辑
    return AKHelper.safe_call(indicator_map[indicator])
