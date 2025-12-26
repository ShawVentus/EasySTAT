"""
诊断 event_listener.py 中的递归错误

测试目标：
1. 验证 _safe_str() 方法在处理循环引用对象时的行为
2. 模拟 CrewAI 的 Agent/Event 对象结构
3. 复现 "maximum recursion depth exceeded" 错误
"""

import sys
sys.path.insert(0, '/Users/mac/dev/personal/br_competition/easystat-webui/backend')

from typing import Any


class MockAgent:
    """模拟 CrewAI 的 Agent 对象"""
    def __init__(self, role: str, goal: str):
        self.role = role
        self.goal = goal
        self.crew = None  # 会被设置为 MockCrew 实例
        self.tools = []
    
    def __str__(self):
        # Pydantic BaseModel 的 __str__ 会序列化所有属性
        # 这会触发 crew 的序列化，从而导致递归
        return f"MockAgent(role={self.role}, crew={self.crew})"
    
    def __repr__(self):
        return self.__str__()


class MockCrew:
    """模拟 CrewAI 的 Crew 对象"""
    def __init__(self):
        self.agents = []
    
    def add_agent(self, agent: MockAgent):
        self.agents.append(agent)
        agent.crew = self  # 形成循环引用
    
    def __str__(self):
        return f"MockCrew(agents={self.agents})"


class MockEvent:
    """模拟 AgentExecutionCompletedEvent"""
    def __init__(self, agent: MockAgent, output: str):
        self.agent = agent
        self.output = output


def test_circular_reference_detection():
    """测试1：验证循环检测机制是否有效"""
    print("\n=== 测试1: 循环引用检测 ===")
    
    # 创建循环引用结构
    agent = MockAgent(role="金融数据采集专家", goal="采集股票数据")
    crew = MockCrew()
    crew.add_agent(agent)
    
    # 验证循环引用存在
    print(f"Agent.crew: {type(agent.crew)}")
    print(f"Crew.agents[0] is Agent: {crew.agents[0] is agent}")
    
    # 测试 _safe_str() 的行为
    from services.event_listener import EasyStatEventListener
    import asyncio
    
    # 创建事件队列（虽然不会用到）
    loop = asyncio.new_event_loop()
    queue = asyncio.Queue()
    queue._my_loop = loop
    
    listener = EasyStatEventListener(event_queue=queue)
    
    try:
        # 这应该会触发递归问题（如果修复前）
        result = listener._safe_str(agent)
        print(f"✅ _safe_str() 成功返回: {result[:100]}...")
    except RecursionError as e:
        print(f"❌ 递归错误: {e}")
    except Exception as e:
        print(f"❌ 其他错误: {type(e).__name__}: {e}")


def test_safe_str_with_basic_types():
    """测试2：验证基本类型处理"""
    print("\n=== 测试2: 基本类型处理 ===")
    
    from services.event_listener import EasyStatEventListener
    import asyncio
    
    loop = asyncio.new_event_loop()
    queue = asyncio.Queue()
    queue._my_loop = loop
    listener = EasyStatEventListener(event_queue=queue)
    
    test_cases = [
        ("字符串", "测试字符串"),
        ("整数", 42),
        ("浮点数", 3.14),
        ("布尔值", True),
        ("None", None),
        ("列表", [1, 2, 3]),
        ("字典", {"key": "value"}),
    ]
    
    for name, obj in test_cases:
        try:
            result = listener._safe_str(obj)
            print(f"✅ {name}: {result}")
        except Exception as e:
            print(f"❌ {name} 失败: {e}")


def test_str_vs_repr_on_agent():
    """测试3：直接对比 str() 和 _safe_str() 的行为"""
    print("\n=== 测试3: str() vs _safe_str() ===")
    
    agent = MockAgent(role="测试专家", goal="测试目标")
    crew = MockCrew()
    crew.add_agent(agent)
    
    # 测试直接调用 str()
    print("尝试直接调用 str(agent):")
    try:
        result = str(agent)
        print(f"✅ str() 成功: {result}")
    except RecursionError:
        print("❌ str() 触发递归错误（预期行为）")
    
    # 测试 _safe_str()
    print("\n尝试调用 _safe_str(agent):")
    from services.event_listener import EasyStatEventListener
    import asyncio
    
    loop = asyncio.new_event_loop()
    queue = asyncio.Queue()
    queue._my_loop = loop
    listener = EasyStatEventListener(event_queue=queue)
    
    try:
        result = listener._safe_str(agent)
        print(f"✅ _safe_str() 成功: {result}")
    except RecursionError:
        print("❌ _safe_str() 仍然触发递归错误（BUG确认）")
    except Exception as e:
        print(f"❌ _safe_str() 其他错误: {e}")


def test_line_193_issue():
    """测试4：验证第193行 return str(item) 的问题"""
    print("\n=== 测试4: 第193行兜底逻辑测试 ===")
    
    # 创建一个不符合任何特殊处理的对象
    class CustomObject:
        def __init__(self):
            self.circular_ref = self
        
        def __str__(self):
            # 这个 __str__ 会访问 circular_ref，导致无限递归
            return f"CustomObject(ref={self.circular_ref})"
    
    obj = CustomObject()
    
    from services.event_listener import EasyStatEventListener
    import asyncio
    
    loop = asyncio.new_event_loop()
    queue = asyncio.Queue()
    queue._my_loop = loop
    listener = EasyStatEventListener(event_queue=queue)
    
    print("测试对象: 自引用的 CustomObject")
    try:
        result = listener._safe_str(obj)
        print(f"✅ _safe_str() 成功: {result}")
    except RecursionError:
        print("❌ 第193行 return str(item) 触发递归（BUG确认）")


if __name__ == "__main__":
    print("=" * 60)
    print("EasySTAT WebUI 事件监听器递归错误诊断")
    print("=" * 60)
    
    test_safe_str_with_basic_types()
    test_circular_reference_detection()
    test_str_vs_repr_on_agent()
    test_line_193_issue()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
