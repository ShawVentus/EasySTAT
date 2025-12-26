import functools
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
import requests
import json
from typing import Callable, Any, Dict, List, Union

class AKHelper:
    """
    AKShare 辅助工具类
    
    主要功能：
    1. 封装 AKShare 的 API 调用
    2. 提供网络请求自动重试机制
    3. 统一异常处理和错误返回格式
    """

    @staticmethod
    def handle_api_error(func: Callable) -> Callable:
        """
        装饰器：处理 API 调用异常
        
        Args:
            func: 需要装饰的函数
            
        Returns:
            Callable: 包装后的函数
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Union[str, Dict, List]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = f"调用 {func.__name__} 失败: {str(e)}"
                print(f"Error: {error_msg}")
                # 返回统一的错误 JSON
                return json.dumps({
                    "error": error_msg,
                    "status": "failed"
                }, ensure_ascii=False)
        return wrapper

    @staticmethod
    def safe_call(func: Callable, *args, **kwargs) -> Any:
        """
        安全调用 AKShare 接口，带重试机制
        
        Args:
            func: AKShare 的接口函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Any: 接口返回的数据（通常是 DataFrame）
        """
        # 定义重试策略：遇到 RequestException 重试 3 次，每次间隔 2 秒
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_fixed(2),
            retry=retry_if_exception_type((requests.RequestException, ConnectionError, TimeoutError))
        )
        def _exec():
            return func(*args, **kwargs)
        
        try:
            return _exec()
        except Exception as e:
            raise e

    @staticmethod
    def dataframe_to_records(df: pd.DataFrame) -> List[Dict]:
        """
        将 DataFrame 转换为字典列表，并安全处理日期格式
        
        Args:
            df: pandas DataFrame
            
        Returns:
            List[Dict]: 字典列表
        """
        if df is None or df.empty:
            return []
        
        # 复制一份避免修改原数据
        df_copy = df.copy()
        
        # 处理日期列，转为字符串
        for col in df_copy.columns:
            if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
                df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d')
            elif df_copy[col].dtype == 'object':
                 try:
                     # 检查是否包含 date/datetime 对象
                     if not df_copy[col].empty:
                         first_val = df_copy[col].iloc[0]
                         if hasattr(first_val, 'isoformat'):
                             df_copy[col] = df_copy[col].apply(lambda x: x.isoformat() if x else None)
                 except:
                     pass

        return df_copy.to_dict(orient="records")
