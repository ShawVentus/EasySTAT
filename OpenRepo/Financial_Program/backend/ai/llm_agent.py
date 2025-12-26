"""
通用 LLM 客户端模块

功能说明：
    提供统一的大语言模型调用接口，支持所有 OpenAI 格式兼容的 API。
    包括通义千问、Deepseek、OpenAI 等云端服务。

主要类：
    - LLMAgent: 通用 LLM 代理类，提供同步和流式分析方法

环境变量：
    - LLM_API_KEY: API 密钥
    - LLM_BASE_URL: API 基础地址
    - LLM_MODEL: 模型名称

作者：Financial_Program
日期：2024-12
"""

import os
import re
import json
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

# ========================================
# LLM 配置常量
# ========================================
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv(
    "LLM_BASE_URL", 
    "https://dashscope.aliyuncs.com/compatible-mode/v1"
)
LLM_MODEL = os.getenv("LLM_MODEL", "qwen-plus")

# 向后兼容：如果未设置新变量，尝试读取旧变量
if not LLM_API_KEY:
    LLM_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
if LLM_BASE_URL == "https://dashscope.aliyuncs.com/compatible-mode/v1":
    _old_url = os.getenv("DEEPSEEK_BASE_URL", "")
    if _old_url:
        LLM_BASE_URL = _old_url
        # 如果使用旧的 Deepseek URL，同时回退模型名
        if LLM_MODEL == "qwen-plus":
            LLM_MODEL = "deepseek-chat"


class LLMAgent:
    """
    通用 LLM 代理类
    
    功能说明：
        提供统一的大语言模型调用接口，支持同步和流式两种调用方式。
        
    使用示例：
        >>> result = LLMAgent.analyze(flow_data, user_message="分析资金流")
        >>> for chunk in LLMAgent.analyze_stream(flow_data, user_message="分析"):
        ...     print(chunk, end="")
    """

    @staticmethod
    def clean_history(history, max_items=5):
        """
        清理历史对话，只保留最近的有效对话
        
        Args:
            history: 历史对话列表，每项包含 question 和 answer 字段
            max_items: 最多保留的对话条数，默认为 5
            
        Returns:
            list: 清理后的有效对话列表，如果无有效对话则返回 None
        """
        if not history:
            return None

        # 如果是字符串，尝试解析为列表
        if isinstance(history, str):
            try:
                history = json.loads(history)
            except (json.JSONDecodeError, ValueError):
                return None

        # 过滤掉无效对话（如只有"你好"的简单对话）
        valid_history = []
        for item in history:
            if isinstance(item, dict):
                question = item.get("question", "").strip()

                # 过滤掉过于简单的对话
                if (
                    len(question) > 3
                    and question.lower() not in ["你好", "hello", "hi", "test"]
                    and not question.startswith("你好")
                ):
                    valid_history.append(item)

        # 只保留最近的几条对话
        return valid_history[-max_items:] if valid_history else None

    @staticmethod
    def build_prompt(flow_data, user_message, history=None, style="专业"):
        """
        构建 LLM 提示词
        
        Args:
            flow_data: 资金流数据列表，包含股票/板块的资金流信息
            user_message: 用户的问题或请求
            history: 可选，历史对话记录
            style: 回答风格，默认为"专业"
            
        Returns:
            str: 构建好的完整提示词
        """
        # 清理历史对话
        cleaned_history = LLMAgent.clean_history(history)

        prompt = f"""
你是一名专业金融智能顾问，请结合下方资金流数据，用自然、通俗的语言为用户分析并给出建议。
如数据不足，请温和提示用户补充信息。

【资金流数据】
{json.dumps(flow_data, ensure_ascii=False, indent=2)}

【用户问题】
{user_message}
"""

        # 只添加清理后的历史对话
        if cleaned_history:
            # 只保留关键信息，减少 token 消耗
            history_summary = []
            for item in cleaned_history:
                q = (
                    item.get("question", "")[:50] + "..."
                    if len(item.get("question", "")) > 50
                    else item.get("question", "")
                )
                a = item.get("answer", "")
                if isinstance(a, dict):
                    a = (
                        a.get("advice", str(a))[:100] + "..."
                        if len(str(a)) > 100
                        else str(a)
                    )
                history_summary.append(f"Q: {q} | A: {a}")

            prompt += "\n【最近对话】\n" + "\n".join(history_summary)

        prompt += f"\n请用{style}风格作答。"
        return prompt

    @staticmethod
    def _create_client():
        """
        创建 OpenAI 客户端实例
        
        Returns:
            OpenAI: 配置好的 OpenAI 客户端实例
        """
        return OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

    @staticmethod
    def _parse_response(content):
        """
        解析 LLM 响应内容，尝试提取 JSON 格式
        
        Args:
            content: LLM 返回的原始文本内容
            
        Returns:
            dict: 解析后的结果字典，包含 advice 字段
        """
        try:
            return json.loads(content)
        except Exception:
            # 尝试从文本中提取 JSON
            match = re.search(r"\{[\s\S]*\}", content)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass
            # 如果无法解析为 JSON，直接返回 advice 字段
            return {"advice": content.strip()}

    @staticmethod
    def analyze(flow_data, user_message=None, history=None, style="专业"):
        """
        同步分析资金流数据
        
        Args:
            flow_data: 资金流数据列表
            user_message: 用户问题，如果为空则使用默认问题
            history: 可选，历史对话记录
            style: 回答风格，默认为"专业"
            
        Returns:
            dict: 包含分析结果的字典，通常包含 advice 字段
        """
        prompt = LLMAgent.build_prompt(flow_data, user_message, history, style)

        # 检查 prompt 长度，如果过长则截断
        if len(prompt) > 8000:
            print(
                f"[LLMAgent] 警告：Prompt 过长 ({len(prompt)} 字符)，正在截断...",
                flush=True,
            )
            prompt = prompt[:8000] + "\n\n[提示：对话历史过长，已截断]"

        request_payload = {
            "model": LLM_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一名专业金融分析师，善于资金流分析和投资建议。",
                },
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
        
        print(
            f"\n===== LLM 请求 =====\n"
            f"模型: {LLM_MODEL}\n"
            f"地址: {LLM_BASE_URL}\n"
            f"===============================\n",
            flush=True,
        )
        
        try:
            client = LLMAgent._create_client()
            response = client.chat.completions.create(**request_payload)
            
            print(
                f"\n===== LLM 响应 =====\n"
                f"状态: 成功\n"
                f"===============================\n",
                flush=True,
            )
            
            content = response.choices[0].message.content
            return LLMAgent._parse_response(content)
        except Exception as e:
            print(f"[LLMAgent] 错误：API 调用失败 - {e}", flush=True)
            return {"advice": f"抱歉，AI 服务暂时不可用，请检查 API 配置。错误信息：{str(e)}"}

    @staticmethod
    def analyze_stream(flow_data, user_message=None, history=None, style="专业"):
        """
        流式分析资金流数据，返回生成器
        
        Args:
            flow_data: 资金流数据列表
            user_message: 用户问题
            history: 可选，历史对话记录
            style: 回答风格，默认为"专业"
            
        Yields:
            str: LLM 生成的文本片段
        """
        prompt = LLMAgent.build_prompt(flow_data, user_message, history, style)

        # 检查 prompt 长度，如果过长则截断
        if len(prompt) > 8000:
            print(
                f"[LLMAgent] 警告：Prompt 过长 ({len(prompt)} 字符)，正在截断...",
                flush=True,
            )
            prompt = prompt[:8000] + "\n\n[提示：对话历史过长，已截断]"

        request_payload = {
            "model": LLM_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一名专业金融分析师，善于资金流分析和投资建议。请直接回答用户问题，不要使用JSON格式。",
                },
                {"role": "user", "content": prompt},
            ],
            "stream": True,
        }
        
        print(
            f"\n===== LLM 流式请求 =====\n"
            f"模型: {LLM_MODEL}\n"
            f"地址: {LLM_BASE_URL}\n"
            f"===============================\n",
            flush=True,
        )
        
        try:
            client = LLMAgent._create_client()
            response = client.chat.completions.create(**request_payload)

            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            print(f"[LLMAgent] 错误：流式 API 调用失败 - {e}", flush=True)
            yield f"抱歉，AI 服务暂时不可用，请检查 API 配置。错误信息：{str(e)}"


# ========================================
# 模块测试代码
# ========================================
if __name__ == "__main__":
    # 构造测试数据
    test_flow_data = [
        {
            "type": "stock",
            "flow_type": "Stock_Flow",
            "market_type": "All_Stocks",
            "period": "today",
            "data": {
                "code": "600000",
                "name": "浦发银行",
                "latest_price": 10.5,
                "change_percentage": 1.2,
                "main_flow_net_amount": 1000000,
                "main_flow_net_percentage": 5.6,
                "crawl_time": "2024-05-01 10:00:00",
            },
        }
    ]
    
    test_message = "请帮我分析一下浦发银行今日的资金流情况"
    
    print("\n=== LLM 客户端本地测试 ===\n")
    print(f"API地址: {LLM_BASE_URL}")
    print(f"模型: {LLM_MODEL}")
    print(f"API Key: {LLM_API_KEY[:10]}..." if LLM_API_KEY else "未配置 API Key")
    print()
    
    if LLM_API_KEY:
        result = LLMAgent.analyze(
            test_flow_data, 
            user_message=test_message, 
            style="专业"
        )
        print("分析结果:", result)
    else:
        print("请先配置 LLM_API_KEY 环境变量")
