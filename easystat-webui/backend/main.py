"""
EasySTAT WebUI 后端 - 应用入口

主要功能：
- 初始化 FastAPI 应用实例
- 配置 CORS 中间件
- 注册路由模块
- 提供应用启动入口

架构说明：
    main.py (入口)
    ├── api/           # API 路由层
    │   └── sse.py     # SSE 流式推送接口
    ├── services/      # 业务逻辑层
    │   └── executor.py # CrewAI 执行器
    └── core/          # 核心配置层
        └── config.py  # 应用配置
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from api.sse import router as sse_router
from api.files import router as files_router
from core.config import settings


def create_app() -> FastAPI:
    """
    创建并配置 FastAPI 应用实例
    
    Returns:
        FastAPI: 配置完成的应用实例
    """
    app = FastAPI(
        title="EasySTAT WebUI API",
        description="EasySTAT 多智能体系统的 Web 可视化后端",
        version="0.1.0",
    )
    
    # 配置 CORS，允许前端跨域访问
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    app.include_router(sse_router, prefix="/api", tags=["SSE"])
    app.include_router(files_router, prefix="/api", tags=["Files"])
    
    # 健康检查接口（放在 API 路由之后，SPA 兜底之前）
    @app.get("/")
    async def root():
        """
        健康检查接口
        
        Returns:
            dict: 包含服务状态信息
        """
        return {"status": "ok", "message": "EasySTAT WebUI API 运行中"}
    
    # === 静态文件托管（Docker 部署时前端构建产物放在 static 目录）===
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir):
        # 挂载静态资源目录
        assets_dir = os.path.join(static_dir, "assets")
        if os.path.exists(assets_dir):
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
        
        # SPA 路由兜底（必须放在所有路由之后）
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            """
            SPA 路由兜底，返回 index.html
            
            Args:
                full_path: 请求路径
            
            Returns:
                FileResponse: index.html 文件
            """
            # 空路径由根路由处理，不在这里返回
            if not full_path or full_path == "":
                return {"error": "Frontend not built"}
            
            # 如果是 API 请求，跳过（不应到达这里，但作为安全检查）
            if full_path.startswith("api/"):
                return {"error": "Not Found"}
            
            index_path = os.path.join(static_dir, "index.html")
            if os.path.exists(index_path):
                return FileResponse(index_path)
            return {"error": "Frontend not built"}
    
    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    # 本地开发端口 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
