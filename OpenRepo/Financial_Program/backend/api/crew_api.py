"""
CrewAI 多智能体分析 API - 流式输出版本
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import sys
import os
import json
import io
import re
import threading
import queue
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 动态添加路径
financial_crew_path = os.getenv('FINANCIAL_CREW_SRC_PATH', '/Users/mac/dev/personal/br_competition/EasySTAT/src')
if financial_crew_path not in sys.path:
    sys.path.append(financial_crew_path)

try:
    from financial_crew.flows.analysis_flow import FinancialAnalysisFlow
except ImportError as e:
    print(f"Error importing FinancialAnalysisFlow: {e}")
    FinancialAnalysisFlow = None

router = APIRouter(prefix="/api/crew", tags=["CrewAI"])

class AnalyzeRequest(BaseModel):
    query: str

class StdoutCapture:
    """
    捕获 stdout 输出并解析 CrewAI 事件
    
    CrewAI 使用 rich 库输出格式化的进度信息，我们通过劫持 stdout 来捕获这些输出
    """
    def __init__(self, event_queue: queue.Queue):
        self.event_queue = event_queue
        self.buffer = io.StringIO()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
    def write(self, text):
        # 同时写入原始 stdout 和 buffer
        self.original_stdout.write(text)
        self.buffer.write(text)
        
        # 解析关键事件
        self._parse_events(text)
        
    def flush(self):
        self.original_stdout.flush()
        
    def _parse_events(self, text):
        """
        解析 CrewAI 输出中的关键事件
        
        Args:
            text: stdout 输出的文本
        """
        # 检测 Agent 开始
        if "Agent:" in text and "Agent Started" not in text:
            match = re.search(r'Agent:\s*(.+?)(?:\n|$)', text)
            if match:
                agent_name = match.group(1).strip()
                self.event_queue.put({
                    'type': 'agent_start',
                    'agent': agent_name
                })
        
        # 检测 Task 开始
        if "Task:" in text:
            match = re.search(r'Task:\s*(.+?)(?:\n|$)', text)
            if match:
                task_desc = match.group(1).strip()[:50]  # 截断
                self.event_queue.put({
                    'type': 'task_start',
                    'task': task_desc
                })
        
        # 检测 Tool 调用
        if "Using Tool:" in text or ("Used" in text and "Tool" in text):
            match = re.search(r'(?:Using Tool:|Used)\s*(.+?)(?:\n|$)', text)
            if match:
                tool_name = match.group(1).strip()
                self.event_queue.put({
                    'type': 'tool_call',
                    'tool': tool_name
                })
        
        # 检测 Task 完成
        if "Task Completed" in text:
            self.event_queue.put({
                'type': 'task_complete',
                'message': '任务完成'
            })
        
        # 检测思考中
        if "Thinking" in text:
            self.event_queue.put({
                'type': 'thinking',
                'message': 'Agent 正在思考...'
            })
        
        # 检测 Final Answer
        if "Final Answer:" in text:
            self.event_queue.put({
                'type': 'final_answer',
                'message': '生成最终答案'
            })


def run_crew_with_capture(query: str, event_queue: queue.Queue):
    """
    在子线程中运行 CrewAI 并捕获输出
    
    Args:
        query: 用户查询
        event_queue: 事件队列
    """
    try:
        # 发送开始事件
        event_queue.put({'type': 'start', 'message': f'开始分析: {query}'})
        
        # 捕获 stdout
        capture = StdoutCapture(event_queue)
        sys.stdout = capture
        
        # 创建并运行 Flow
        flow = FinancialAnalysisFlow()
        flow.state.user_query = query
        flow.kickoff()
        
        # 恢复 stdout
        sys.stdout = capture.original_stdout
        
        # 发送完成事件
        event_queue.put({
            'type': 'report',
            'content': flow.state.final_report,
            'data': {
                'capital_flow': flow.state.capital_flow_data,
                'technical_indicators': flow.state.technical_indicators,
                'volatility_data': flow.state.volatility_data
            }
        })
        
    except Exception as e:
        import traceback
        # 先恢复 stdout 再发送错误
        sys.stdout = sys.__stdout__
        event_queue.put({
            'type': 'error',
            'message': str(e),
            'trace': traceback.format_exc()
        })
        event_queue.put({'type': 'done'})
    else:
        # 成功时发送 done
        event_queue.put({'type': 'done'})


@router.post("/analyze")
async def analyze_stock(request: AnalyzeRequest):
    """
    触发多智能体分析（非流式）
    
    Args:
        request: 包含 query 的请求体
        
    Returns:
        dict: 包含报告和中间数据的完整分析结果
    """
    if FinancialAnalysisFlow is None:
        raise HTTPException(status_code=500, detail="FinancialAnalysisFlow 未正确加载，请检查路径配置")

    print(f"收到分析请求: {request.query}")
    
    try:
        flow = FinancialAnalysisFlow()
        flow.state.user_query = request.query
        
        # 运行 Flow
        await asyncio.to_thread(flow.kickoff)
        
        return {
            "success": True,
            "report": flow.state.final_report,
            "data": {
                "capital_flow": flow.state.capital_flow_data,
                "technical_indicators": flow.state.technical_indicators,
                "volatility_data": flow.state.volatility_data
            }
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@router.post("/analyze/stream")
async def analyze_stream(request: AnalyzeRequest):
    """
    流式输出分析过程（SSE）
    
    使用 Server-Sent Events 实时推送分析进度和结果
    
    Args:
        request: 包含 query 的请求体
        
    Returns:
        StreamingResponse: SSE 流
    """
    if FinancialAnalysisFlow is None:
        raise HTTPException(status_code=500, detail="FinancialAnalysisFlow 未正确加载")

    print(f"收到流式分析请求: {request.query}")
    
    async def generate():
        """
        SSE 事件生成器
        
        Yields:
            str: SSE 格式的事件数据
        """
        event_queue = queue.Queue()
        
        # 在后台线程运行 CrewAI
        thread = threading.Thread(
            target=run_crew_with_capture,
            args=(request.query, event_queue)
        )
        thread.start()
        
        # 消费事件队列并发送 SSE
        while True:
            try:
                # 非阻塞获取事件，超时后继续循环
                event = event_queue.get(timeout=0.3)
                
                # 发送 SSE 事件
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                
                # 检查是否结束
                if event.get('type') == 'done':
                    break
                    
            except queue.Empty:
                # 发送心跳保持连接
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                
                # 检查线程是否还在运行
                if not thread.is_alive() and event_queue.empty():
                    break
        
        thread.join(timeout=5)
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
