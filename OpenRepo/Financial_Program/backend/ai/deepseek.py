"""
Deepseek 兼容模块

功能说明：
    为保持向后兼容，此模块将 DeepseekAgent 作为 LLMAgent 的别名导出。
    所有原有使用 DeepseekAgent 的代码无需修改即可继续工作。

迁移说明：
    - 新代码建议直接使用: from ai.llm_agent import LLMAgent
    - 旧代码可继续使用: from ai.deepseek import DeepseekAgent

作者：Financial_Program
日期：2024-12
"""

# 导入通用 LLM 客户端
from ai.llm_agent import LLMAgent

# ========================================
# 向后兼容：DeepseekAgent 作为 LLMAgent 的别名
# ========================================
# 这样所有使用 DeepseekAgent 的代码无需修改
DeepseekAgent = LLMAgent

# 同时导出新的配置变量（如需直接访问）
from ai.llm_agent import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

# 向后兼容的变量别名
DEEPSEEK_API_KEY = LLM_API_KEY
DEEPSEEK_BASE_URL = LLM_BASE_URL


# ========================================
# 模块测试代码
# ========================================
if __name__ == "__main__":
    # 使用别名测试
    print("=== Deepseek 兼容模块测试 ===")
    print(f"DeepseekAgent 类型: {type(DeepseekAgent)}")
    print(f"是否与 LLMAgent 相同: {DeepseekAgent is LLMAgent}")
    print(f"API 地址: {DEEPSEEK_BASE_URL}")
    print(f"API Key: {DEEPSEEK_API_KEY[:10]}..." if DEEPSEEK_API_KEY else "未配置")

