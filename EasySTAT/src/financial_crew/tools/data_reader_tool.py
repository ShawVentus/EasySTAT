"""
通用数据读取工具 (Data Reader Tool)

主要功能：
    从数据总线 (DataBus) 读取任意已采集的数据（通过 data_ref 引用）。
    返回数据的摘要信息（如前几行数据、统计描述、列名等），帮助 LLM 理解数据内容。
"""

import json
import pandas as pd
from typing import Type, Dict, Any, Union, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from financial_crew.utils.data_bus import data_bus


class DataReaderToolInput(BaseModel):
    """
    数据读取工具输入参数
    
    Attributes:
        data_ref_json: 数据引用 JSON，包含 data_ref 字段
        category: 可选，数据类别（ohlcv/capital_flow），用于从 Registry 获取数据
    """
    data_ref_json: Union[str, Dict[str, Any]] = Field(
        ..., 
        description="数据引用 JSON 或字符串，必须包含 'data_ref' 字段。例如：{'data_ref': 'ohlcv_hist_600519', ...}"
    )
    category: Optional[str] = Field(
        default=None,
        description="数据类别：'ohlcv'（K线）或 'capital_flow'（资金流）。如不指定，将直接使用 data_ref_json 中的 data_ref 字段。"
    )


class DataReaderTool(BaseTool):
    """
    通用数据读取工具
    
    主要功能：
        根据 data_ref 从数据总线加载数据（通常是 DataFrame）。
        生成并返回数据的 Markdown 摘要，包括：
        1. 基本信息（行数、列数）
        2. 数据预览（head）
        3. 统计描述（describe）
        
    设计目的：
        赋予 Agent "阅读" 能力，使其能分析 CrawlerTool 等采集到的原始数据。
    """
    name: str = "通用数据读取工具"
    description: str = "根据 data_ref 读取数据总线中的数据，并返回 Markdown 格式摘要。可指定 category 参数（ohlcv/capital_flow）从 Registry 获取最新数据。"
    args_schema: Type[BaseModel] = DataReaderToolInput

    def _run(self, data_ref_json: Union[str, Dict[str, Any]], category: Optional[str] = None) -> str:
        """
        执行数据读取
        
        数据获取策略：传参优先，Registry 兜底
        1. 优先从 data_ref_json 提取 data_ref 字段
        2. 如果提取失败且指定了 category，从 Registry 获取该类别的最新数据
        3. 如果仍然失败，返回错误信息
        
        Args:
            data_ref_json: 数据引用对象，可以是 JSON 字符串或字典
            category: 可选，数据类别（ohlcv/capital_flow），用于 Registry 兜底
            
        Returns:
            str: 数据的 Markdown 摘要或错误信息 JSON
        """
        try:
            # 1. 解析输入
            if isinstance(data_ref_json, str):
                try:
                    ref = json.loads(data_ref_json)
                except json.JSONDecodeError:
                    return json.dumps({"error": "输入的 data_ref_json 不是有效的 JSON 字符串"}, ensure_ascii=False)
            else:
                ref = data_ref_json

            # 2. 数据获取策略：传参优先，Registry 兜底
            # 修改理由：之前硬编码 capital_flow 导致无法读取 OHLCV 数据
            data_key = None
            
            # 2.1 优先从传参提取 data_ref
            data_key = self._extract_data_key(ref)
            if data_key:
                print(f"[DataReaderTool] 使用 Agent 传参的 data_ref: {data_key}")
            
            # 2.2 如果传参无效且指定了 category，从 Registry 获取
            if not data_key and category:
                data_key = data_bus.get_latest(category)
                if data_key:
                    print(f"[DataReaderTool] 使用 Registry 中 {category} 类别的数据: {data_key}")
            
            # 2.3 如果仍然没有，返回错误
            if not data_key:
                return json.dumps({
                    "error": "无法获取数据引用",
                    "detail": "data_ref_json 中无有效 data_ref，且未指定 category 或 Registry 为空。",
                    "hint": "请确保传入包含 'data_ref' 字段的 JSON，或指定 category 参数。",
                    "received_input": str(ref)[:200]
                }, ensure_ascii=False)

            # 3. 从总线加载数据
            print(f"[DataReaderTool] 正在读取数据: {data_key}")
            try:
                data = data_bus.load(data_key)
            except FileNotFoundError:
                return json.dumps({
                    "error": "数据文件不存在",
                    "detail": f"Key '{data_key}' 在数据总线中未找到。请检查上游任务是否成功采集数据。"
                }, ensure_ascii=False)

            # 4. 生成摘要
            if isinstance(data, pd.DataFrame):
                return self._generate_dataframe_summary(data, data_key)
            elif isinstance(data, (dict, list)):
                # 处理非 DataFrame 数据
                
                # Check for Hybrid Data (混合数据结构)
                if isinstance(data, dict) and "target_stock" in data and "market_context" in data:
                    return self._render_hybrid_data(data)

                return json.dumps({
                    "info": f"数据类型为 {type(data).__name__}",
                    "content": data
                }, ensure_ascii=False, indent=2)
            else:
                return f"无法预览的数据类型: {type(data).__name__}"

        except Exception as e:
            print(f"[DataReaderTool] 读取发生异常: {e}")
            return json.dumps({"error": f"读取失败: {str(e)}"}, ensure_ascii=False)

    def _extract_data_key(self, ref: Any) -> Optional[str]:
        """从引用中提取 Key (兼容多种嵌套格式)"""
        if isinstance(ref, dict):
            # 标准格式
            if "data_ref" in ref:
                return ref["data_ref"]
            # 嵌套格式
            if "references" in ref and isinstance(ref["references"], list) and len(ref["references"]) > 0:
                item = ref["references"][0]
                if isinstance(item, dict) and "data_ref" in item:
                    return item["data_ref"]
        return None

    def _generate_dataframe_summary(self, df: pd.DataFrame, title: str) -> str:
        """生成 DataFrame 的 Markdown 摘要"""
        if df.empty:
            return f"### 数据详情 ({title})\n\n*(数据为空)*"

        summary = [f"### 数据详情: {title}"]
        summary.append(f"- **维度**: {df.shape[0]} 行 x {df.shape[1]} 列")
        # 如果列数过多 (>10)，则不显示完整预览，改为列表展示列名
        if len(df.columns) > 10:
            summary.append(f"\n> [!NOTE]\n> 数据包含 {len(df.columns)} 列，为保持整洁，仅展示前 5 列预览。")
            summary.append(f"**所有列名**: {', '.join(df.columns.tolist())}")
            # 仅展示前 5 列
            preview_df = df.iloc[:, :5].head(5)
            summary.append("\n#### 1. 数据预览 (前 5 行，前 5 列)")
            summary.append(preview_df.to_markdown(index=False))
        else:
            summary.append(f"- **列名**: {', '.join(df.columns.tolist())}")
            summary.append("\n#### 1. 数据预览 (前 5 行)")
            summary.append(df.head(5).to_markdown(index=False))

        # 仅对数值列做统计描述
        numeric_df = df.select_dtypes(include=['number'])
        if not numeric_df.empty:
            summary.append("\n#### 2. 统计描述")
            # 截取主要统计指标，避免过长
            stats = numeric_df.describe().loc[['count', 'mean', 'min', 'max', '50%']]
            
            # 同样处理统计宽表
            if len(stats.columns) > 8:
                summary.append(stats.iloc[:, :8].to_markdown())
                summary.append(f"\n*(仅展示前 8 个数值列的统计)*")
            else:
                summary.append(stats.to_markdown())

        return "\n".join(summary)

    def _render_hybrid_data(self, data: Dict[str, Any]) -> str:
        """渲染混合数据结构 (Target + Context)"""
        summary = ["### 📊 混合资金流数据分析"]
        
        # 1. 目标个股
        target = data.get("target_stock", {})
        if target:
            summary.append("\n#### 🎯 目标个股资金流")
            # 将单行字典转为 DataFrame 展示
            target_df = pd.DataFrame([target])
            summary.append(target_df.to_markdown(index=False))
        else:
            summary.append("\n> [!WARNING]\n> 未找到目标个股数据 (Target Not Found)")

        # 2. 市场上下文
        context = data.get("market_context", [])
        if context:
            summary.append("\n#### 🔥 市场热度参考 (Top 10)")
            context_df = pd.DataFrame(context)
            # 限制列数展示，防止太宽
            if len(context_df.columns) > 8:
                summary.append(context_df.iloc[:, :8].to_markdown(index=False))
                summary.append("*(仅展示前 8 列)*")
            else:
                summary.append(context_df.to_markdown(index=False))
        
        return "\n".join(summary)
