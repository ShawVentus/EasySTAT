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
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",  # Vite 默认端口
        "http://localhost:3000",  # 备用端口
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    
    # === CrewAI 相关配置 ===
    EASYSTAT_PROJECT_PATH: str = os.getenv(
        "EASYSTAT_PROJECT_PATH",
        "/Users/mac/dev/personal/br_competition/EasySTAT"
    )
    
    # === SSE 配置 ===
    SSE_RETRY_TIMEOUT: int = 3000  # 客户端重连间隔（毫秒）


# 创建配置单例
settings = Settings()
