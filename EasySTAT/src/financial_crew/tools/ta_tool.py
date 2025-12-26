"""
技术指标计算工具 (Technical Analysis Tool)

主要功能：
    基于 OHLCV 数据计算 RSI、MACD、布林带等技术指标。
    从数据总线读取上游工具保存的数据，通过数据引用获取完整 DataFrame。
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()

# 动态添加路径
ta_path = os.getenv('TA_ANA_PATH', '/Users/mac/dev/personal/easystat/OpenRepo/金融/ta_ana')
if ta_path not in sys.path:
    sys.path.append(ta_path)

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Dict, Any, Union, Optional
import pandas as pd
import json

from financial_crew.utils.data_bus import data_bus


class TAToolInput(BaseModel):
    """技术分析工具输入参数"""
    data_ref_json: Union[str, Dict[str, Any]] = Field(
        ..., 
        description="数据引用 JSON 或字符串，包含 data_ref 字段"
    )


class TATool(BaseTool):
    """
    技术指标计算工具
    
    主要功能：
        从数据总线读取 OHLCV 数据，计算 RSI、MACD、布林带、ATR 等技术指标。
        返回最新一条数据的关键技术指标值。
    """
    name: str = "技术指标计算工具"
    description: str = "基于数据引用读取 OHLCV 数据，计算 RSI、MACD、布林带等技术指标。输入为 K线数据获取工具返回的 data_ref JSON。"
    args_schema: Type[BaseModel] = TAToolInput
    
    def _run(self, data_ref_json: Union[str, Dict[str, Any]]) -> str:
        """
        执行技术指标计算
        
        该方法会解析输入的数据引用，从数据总线加载 DataFrame，并调用 ta 库计算指标。
        
        Args:
            data_ref_json (Union[str, Dict]): 数据引用信息，可以是 JSON 字符串或已解析的字典。
            
        Returns:
            str: 包含技术指标结果的 JSON 字符串。
        """
        try:
            # 兼容性处理：如果是字符串则解析，如果是字典则直接使用
            if isinstance(data_ref_json, str):
                ref = json.loads(data_ref_json)
            else:
                ref = data_ref_json
            
            # 数据获取策略：Registry 优先，传参兜底
            # 理由：Agent (LLM) 经常会编造虚假的 data_ref 字符串，Registry 是内部维护的真实数据源。
            data_key = data_bus.get_latest("ohlcv")
            
            if data_key:
                print(f"[TATool] 正在使用 Registry 提供的正确数据: {data_key}")
            else:
                # 只有 Registry 中没有时，才尝试提取传参
                data_key = self._extract_data_key(ref)
                if data_key:
                    print(f"[TATool] Registry 为空，尝试使用 Agent 传参: {data_key}")
                else:
                    return json.dumps({
                        "error": "无法获取数据引用",
                        "detail": "Registry 中无 ohlcv 数据且传参无效。请确保上游 K线采集任务已成功执行。",
                        "received": str(ref)[:200]
                    }, ensure_ascii=False)
            
            # 从数据总线读取数据
            print(f"[TATool] 正在从数据总线读取: {data_key}")
            df = data_bus.load(data_key)
            
            # 验证数据结构
            validation_error = self._validate_dataframe(df)
            if validation_error:
                return validation_error
            
            # 计算技术指标
            df_with_indicators = self._calculate_indicators(df)
            if df_with_indicators is None:
                return json.dumps({
                    "error": "技术指标计算失败",
                    "reason": "无法导入 ta 库，请检查环境"
                }, ensure_ascii=False)
            
            # 提取最新指标值
            result = self._extract_latest_indicators(df_with_indicators, data_key)
            return json.dumps(result, ensure_ascii=False)
            
        except FileNotFoundError as e:
            return json.dumps({
                "error": "数据文件不存在",
                "detail": str(e)
            }, ensure_ascii=False)
        except json.JSONDecodeError as e:
            return json.dumps({
                "error": "JSON 解析失败",
                "detail": str(e)
            }, ensure_ascii=False)
        except Exception as e:
            print(f"[TATool] 发生异常: {e}")
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    def _extract_data_key(self, ref: Any) -> Optional[str]:
        """
        从引用对象中提取数据 key
        
        Args:
            ref: 解析后的引用对象（支持 dict 或嵌套 references 列表）
            
        Returns:
            str: 数据 key，若无效则返回 None
        """
        if not isinstance(ref, dict):
            return None
            
        # 1. 标准格式：{"data_ref": "ohlcv_600519", ...}
        if "data_ref" in ref and isinstance(ref["data_ref"], str):
            return ref["data_ref"]
            
        # 2. 兼容嵌套格式：{"references": [{"data_ref": ...}]}
        if "references" in ref and isinstance(ref["references"], list):
            for item in ref["references"]:
                if isinstance(item, dict) and "data_ref" in item:
                    return item["data_ref"]
                    
        return None
    
    def _validate_dataframe(self, df: pd.DataFrame) -> Optional[str]:
        """
        验证 DataFrame 是否包含必要列
        
        Args:
            df: 要验证的 DataFrame
            
        Returns:
            str: 错误信息 JSON，验证通过返回 None
        """
        if df.empty:
            return json.dumps({"error": "数据为空"}, ensure_ascii=False)
        
        required_columns = ["Open", "High", "Low", "Close", "Volume"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return json.dumps({
                "error": f"数据缺少必要列",
                "missing": missing_columns,
                "available": list(df.columns)
            }, ensure_ascii=False)
        
        return None
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        计算所有技术指标
        
        Args:
            df: 包含 OHLCV 数据的 DataFrame
            
        Returns:
            pd.DataFrame: 添加技术指标后的 DataFrame，导入失败返回 None
        """
        try:
            from ta import add_all_ta_features
        except ImportError:
            print("[TATool] 无法导入 ta 库")
            return None
        
        # 计算所有技术指标
        df_with_ta = add_all_ta_features(
            df.copy(),
            open="Open",
            high="High",
            low="Low",
            close="Close",
            volume="Volume",
            fillna=True
        )
        
        print(f"[TATool] 已计算技术指标，共 {len(df_with_ta.columns)} 列")
        return df_with_ta
    
    def _extract_latest_indicators(self, df: pd.DataFrame, data_key: str) -> Dict[str, Any]:
        """
        提取最新一条数据的关键技术指标
        
        Args:
            df: 包含技术指标的 DataFrame
            data_key: 数据标识符
            
        Returns:
            dict: 关键技术指标值
        """
        latest = df.iloc[-1]
        
        def safe_float(value):
            """安全转换为浮点数"""
            if pd.isna(value):
                return None
            try:
                return round(float(value), 4)
            except (TypeError, ValueError):
                return None
        
        result = {
            "data_ref": data_key,
            "rsi": safe_float(latest.get("momentum_rsi")),
            "macd": safe_float(latest.get("trend_macd")),
            "macd_signal": safe_float(latest.get("trend_macd_signal")),
            "macd_diff": safe_float(latest.get("trend_macd_diff")),
            "bollinger_hband": safe_float(latest.get("volatility_bbh")),
            "bollinger_mband": safe_float(latest.get("volatility_bbm")),
            "bollinger_lband": safe_float(latest.get("volatility_bbl")),
            "atr": safe_float(latest.get("volatility_atr")),
            "close": safe_float(latest.get("Close")),
            "volume": safe_float(latest.get("Volume")),
        }
        
        print(f"[TATool] 指标计算完成: RSI={result['rsi']}, MACD={result['macd']}")
        return result
