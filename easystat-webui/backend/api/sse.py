"""
EasySTAT WebUI 后端 - SSE 流式推送接口

主要功能：
- 提供 Server-Sent Events (SSE) 端点
- 接收前端请求后启动 CrewAI 执行
- 实时推送执行日志到前端

SSE 协议说明：
    SSE 是 HTTP 协议的扩展，允许服务器向客户端单向推送数据。
    每条消息格式为: "data: <内容>\n\n"
    客户端使用 EventSource API 接收。
"""

import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter, Query
from sse_starlette.sse import EventSourceResponse

from services.executor import CrewExecutor


router = APIRouter()


# 全局执行器实例，确保 /api/stop 能够控制当前正在运行的任务
global_executor = CrewExecutor()


async def _generate_sse_events(user_query: str) -> AsyncGenerator[dict, None]:
    """
    生成 SSE 事件流的异步生成器
    
    Args:
        user_query (str): 用户输入的自然语言查询
        
    Yields:
        dict: SSE 事件数据，包含 event 类型和 data 内容
    """
    # 发送开始事件
    yield {
        "event": "start",
        "data": f"开始执行查询: {user_query}"
    }
    
    try:
        # 使用全局执行器获取事件流
        async for event in global_executor.run_crew_with_events(user_query):
            yield event
    except Exception as e:
        yield {
            "event": "error",
            "data": {"error": f"执行过程中发生未捕获异常: {str(e)}"}
        }



@router.get("/stream")
async def stream_crew_execution(
    query: str = Query(
        default="分析茅台股票",
        description="用户的自然语言查询"
    )
) -> EventSourceResponse:
    """
    SSE 流式推送接口
    
    接收用户查询，启动 CrewAI 执行，并实时推送日志。
    
    Args:
        query: 用户的自然语言查询（URL 参数）
        
    Returns:
        EventSourceResponse: SSE 事件流响应
        
    示例:
        GET /api/stream?query=分析茅台股票
    """
    return EventSourceResponse(
        _generate_sse_events(query),
        media_type="text/event-stream"
    )


@router.post("/stop")
async def stop_crew_execution():
    """
    停止当前正在运行的 CrewAI 执行。
    
    通过调用全局执行器的 stop() 方法，设置中断信号，
    使得后台线程能够安全地终止。
    
    Returns:
        dict: 包含操作状态的响应字典
    """
    global_executor.stop()
    return {"status": "ok", "message": "已发出停止指令"}


@router.get("/test-stream")
async def test_stream() -> EventSourceResponse:
    """
    测试用 SSE 接口（不依赖 CrewAI）
    
    用于验证 SSE 链路是否正常工作。
    每秒发送一条测试消息，共发送 5 条。
    
    Returns:
        EventSourceResponse: 测试事件流
    """
    async def _generate_test_events() -> AsyncGenerator[dict, None]:
        """生成测试事件"""
        yield {"event": "start", "data": "测试开始"}
        
        for i in range(5):
            await asyncio.sleep(1)
            yield {
                "event": "log",
                "data": f"[{i+1}/5] 这是一条测试消息，验证 SSE 实时推送功能"
            }
        
        yield {"event": "complete", "data": "测试完成"}
    
    return EventSourceResponse(
        _generate_test_events(),
        media_type="text/event-stream"
    )
