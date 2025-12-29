"""
EasySTAT WebUI 后端 - CrewAI 执行器服务

主要功能：
- 在进程内执行 CrewAI 多智能体流程
- 通过事件监听器捕获实时执行状态
- 使用线程池隔离避免阻塞 FastAPI 事件循环
- 通过异步队列传递事件给 SSE 接口

架构说明：
    Phase 2 改用进程内执行 + 事件系统，替代 Phase 1 的子进程方式。
    通过 run_in_executor 在线程池中运行 CrewAI，确保不阻塞 Web 服务。
"""

import asyncio
import sys
import threading
from typing import AsyncGenerator

from core.config import settings
from .event_listener import EasyStatEventListener


class CrewStopException(Exception):
    """
    自定义异常，用于协作式中断 CrewAI 执行流程。
    
    当用户点击“停止”按钮时，监听器会捕获信号并抛出此异常，
    从而安全地终止当前的线程执行。
    """
    pass


class CrewExecutor:
    """
    CrewAI 执行器
    
    负责在进程内启动 CrewAI 多智能体流程，捕获事件并实时推送。
    
    Attributes:
        project_path (str): EasySTAT 项目的根目录路径
        event_queue (asyncio.Queue): 异步队列，存储 CrewAI 事件供 SSE 消费
        stop_event (threading.Event): 线程事件，用于发出停止信号
    """
    
    def __init__(self):
        """
        初始化执行器
        
        设置项目路径，并初始化用于跨线程通信的停止事件信号。
        """
        self.project_path = settings.EASYSTAT_PROJECT_PATH
        self.event_queue = None  # 将在 run_crew_with_events 中初始化
        
        self.stop_event = threading.Event()  # 停止信号量
    
    async def run_crew_with_events(self, user_query: str) -> AsyncGenerator[dict, None]:
        """
        在进程内执行 CrewAI 并通过事件队列获取实时输出
        
        执行流程：
          1. 创建异步队列用于事件传递
          2. 在线程池中启动 CrewAI 执行（避免阻塞事件循环）
          3. 从队列中逐个取出事件并 yield 给 SSE
        
        Args:
            user_query: 用户的自然语言查询（Phase 2 暂不使用，Phase 3 将支持）
            
        Yields:
            dict: 事件消息，格式为 {"event": "...", "data": {...}}
            
        注意：
            - 必须在异步上下文中创建 asyncio.Queue()
            - 使用 run_in_executor 在线程池中执行同步代码
            - 通过超时机制避免队列永久阻塞
        """
        # 1. 初始化异步队列并保存事件循环引用
        self.event_queue = asyncio.Queue()
        # 修复 Bug 1: 手动添加 _my_loop 属性供跨线程使用
        self.event_queue._my_loop = asyncio.get_running_loop()
        
        # 每次启动前重置停止信号
        self.stop_event.clear()
        
        # 优化：在初始化时设置 Python 路径，避免重复插入
        import os
        src_path = os.path.join(self.project_path, "src")
        # 确保路径是绝对路径
        if not os.path.isabs(src_path):
             src_path = os.path.abspath(src_path)
             
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        # 2. 在线程池中执行 CrewAI
        loop = asyncio.get_running_loop()
        executor_future = loop.run_in_executor(
            None,  # 使用默认线程池
            self._run_crew_in_thread,
            user_query
        )
        
        # 3. 持续从队列中取事件
        while True:
            try:
                # 等待事件（超时 1 秒，避免永久阻塞）
                event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=1.0
                )
                yield event
                
                # 如果是完成事件或错误事件，退出循环
                if event.get("event") in ["crew_complete", "error"]:
                    break
                    
            except asyncio.TimeoutError:
                # 检查线程是否结束
                if executor_future.done():
                    # 修复 Bug 4: 循环读取队列中所有残留事件
                    while True:
                        try:
                            event = await asyncio.wait_for(
                                self.event_queue.get(),
                                timeout=0.1
                            )
                            yield event
                            if event.get("event") in ["crew_complete", "error"]:
                                return  # 找到终止事件，退出
                        except asyncio.TimeoutError:
                            break  # 队列为空
                    return  # 线程已结束且队列为空，退出循环
                continue
    
    def _run_crew_in_thread(self, user_query: str):
        """
        在线程中同步执行 CrewAI 流程
        
        该方法运行在独立的线程池中，负责初始化事件监听器并启动 CrewAI 决策。
        
        Args:
            user_query (str): 用户输入的自然语言查询指令
            
        Returns:
            None: 执行结果通过事件队列异步返回
        """
        # 1. 创建事件监听器（会自动注册到 crewai_event_bus）
        # 传入 stop_event 以便监听器能够捕获中断信号
        listener = EasyStatEventListener(self.event_queue, self.stop_event)
        
        try:
            # 加载 EasySTAT 项目的 .env 文件，确保 DATA_BUS_PATH 等环境变量生效
            from dotenv import load_dotenv
            import os
            easystat_env_path = os.path.join(self.project_path, '.env')
            load_dotenv(easystat_env_path, override=True)
            print(f"[执行器] 已加载环境变量: {easystat_env_path}")
            
            # 延迟导入，确保 sys.path 和环境变量已设置
            from financial_crew.crew import FinancialCrew
            
            print("[执行器] 开始执行 CrewAI")
            
            # 2. 创建并执行 Crew
            crew = FinancialCrew()
            result = crew.crew().kickoff(inputs={
                "user_query": user_query
            })
            
            print(f"[执行器] CrewAI 执行完成，结果: {str(result)[:100]}...")
            
            # 3. 追踪生成的文件
            generated_files = listener._track_generated_files()
            
            # 4. 发送文件列表事件
            if generated_files:
                self._put_files_event(generated_files)
            
            # 5. 发送完成事件
            self._put_completion_event(result)
            
        except CrewStopException:
            print("[执行器] 收到停止信号，执行已中断")
            self._put_error_event("执行已由用户手动停止")
            
        except Exception as e:
            print(f"[执行器] 执行出错: {e}")
            import traceback
            traceback.print_exc()
            
            # 发送错误事件
            self._put_error_event(f"执行出错: {str(e)}")
            
        finally:
            # 确保即使发生未捕获异常，也能清理监听器状态（如果需要）
            print("[执行器] 线程执行结束，正在清理资源")
    
    def _put_completion_event(self, result):
        """
        发送执行完成事件
        
        Args:
            result: CrewAI 执行结果对象
        """
        # 修复 Bug 1: 使用 _my_loop 而非不存在的 _loop
        asyncio.run_coroutine_threadsafe(
            self.event_queue.put({
                "event": "crew_complete",
                "data": {"result": str(result)}
            }),
            self.event_queue._my_loop
        )
    
    def _put_error_event(self, error: str):
        """
        发送执行错误事件
        
        Args:
            error: 错误信息字符串
        """
        # 修复 Bug 1: 使用 _my_loop
        asyncio.run_coroutine_threadsafe(
            self.event_queue.put({
                "event": "error",
                "data": {"error": error}
            }),
            self.event_queue._my_loop
        )
    
    def _put_files_event(self, files: list):
        """
        发送文件列表事件
        
        Args:
            files: 生成的文件路径列表
        """
        # 转换为相对路径，方便前端显示
        relative_files = [f.replace(self.project_path, "").lstrip("/") for f in files]
        
        # 修复 Bug 1: 使用 _my_loop
        asyncio.run_coroutine_threadsafe(
            self.event_queue.put({
                "event": "files_generated",
                "data": {"files": relative_files}
            }),
            self.event_queue._my_loop
        )

    def stop(self):
        """
        触发停止信号，中断当前正在运行的 CrewAI 流程。
        
        该方法会被 API 路由调用，通过设置 threading.Event 信号，
        使得正在运行的监听器抛出异常从而中断执行。
        """
        if self.stop_event:
            self.stop_event.set()
            print("[执行器] 用户请求停止执行，已设置停止信号")
