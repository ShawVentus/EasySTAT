"""
EasySTAT WebUI 后端 - CrewAI 事件监听器

主要功能：
- 监听 CrewAI 的 Agent/Task/Tool 执行事件
- 将事件转换为结构化 JSON 格式
- 通过异步队列推送给 SSE 接口
- 追踪执行过程中生成的文件

技术细节：
- 继承 CrewAI 的 BaseEventListener 抽象类
- 使用 asyncio.Queue 进行线程安全的事件传递
- 通过 run_coroutine_threadsafe 桥接同步/异步上下文
"""

import asyncio
import os
import glob
import threading
import re
import sys
import traceback
from typing import Any
from datetime import datetime

from crewai.events import BaseEventListener, crewai_event_bus
from crewai.events import (
    AgentExecutionStartedEvent,
    AgentExecutionCompletedEvent,
    TaskStartedEvent,
    TaskCompletedEvent,
    ToolUsageStartedEvent,
    ToolUsageFinishedEvent,
)

from core.config import settings


def _safe_log(message: str):
    """
    安全的日志输出函数，绕过 Rich 的 FileProxy 代理。
    
    Rich 库会劫持 stdout，在某些情况下调用 print() 会导致递归错误。
    使用 sys.__stdout__ 可以直接访问原始的 stdout，避免此问题。
    """
    try:
        sys.__stdout__.write(message + "\n")
        sys.__stdout__.flush()
    except:
        pass  # 静默失败，日志输出不应影响主逻辑



class EasyStatEventListener(BaseEventListener):
    """
    EasySTAT 自定义事件监听器
    
    捕获 CrewAI 执行过程中的关键事件，转换为标准化 JSON 格式，
    并通过异步队列传递给 SSE 接口进行前端推送。
    
    Attributes:
        event_queue (asyncio.Queue): 异步队列，存储事件供 SSE 消费
        generated_files (list): 记录本次执行生成的文件路径列表
        initial_files (set): 执行开始前 result 目录已有的文件集合
    """
    
    def __init__(self, event_queue: asyncio.Queue, stop_event: threading.Event = None):
        """
        初始化事件监听器
        
        Args:
            event_queue (asyncio.Queue): 外部传入的异步队列，用于存储捕获的事件
            stop_event (threading.Event): 停止信号量，用于协作式中断执行
        """
        self.event_queue = event_queue
        self.stop_event = stop_event
        self.generated_files = []
        
        # 记录执行开始前已有的文件
        result_dir = os.path.join(settings.EASYSTAT_PROJECT_PATH, "result")
        if os.path.exists(result_dir):
            self.initial_files = set(glob.glob(f"{result_dir}/**/*", recursive=True))
        else:
            self.initial_files = set()
        
        # 初始化日志存盘
        self.log_file = self._init_log_file()
        
        super().__init__()  # 自动调用 setup_listeners

    def _init_log_file(self) -> str:
        """
        初始化本次执行的日志文件
        
        在 EasySTAT/logs 目录下创建一个以时间戳命名的 .log 文件。
        
        Returns:
            str: 日志文件的绝对路径
        """
        log_dir = os.path.join(settings.EASYSTAT_PROJECT_PATH, "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(log_dir, f"crew_execution_{timestamp}.log")
        
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"=== EasySTAT 执行日志 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ===\n\n")
            
        return log_path
    
    def setup_listeners(self, event_bus) -> None:
        """
        在事件总线上注册监听器
        
        注册 6 种类型的事件处理器，覆盖 Agent/Task/Tool 的生命周期。
        
        Args:
            event_bus: CrewAI 事件总线实例（由父类传入）
        """
        # 注册 Agent 事件
        event_bus.on(AgentExecutionStartedEvent)(self._handle_agent_start)
        event_bus.on(AgentExecutionCompletedEvent)(self._handle_agent_complete)
        
        # 注册 Task 事件
        event_bus.on(TaskStartedEvent)(self._handle_task_start)
        event_bus.on(TaskCompletedEvent)(self._handle_task_complete)
        
        # 注册 Tool 事件
        event_bus.on(ToolUsageStartedEvent)(self._handle_tool_start)
        event_bus.on(ToolUsageFinishedEvent)(self._handle_tool_finish)

    def _check_interruption(self):
        """
        检查是否收到停止信号，若收到则抛出异常中断执行。
        
        Raises:
            CrewStopException: 当收到停止信号时抛出，由执行器捕获。
        """
        if self.stop_event and self.stop_event.is_set():
            # 延迟导入以避免循环依赖
            from .executor import CrewStopException
            raise CrewStopException()
    
    def _safe_str(self, obj, max_len=1000):
        """
        安全地将对象转换为可读字符串，用于日志记录和SSE推送。
        
        核心策略：
        1. 白名单属性提取：对已知类型（Agent/Task）只提取关键属性
        2. 循环检测：使用 visited set 检测循环引用
        3. 安全降级：对未知类型只返回类型名，避免调用其 __str__() 方法
        
        Args:
            obj: 要转换的对象
            max_len: 字符串最大长度限制
            
        Returns:
            str: 转换后的安全字符串
        """
        visited = set()

        def _recursive_convert(item):
            # 1. 循环检测：如果对象 ID 已处理过，说明出现了 A->B->A 的死循环
            item_id = id(item)
            if item_id in visited:
                return f"<CircularReference: {type(item).__name__}>"
            
            # 标记为已访问（仅针对容器对象和自定义对象，基本类型无需标记）
            if not isinstance(item, (int, float, bool, str, type(None))):
                visited.add(item_id)

            try:
                if item is None:
                    return "None"
                if isinstance(item, (int, float, bool)):
                    return str(item)
                if isinstance(item, str):
                    return item[:max_len]
                
                # CrewAI Agent 对象：提取 role 和 goal
                if hasattr(item, 'role') and hasattr(item, 'goal'):
                    role = getattr(item, 'role', 'Unknown')
                    goal = getattr(item, 'goal', 'No Goal')
                    return f"Agent(role={role}, goal={str(goal)[:50]}...)"
                
                # CrewAI Task 对象：提取 description
                if hasattr(item, 'description') and hasattr(item, 'expected_output'):
                    desc = getattr(item, 'description', '')
                    return f"Task(description={str(desc)[:50]}...)"
                
                # 容器处理
                if isinstance(item, list):
                    res = [_recursive_convert(i) for i in item[:10]]
                    if len(item) > 10: res.append("...")
                    return "[" + ", ".join(res) + "]"
                
                if isinstance(item, dict):
                    res = []
                    for k, v in list(item.items())[:10]:
                        res.append(f"{_recursive_convert(k)}: {_recursive_convert(v)}")
                    if len(item) > 10: res.append("...")
                    return "{" + ", ".join(res) + "}"
                
                # 兜底：只返回类型名，不调用对象的 __str__() 方法
                # 这是防止递归的最后一道防线
                return f"<{type(item).__name__}>"
                
            except Exception as e:
                return f"<Error: {str(e)}>"
            finally:
                # 回溯时移除标记
                if not isinstance(item, (int, float, bool, str, type(None))):
                    try:
                        visited.remove(item_id)
                    except KeyError:
                        pass
        
        try:
            return _recursive_convert(obj)
        except RecursionError:
            return "<Critical Recursion Error>"


    def _handle_agent_start(self, source: Any, event: AgentExecutionStartedEvent):
        """
        处理 Agent 开始执行事件
        """
        try:
            self._check_interruption()
            
            # 提取关键信息
            agent_obj = getattr(event, 'agent', None)
            agent_role = self._safe_str(getattr(agent_obj, 'role', '未知角色')) if agent_obj else "未知角色"
            
            task_obj = getattr(event, 'task', None)
            if task_obj and hasattr(task_obj, 'description'):
                task_desc = self._safe_str(task_obj.description)
            else:
                task_desc = "未知任务"
            
            # 构造 SSE 格式消息
            message = {
                "event": "agent_start",
                "data": {
                    "agent": agent_role,
                    "task": task_desc,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # 同步放入队列
            self._put_event_sync(message)
            _safe_log(f"[事件监听器] Agent 开始: {agent_role}")
        except Exception as e:
            if "CrewStopException" in str(type(e)): raise e
            _safe_log(f"[事件监听器] 处理 agent_start 事件失败: {e}")
    
    def _handle_agent_complete(self, source: Any, event: AgentExecutionCompletedEvent):
        """
        处理 Agent 完成执行事件
        """
        try:
            self._check_interruption()
            
            agent_obj = getattr(event, 'agent', None)
            agent_role = self._safe_str(getattr(agent_obj, 'role', '未知角色')) if agent_obj else "未知角色"
            output = self._safe_str(getattr(event, 'output', ''))
            
            message = {
                "event": "agent_complete",
                "data": {
                    "agent": agent_role,
                    "output": output,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            self._put_event_sync(message)
            _safe_log(f"[事件监听器] Agent 完成: {agent_role}")
        except Exception as e:
            if "CrewStopException" in str(type(e)): raise e
            _safe_log(f"[事件监听器] 处理 agent_complete 事件失败: {e}")
    
    def _handle_task_start(self, source: Any, event: TaskStartedEvent):
        """
        处理 Task 开始事件。
        """
        try:
            self._check_interruption()
            
            task_obj = getattr(event, 'task', None)
            if not task_obj:
                task_name = "未知任务"
            else:
                task_name = getattr(task_obj, 'name', None)
                if not task_name:
                    task_name = self._safe_str(getattr(task_obj, 'description', '未知任务'), 50)
            
            message = {
                "event": "task_start",
                "data": {
                    "task": task_name,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            self._put_event_sync(message)
            _safe_log(f"[事件监听器] Task 开始: {task_name}")
        except Exception as e:
            if "CrewStopException" in str(type(e)): raise e
            _safe_log(f"[事件监听器] 处理 task_start 事件失败: {e}")
    
    def _handle_task_complete(self, source: Any, event: TaskCompletedEvent):
        """
        处理 Task 完成事件。
        """
        try:
            self._check_interruption()
            
            task_obj = getattr(event, 'task', None)
            if not task_obj:
                task_name = "未知任务"
                output = ""
            else:
                task_name = getattr(task_obj, 'name', None)
                if not task_name:
                    task_name = self._safe_str(getattr(task_obj, 'description', '未知任务'), 50)
                output = self._safe_str(getattr(task_obj, 'output', ''))
            
            message = {
                "event": "task_complete",
                "data": {
                    "task": task_name,
                    "output": output,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            self._put_event_sync(message)
            _safe_log(f"[事件监听器] Task 完成: {task_name}")
            
            # 任务完成时也检查一次文件
            self._check_and_emit_files()
        except Exception as e:
            if "CrewStopException" in str(type(e)): raise e
            _safe_log(f"[事件监听器] 处理 task_complete 事件失败: {e}")
    
    def _handle_tool_start(self, source: Any, event: ToolUsageStartedEvent):
        """
        处理 Tool 开始使用事件。
        """
        try:
            self._check_interruption()
            
            # 兼容性处理：不同版本的 CrewAI 可能使用不同的属性名
            tool_obj = getattr(event, 'tool', None)
            tool_name = getattr(tool_obj, 'name', None) if tool_obj else getattr(event, 'tool_name', '未知工具')
            
            # 记录原始参数
            args = self._safe_str(getattr(event, 'args', {}))
            
            message = {
                "event": "tool_start",
                "data": {
                    "tool": tool_name,
                    "args": args,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            self._put_event_sync(message)
            _safe_log(f"[事件监听器] 工具开始: {tool_name}")
        except Exception as e:
            if "CrewStopException" in str(type(e)): raise e
            _safe_log(f"[事件监听器] 处理 tool_start 事件失败: {e}")
    
    def _handle_tool_finish(self, source: Any, event: ToolUsageFinishedEvent):
        """
        处理 Tool 使用完成事件。
        """
        try:
            self._check_interruption()
            
            tool_name = getattr(event, 'tool_name', '未知工具')
            # 记录原始输出，不进行截断
            output = self._safe_str(getattr(event, 'output', "无输出"))
            
            message = {
                "event": "tool_finish",
                "data": {
                    "tool": tool_name,
                    "output": output,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            self._put_event_sync(message)
            _safe_log(f"[事件监听器] 工具完成: {tool_name}")
            
            # 工具执行完后检查新文件
            self._check_and_emit_files()
        except Exception as e:
            if "CrewStopException" in str(type(e)): raise e
            _safe_log(f"[事件监听器] 处理 tool_finish 事件失败: {e}")

    def _check_and_emit_files(self):
        """检查新文件并发送事件"""
        try:
            new_files = self._track_generated_files()
            if new_files:
                # 发送文件生成事件
                # 注意：这里发送的是累积的所有新文件，还是增量？
                # 前端 setFiles 是替换操作，所以应该发送所有累积的新文件
                # 但 _track_generated_files 目前返回的是所有新文件（相对于初始状态）
                # 所以直接发送即可
                
                message = {
                    "event": "files_generated",
                    "data": {
                        "files": [os.path.basename(f) for f in self.generated_files], # 只发送文件名
                        "timestamp": datetime.now().isoformat()
                    }
                }
                self._put_event_sync(message)
        except Exception as e:
            _safe_log(f"[事件监听器] 文件追踪失败: {e}")
    
    def _track_generated_files(self):
        """
        追踪执行过程中生成的新文件（优化版：增量扫描）
        """
        result_dir = os.path.join(settings.EASYSTAT_PROJECT_PATH, "result")
        
        if not os.path.exists(result_dir):
            return []
        
        # 优化：仅扫描最近 1 小时内修改过的文件，减少大规模文件下的性能开销
        import time
        now = time.time()
        one_hour_ago = now - 3600
        
        # 获取当前所有文件（带过滤）
        current_files = set()
        for root, dirs, files in os.walk(result_dir):
            for f in files:
                full_path = os.path.join(root, f)
                try:
                    if os.path.getmtime(full_path) > one_hour_ago:
                        current_files.add(full_path)
                except OSError:
                    continue
        
        # 找出新文件
        new_files = list(current_files - self.initial_files)
        
        # 过滤掉目录，只保留文件
        new_files = [f for f in new_files if os.path.isfile(f)]
        
        # 累积更新生成的列表
        for f in new_files:
            if f not in self.generated_files:
                self.generated_files.append(f)
        
        if new_files:
            _safe_log(f"[事件监听器] 发现新生成文件: {len(new_files)} 个")
        
        return new_files
    
    def _put_event_sync(self, message: dict):
        """
        同步方式将事件放入异步队列，并过滤装饰性字符。
        
        Args:
            message (dict): 事件消息字典，格式为 {"event": "...", "data": {...}}
        """
        # 装饰性字符过滤逻辑
        if "data" in message:
            for key in ["message", "output", "task", "agent", "tool", "args"]:
                if key in message["data"] and isinstance(message["data"][key], str):
                    val = message["data"][key]
                    # 过滤 CrewAI 常见的装饰性字符和 ANSI 转义码
                    # 过滤 🚀, ╭───, ╰───, ├───, │ 等
                    val = re.sub(r'[🚀╭╮╯╰─│├┤]+', '', val)
                    # 过滤 ANSI 转义码
                    val = re.sub(r'\x1b\[[0-9;]*[mGKH]', '', val)
                    message["data"][key] = val.strip()

        loop = self.event_queue._my_loop
        
        # 同步写入本地日志文件
        self._write_to_log_file(message)
        
        asyncio.run_coroutine_threadsafe(
            self.event_queue.put(message),
            loop
        )

    def _write_to_log_file(self, message: dict):
        """
        将事件消息写入本地日志文件
        
        Args:
            message (dict): 事件消息字典
        """
        try:
            event_type = message.get("event", "unknown")
            data = message.get("data", {})
            timestamp = data.get("timestamp", datetime.now().isoformat())
            
            log_entry = f"[{timestamp}] [{event_type.upper()}] "
            
            if event_type == "agent_start":
                log_entry += f"智能体: {data.get('agent')}\n任务: {data.get('task')}\n"
            elif event_type == "agent_complete":
                log_entry += f"智能体: {data.get('agent')}\n输出: {data.get('output')[:500]}...\n"
            elif event_type == "tool_start":
                log_entry += f"工具: {data.get('tool')}\n参数: {data.get('args')}\n"
            elif event_type == "tool_finish":
                log_entry += f"工具: {data.get('tool')}\n结果: {data.get('output')[:500]}...\n"
            elif event_type == "task_start":
                log_entry += f"任务开始: {data.get('task')}\n"
            elif event_type == "task_complete":
                log_entry += f"任务完成: {data.get('task')}\n"
            elif event_type == "error":
                log_entry += f"[ERROR] 错误详情: {data.get('error')}\n"
            else:
                log_entry += f"{str(data)}\n"
                
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry + "-"*50 + "\n")
        except Exception as e:
            _safe_log(f"[事件监听器] 写入日志文件失败: {e}")
