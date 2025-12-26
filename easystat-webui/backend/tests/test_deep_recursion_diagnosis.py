"""
深入诊断：模拟真实的 CrewAI Agent 完成事件

目标：复现终端中显示的错误
[事件监听器] 处理 agent_complete 事件失败: maximum recursion depth exceeded
"""

import sys
sys.path.insert(0, '/Users/mac/dev/personal/br_competition/easystat-webui/backend')

from typing import Any
import asyncio


class SimulatedBaseAgent:
    """更真实地模拟 CrewAI BaseAgent（Pydantic BaseModel）"""
    def __init__(self, role: str, goal: str):
        self.id = "test-uuid"
        self.role = role
        self.goal = goal
        self.backstory = "专业的金融分析专家"
        self.crew = None
        self.tools = []
        self.agent_executor = None
        self.llm = {"model": "qwen-plus"}
        
    def __str__(self):
        """Pydantic BaseModel 的 __str__ 方法会打印所有字段"""
        # 这会触发对 crew 的字符串化，导致循环
        fields = {
            'id': self.id,
            'role': self.role,
            'goal': self.goal,
            'backstory': self.backstory,
            'crew': self.crew,  # 这里会触发递归
            'tools': self.tools,
        }
        return f"SimulatedBaseAgent({fields})"


class SimulatedCrew:
    """模拟 Crew 对象"""
    def __init__(self):
        self.agents = []
        self.tasks = []
        
    def add_agent(self, agent):
        self.agents.append(agent)
        agent.crew = self
    
    def __str__(self):
        return f"SimulatedCrew(agents_count={len(self.agents)})"


class SimulatedAgentExecutionCompletedEvent:
    """模拟 AgentExecutionCompletedEvent"""
    def __init__(self, agent, task, output: str):
        self.agent = agent
        self.task = task
        self.output = output
        self.timestamp = "2025-12-26T11:41:16"
        self.type = "agent_execution_completed"


def test_real_agent_complete_handler():
    """
    测试真实的 _handle_agent_complete 流程
    复现用户terminal中看到的错误
    """
    print("\n=== 真实场景模拟：agent_complete 事件处理 ===\n")
    
    # 1. 创建带循环引用的 Agent 和 Crew
    agent = SimulatedBaseAgent(
        role="金融数据采集专家",
        goal="采集贵州茅台的资金流数据"
    )
    crew = SimulatedCrew()
    crew.add_agent(agent)
    
    print(f"✓ 创建了 Agent: {agent.role}")
    print(f"✓ Agent.crew: {type(agent.crew)}")
    print(f"✓ 循环引用已建立: {crew.agents[0] is agent}\n")
    
    # 2. 创建事件
    event = SimulatedAgentExecutionCompletedEvent(
        agent=agent,
        task={"name": "fetch_capital_flow_task"},
        output='{"data_ref": "flow_stock_flow_all_stocks_today_hybrid_600519", ...}'
    )
    
    # 3. 导入事件监听器
    from services.event_listener import EasyStatEventListener
    
    loop = asyncio.new_event_loop()
    queue = asyncio.Queue()
    queue._my_loop = loop
    
    listener = EasyStatEventListener(event_queue=queue)
    
    # 4. 调用 _handle_agent_complete
    print("开始调用 _handle_agent_complete()...\n")
    
    try:
        listener._handle_agent_complete(source=None, event=event)
        print("✅ _handle_agent_complete() 成功执行\n")
    except RecursionError as e:
        print(f"❌ 递归错误: {e}\n")
        import traceback
        print("堆栈跟踪:")
        traceback.print_exc()
    except Exception as e:
        print(f"❌ 其他错误: {type(e).__name__}: {e}\n")
        import traceback
        traceback.print_exc()


def test_print_statement_recursion():
    """
    测试关键假设：print() 语句中的 f-string 是否会触发递归？
    print(f"[事件监听器] Agent 完成: {agent_role}")
    """
    print("\n=== 测试 print f-string 是否触发递归 ===\n")
    
    agent = SimulatedBaseAgent(role="测试专家", goal="测试")
    crew = SimulatedCrew()
    crew.add_agent(agent)
    
    # 模拟第252行
    agent_obj = agent
    agent_role = getattr(agent_obj, 'role', '未知角色')
    
    print(f"agent_role 的类型: {type(agent_role)}")
    print(f"agent_role 的值: {repr(agent_role)}")
    
    # 模拟第265行
    try:
        print(f"[事件监听器] Agent 完成: {agent_role}")
        print("✅ print 语句执行成功，不会触发递归\n")
    except RecursionError:
        print("❌ print 语句触发递归\n")


def test_str_conversion_in_exception_handler():
    """
    关键测试：在 except 块中调用 str(e) 是否会触发递归？
    第268行: print(f"[事件监听器] 处理 agent_complete 事件失败: {e}")
    """
    print("\n=== 测试 except 块中的递归 ===\n")
    
    class RecursiveException(Exception):
        def __init__(self, obj):
            self.obj = obj
        
        def __str__(self):
            # 如果 obj 有循环引用，这里会递归
            return f"RecursiveException with obj: {self.obj}"
    
    agent = SimulatedBaseAgent(role="测试", goal="测试")
    crew = SimulatedCrew()
    crew.add_agent(agent)
    
    try:
        raise RecursiveException(agent)
    except Exception as e:
        try:
            print(f"捕获异常: {e}")
        except RecursionError:
            print("❌ 在 except 中打印异常时触发递归！")


if __name__ == "__main__":
    print("=" * 70)
    print("深入诊断：maximum recursion depth exceeded 根因分析")
    print("=" * 70)
    
    test_print_statement_recursion()
    test_str_conversion_in_exception_handler()
    test_real_agent_complete_handler()
    
    print("\n" + "=" * 70)
    print("诊断完成")
    print("=" * 70)
