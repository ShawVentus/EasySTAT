"""
EasySTAT WebUI 后端 - API 模块初始化

主要功能：
- 导出 API 路由模块
"""

from .sse import router as sse_router

__all__ = ["sse_router"]
