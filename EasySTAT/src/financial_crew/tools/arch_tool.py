"""
波动率建模工具 (ARCH/GARCH Volatility Modeling Tool)

主要功能：
    使用 GARCH(1,1) 模型对股票收益率进行波动率建模。
    从数据总线读取上游工具保存的 OHLCV 数据，提取收盘价计算对数收益率。
    评估当前市场风险水平，输出条件波动率和模型参数。
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()

# 动态添加路径
arch_path = os.getenv('ARCH_MODEL_PATH', '/Users/mac/dev/personal/br_competition/OpenRepo/arch_model')
if arch_path not in sys.path:
    sys.path.append(arch_path)

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Dict, Any, Union, Optional
import numpy as np
import pandas as pd
import json

from financial_crew.utils.data_bus import data_bus

# 最小数据量要求
MIN_DATA_POINTS = 30


class ArchToolInput(BaseModel):
    """波动率建模工具输入参数"""
    data_ref_json: Union[str, Dict[str, Any]] = Field(
        ..., 
        description="数据引用 JSON 或字符串，包含 data_ref 字段"
    )


class ArchTool(BaseTool):
    """
    波动率建模工具
    
    主要功能：
        从数据总线读取 OHLCV 数据，使用 GARCH(1,1) 模型分析股票波动率。
        输出条件波动率、模型参数（omega, alpha, beta）及对数似然值。
    """
    name: str = "波动率建模工具"
    description: str = "基于数据引用读取 OHLCV 数据，使用 GARCH 模型分析波动率风险。输入为 K线数据获取工具返回的 data_ref JSON。"
    args_schema: Type[BaseModel] = ArchToolInput
    
    def _run(self, data_ref_json: Union[str, Dict[str, Any]]) -> str:
        """
        执行波动率建模分析
        
        该方法会解析输入的数据引用，计算对数收益率，并拟合 GARCH 模型评估风险。
        
        Args:
            data_ref_json (Union[str, Dict]): 数据引用信息，支持 JSON 字符串或字典。
            
        Returns:
            str: 包含 GARCH 模型参数和风险评估结果的 JSON 字符串。
        """
        try:
            # 兼容性处理：支持字符串和字典输入
            if isinstance(data_ref_json, str):
                ref = json.loads(data_ref_json)
            else:
                ref = data_ref_json
            
            # 数据获取策略：Registry 优先，传参兜底
            # 理由：Agent (LLM) 经常会编造虚假的 data_ref 字符串，Registry 是内部维护的真实数据源。
            data_key = data_bus.get_latest("ohlcv")
            
            if data_key:
                print(f"[ArchTool] 正在使用 Registry 提供的正确数据: {data_key}")
            else:
                # 只有 Registry 中没有时，才尝试提取传参（用于支持复杂的历史数据指定或其他特殊场景）
                data_key = self._extract_data_key(ref)
                if data_key:
                    print(f"[ArchTool] Registry 为空，尝试使用 Agent 传参: {data_key}")
                else:
                    return json.dumps({
                        "error": "无法获取数据引用",
                        "detail": "Registry 中无 ohlcv 数据且传参无效。请确保上游 K线采集任务已成功执行。",
                        "received": str(ref)[:200]
                    }, ensure_ascii=False)
            
            # 从数据总线读取数据
            print(f"[ArchTool] 正在从数据总线读取: {data_key}")
            df = data_bus.load(data_key)
            
            # 提取收盘价
            prices = self._extract_close_prices(df)
            if prices is None:
                return json.dumps({
                    "error": "无法提取收盘价",
                    "detail": "数据中缺少 Close 或 收盘 列"
                }, ensure_ascii=False)
            
            # 检查数据量
            if len(prices) < MIN_DATA_POINTS:
                return json.dumps({
                    "error": "数据量不足",
                    "detail": f"至少需要 {MIN_DATA_POINTS} 条数据，当前仅有 {len(prices)} 条"
                }, ensure_ascii=False)
            
            # 执行 GARCH 建模
            result = self._fit_garch_model(prices, data_key)
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
            print(f"[ArchTool] 发生异常: {e}")
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    def _extract_data_key(self, ref: Any) -> Optional[str]:
        """
        从引用对象中提取数据 key
        
        Args:
            ref: 解析后的引用对象
            
        Returns:
            str: 数据 key，若无效则返回 None
        """
        if isinstance(ref, dict):
            if "data_ref" in ref:
                return ref["data_ref"]
            if "references" in ref and isinstance(ref["references"], list):
                if len(ref["references"]) > 0:
                    return ref["references"][0].get("data_ref")
        return None
    
    def _extract_close_prices(self, df: pd.DataFrame) -> Optional[np.ndarray]:
        """
        从 DataFrame 中提取收盘价序列
        
        Args:
            df: OHLCV 数据 DataFrame
            
        Returns:
            np.ndarray: 收盘价数组，若无法提取则返回 None
        """
        # 尝试多种可能的列名
        for col_name in ["Close", "close", "收盘"]:
            if col_name in df.columns:
                prices = pd.to_numeric(df[col_name], errors='coerce').dropna().values
                if len(prices) > 0:
                    return prices
        return None
    
    def _fit_garch_model(self, prices: np.ndarray, data_key: str) -> Dict[str, Any]:
        """
        拟合 GARCH(1,1) 模型
        
        Args:
            prices: 收盘价数组
            data_key: 数据标识符
            
        Returns:
            dict: 建模结果
        """
        # 计算对数收益率（百分比形式）
        returns = 100 * np.diff(np.log(prices))
        
        # 动态导入 arch 库
        try:
            from arch import arch_model
        except ImportError:
            return {
                "error": "无法导入 arch 库",
                "detail": "请确保已安装 arch 库: pip install arch"
            }
        
        # 拟合 GARCH(1,1) 模型
        print(f"[ArchTool] 正在拟合 GARCH(1,1) 模型，数据点数: {len(returns)}")
        am = arch_model(returns, vol='Garch', p=1, q=1)
        res = am.fit(disp='off')
        
        # 提取结果
        result = {
            "data_ref": data_key,
            "model": "GARCH(1,1)",
            "data_points": len(returns),
            "conditional_volatility": round(float(res.conditional_volatility[-1]), 4),
            "omega": round(float(res.params.get('omega', 0)), 6),
            "alpha": round(float(res.params.get('alpha[1]', 0)), 6),
            "beta": round(float(res.params.get('beta[1]', 0)), 6),
            "log_likelihood": round(float(res.loglikelihood), 4),
            "aic": round(float(res.aic), 4),
            "bic": round(float(res.bic), 4),
        }
        
        print(f"[ArchTool] GARCH 建模完成: 条件波动率={result['conditional_volatility']}%, "
              f"omega={result['omega']}, alpha={result['alpha']}, beta={result['beta']}")
        
        return result
