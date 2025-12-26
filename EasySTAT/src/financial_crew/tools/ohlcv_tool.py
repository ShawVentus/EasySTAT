import asyncio
import os
import json
from typing import Type, List, Dict, Union, Any
import pandas as pd
import akshare as ak
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from financial_crew.utils.ak_helper import AKHelper
from financial_crew.utils.cache_manager import get_cache_decorator
from financial_crew.utils.data_bus import data_bus

# 获取缓存装饰器
cached = get_cache_decorator()

# 数据量限制常量（一年约250个交易日）
MAX_RECORDS_PER_STOCK = 250

class OHLCVToolInput(BaseModel):
    """K线数据工具输入参数"""
    stock_code: str = Field(..., description="股票代码，支持单个代码(如 '600519') 或批量代码(逗号分隔，如 '600519,000001')")
    period: str = Field(default="daily", description="周期: 'daily' (日线), 'weekly' (周线), 'monthly' (月线)")
    start_date: str = Field(default="20230101", description="开始日期，格式 YYYYMMDD")
    end_date: str = Field(default="20500101", description="结束日期，格式 YYYYMMDD")
    adjust: str = Field(default="qfq", description="复权方式: 'qfq' (前复权), 'hfq' (后复权), '' (不复权)")

class OHLCVTool(BaseTool):
    """
    K线数据获取工具
    
    主要功能：
        使用 AKShare 获取 A 股历史 K 线数据，支持多股票并发采集。
        采集后的数据会保存到数据总线，并返回数据引用。
    """
    name: str = "K线数据获取工具"
    description: str = "使用 AKShare 获取 A 股历史 K 线数据。支持多股票并发采集。返回数据引用对象。"
    args_schema: Type[BaseModel] = OHLCVToolInput
    
    def _run(self, stock_code: str, period: str = "daily", start_date: str = "20230101", end_date: str = "20500101", adjust: str = "qfq") -> str:
        """
        执行 K 线数据获取（同步入口，内部调用异步并发逻辑）
        
        Args:
            stock_code (str): 股票代码，支持单个或批量（逗号分隔）
            period (str): 周期
            start_date (str): 开始日期
            end_date (str): 结束日期
            adjust (str): 复权方式
            
        Returns:
            str: 数据引用 JSON 字符串
        """
        codes = [c.strip() for c in stock_code.split(",") if c.strip()]
        
        print(f"[OHLCVTool] 开始并发采集股票 K 线: {codes}")
        
        try:
            # 兼容处理：检查当前线程是否已有运行中的事件循环
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            if loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
                results = asyncio.run(self._fetch_all_concurrently(codes, period, start_date, end_date, adjust))
            else:
                results = loop.run_until_complete(self._fetch_all_concurrently(codes, period, start_date, end_date, adjust))
            
            # 过滤掉失败的结果
            valid_results = [res for res in results if res is not None]
            
            if not valid_results:
                return json.dumps({"error": "未获取到任何有效数据", "status": "failed"}, ensure_ascii=False)
            
            # 单只股票返回单个引用，多只股票返回列表
            if len(valid_results) == 1:
                return json.dumps(valid_results[0], ensure_ascii=False)
            else:
                return json.dumps({
                    "status": "success",
                    "count": len(valid_results),
                    "references": valid_results
                }, ensure_ascii=False)
                
        except Exception as e:
            print(f"[OHLCVTool] 运行异常: {e}")
            return json.dumps({"error": f"执行失败: {str(e)}"}, ensure_ascii=False)

    async def _fetch_all_concurrently(self, codes: List[str], period: str, start_date: str, end_date: str, adjust: str) -> List[Any]:
        """异步并发获取所有股票数据"""
        # 限制并发数，防止被 API 封禁
        max_concurrent = int(os.getenv('MAX_STOCK_CONCURRENT', '5'))
        semaphore = asyncio.Semaphore(max_concurrent)
        
        tasks = [self._fetch_one_with_retry(code, period, start_date, end_date, adjust, semaphore) for code in codes]
        return await asyncio.gather(*tasks)

    async def _fetch_one_with_retry(self, code: str, period: str, start_date: str, end_date: str, adjust: str, semaphore: asyncio.Semaphore) -> Any:
        """带信号量控制的单个股票采集"""
        async with semaphore:
            try:
                df = await asyncio.to_thread(fetch_stock_data, code, period, start_date, end_date, adjust)
                
                if df.empty:
                    return None
                
                # 限制数据量
                if len(df) > MAX_RECORDS_PER_STOCK:
                    df = df.tail(MAX_RECORDS_PER_STOCK)
                
                # 生成 Key
                data_key = f"ohlcv_latest_{code}" if start_date == end_date else f"ohlcv_hist_{code}"
                
                # 保存到数据总线（注册到 Registry）
                return data_bus.save(data_key, df, category="ohlcv")
                
            except Exception as e:
                print(f"[OHLCVTool] 股票 {code} 采集失败: {e}")
                return None

@cached
def fetch_stock_data(symbol: str, period: str, start_date: str, end_date: str, adjust: str) -> pd.DataFrame:
    """获取单只股票数据（带缓存的同步函数）"""
    clean_symbol = ''.join(filter(str.isdigit, symbol))
    
    df = AKHelper.safe_call(
        ak.stock_zh_a_hist,
        symbol=clean_symbol,
        period=period,
        start_date=start_date,
        end_date=end_date,
        adjust=adjust
    )
    
    if df is None or df.empty:
        return pd.DataFrame()

    # 列名映射
    rename_map = {
        "日期": "Date", "开盘": "Open", "收盘": "Close", "最高": "High", "最低": "Low",
        "成交量": "Volume", "成交额": "Amount", "振幅": "Amplitude", "涨跌幅": "QuoteChange",
        "涨跌额": "PriceChange", "换手率": "Turnover"
    }
    df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)
    
    if "stock_code" not in df.columns:
        df["stock_code"] = symbol
        
    numeric_cols = ["Open", "Close", "High", "Low", "Volume", "Amount"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            
    df.fillna(0, inplace=True)
    return df
