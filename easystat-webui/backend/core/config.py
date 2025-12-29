"""
EasySTAT WebUI 后端 - 核心配置

主要功能：
- 定义应用全局配置
- 从环境变量加载敏感配置
- 提供配置单例供其他模块使用
"""

import os
from typing import List
from dotenv import load_dotenv

# 加载 .env 文件
# 定义 EasySTAT 项目路径（默认值）
DEFAULT_EASYSTAT_PATH = "/Users/mac/dev/personal/br_competition/EasySTAT"
EASYSTAT_PROJECT_PATH = os.getenv("EASYSTAT_PROJECT_PATH", DEFAULT_EASYSTAT_PATH)

# 加载 EasySTAT 项目下的 .env 文件
env_path = os.path.join(EASYSTAT_PROJECT_PATH, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    # 如果指定路径不存在，尝试加载当前目录下的 .env
    load_dotenv()


class Settings:
    """
    应用配置类
    
    集中管理所有配置项，支持从环境变量读取
    """
    
    # === 服务配置 ===
    APP_NAME: str = "EasySTAT WebUI"
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # === CORS 配置 ===
    _cors_origins_str: str = os.getenv("CORS_ORIGINS", '["http://localhost:5173", "http://localhost:3000"]')
    try:
        import json
        CORS_ORIGINS: List[str] = json.loads(_cors_origins_str)
    except Exception:
        CORS_ORIGINS: List[str] = ["*"]

    # === CrewAI 相关配置 ===
    # 动态解析项目根目录：如果环境变量是相对路径，则基于当前工作目录（假设在 backend）向上推导
    _raw_project_path: str = os.getenv(
        "EASYSTAT_PROJECT_PATH",
        "../../EasySTAT"
    )
    # 获取 backend 目录的绝对路径 (config.py在 backend/core/config.py, 所以向上两级就是 backend)
    _backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 如果是相对路径，则转换为绝对路径
    if not os.path.isabs(_raw_project_path):
        EASYSTAT_PROJECT_PATH: str = os.path.abspath(os.path.join(_backend_dir, _raw_project_path))
    else:
        EASYSTAT_PROJECT_PATH: str = _raw_project_path
    
    # === SSE 配置 ===
    SSE_RETRY_TIMEOUT: int = 3000  # 客户端重连间隔（毫秒）


# 创建配置单例
settings = Settings()
