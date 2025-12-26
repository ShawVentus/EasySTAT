"""
使用真实 CrewAI 对象的递归错误测试

目标：
1. 用真实的 CrewAI Agent、Crew、Task 对象
2. 复现用户终端中的实际错误场景
3. 测试 _put_event_sync 和 _write_to_log_file 的完整流程
"""

import os
import sys

# 加载 EasySTAT 的环境变量配置（包含 LLM API key）
from dotenv import load_dotenv
load_dotenv('/Users/mac/dev/personal/br_competition/EasySTAT/.env')

print(f"✓ 已加载环境变量")
print(f"  OPENAI_API_KEY: {'已设置' if os.getenv('OPENAI_API_KEY') else '未设置'}")
print(f"  OPENAI_MODEL_NAME: {os.getenv('OPENAI_MODEL_NAME')}\n")

sys.path.insert(0, '/Users/mac/dev/personal/br_competition/easystat-webui/backend')

import asyncio
from datetime import datetime



def test_real_crewai_agent_recursion():
    """
    测试1：使用真实的 CrewAI Agent 对象
    """
    print("\n=== 测试1: 真实 CrewAI Agent 对象递归测试 ===\n")
    
    try:
        from crewai import Agent, Task, Crew
        from crewai.tools import tool
        print("✓ 成功导入 CrewAI\n")
    except ImportError as e:
        print(f"❌ 无法导入 CrewAI: {e}")
        return
    
    # 创建真实的 Agent
    print("创建真实的 CrewAI Agent...")
    agent = Agent(
        role="金融数据采集专家",
        goal="采集和整理股票市场数据",
        backstory="专业的金融数据分析师，擅长从各种渠道采集数据",
        verbose=True
    )
    
    print(f"✓ Agent 创建成功: {type(agent)}")
    print(f"  - role: {agent.role}")
    print(f"  - id: {agent.id}")
    
    # 创建 Crew（这会建立 agent.crew 的循环引用）
    print("\n创建 Crew 并添加 Agent...")
    crew = Crew(
        agents=[agent],
        tasks=[],  # 暂时不添加任务
        verbose=True
    )
    
    print(f"✓ Crew 创建成功: {type(crew)}")
    print(f"✓ 循环引用检查: agent.crew is crew -> {agent.crew is crew}")
    print(f"✓ 循环引用检查: crew.agents[0] is agent -> {crew.agents[0] is agent}\n")
    
    # 测试 _safe_str() 对真实 Agent 的处理
    from services.event_listener import EasyStatEventListener
    
    loop = asyncio.new_event_loop()
    queue = asyncio.Queue()
    queue._my_loop = loop
    
    listener = EasyStatEventListener(event_queue=queue)
    
    print("测试 _safe_str() 处理真实 Agent...")
    try:
        result = listener._safe_str(agent)
        print(f"✅ _safe_str(agent) 成功")
        print(f"   结果: {result[:200]}...")
    except RecursionError as e:
        print(f"❌ _safe_str(agent) 触发递归错误!")
        import traceback
        traceback.print_exc()
        return
    
    # 测试处理真实 Agent 的 __str__
    print("\n测试直接调用 str(agent)...")
    try:
        agent_str = str(agent)
        print(f"✅ str(agent) 成功")
        print(f"   长度: {len(agent_str)} 字符")
        print(f"   前200字符: {agent_str[:200]}...")
    except RecursionError:
        print(f"❌ str(agent) 触发递归错误!")
        return


def test_real_agent_complete_event():
    """
    测试2：创建真实的 AgentExecutionCompletedEvent 并处理
    """
    print("\n\n=== 测试2: 真实 AgentExecutionCompletedEvent 处理 ===\n")
    
    try:
        from crewai import Agent, Crew
        from crewai.events import AgentExecutionCompletedEvent
        print("✓ 成功导入所需模块\n")
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return
    
    # 创建真实的 Agent 和 Crew
    agent = Agent(
        role="测试专家",
        goal="执行测试任务",
        backstory="专业测试人员"
    )
    
    crew = Crew(
        agents=[agent],
        tasks=[],
        verbose=False
    )
    
    print(f"✓ Agent 和 Crew 已创建\n")
    
    # 创建真实的事件对象
    # 注意：我们需要模拟一个真实的任务对象
    class MockTask:
        def __init__(self):
            self.description = "测试任务"
            self.expected_output = "测试结果"
            self.agent = agent
    
    task = MockTask()
    
    print("创建 AgentExecutionCompletedEvent...")
    event = AgentExecutionCompletedEvent(
        agent=agent,
        task=task,
        output="任务完成，输出结果..."
    )
    
    print(f"✓ Event 创建成功: {type(event)}")
    print(f"  - event.agent: {type(event.agent)}")
    print(f"  - event.task: {type(event.task)}")
    print(f"  - event.output: {type(event.output)}\n")
    
    # 测试事件监听器处理
    from services.event_listener import EasyStatEventListener
    
    loop = asyncio.new_event_loop()
    queue = asyncio.Queue()
    queue._my_loop = loop
    
    listener = EasyStatEventListener(event_queue=queue)
    
    print("调用 _handle_agent_complete()...")
    try:
        listener._handle_agent_complete(source=None, event=event)
        print("✅ _handle_agent_complete() 成功执行\n")
    except RecursionError as e:
        print(f"❌ 递归错误: {e}\n")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"❌ 其他错误: {type(e).__name__}: {e}\n")
        import traceback
        traceback.print_exc()


def test_complex_nested_structure():
    """
    测试3：复杂嵌套结构 - Agent 的属性中包含更深层的循环引用
    """
    print("\n\n=== 测试3: 复杂嵌套结构测试 ===\n")
    
    try:
        from crewai import Agent, Crew
        from crewai.tools import tool
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return
    
    # 创建多个相互引用的 Agent
    print("创建多个 Agent 形成复杂引用网络...")
    
    agent1 = Agent(
        role="Agent1",
        goal="任务1",
        backstory="背景1"
    )
    
    agent2 = Agent(
        role="Agent2", 
        goal="任务2",
        backstory="背景2"
    )
    
    agent3 = Agent(
        role="Agent3",
        goal="任务3", 
        backstory="背景3"
    )
    
    # 创建 Crew，所有 Agent 都引用同一个 Crew
    crew = Crew(
        agents=[agent1, agent2, agent3],
        tasks=[],
        verbose=False
    )
    
    print(f"✓ 创建了 3 个 Agent")
    print(f"✓ 所有 Agent 都引用同一个 Crew")
    print(f"  - agent1.crew is crew: {agent1.crew is crew}")
    print(f"  - agent2.crew is crew: {agent2.crew is crew}")
    print(f"  - agent3.crew is crew: {agent3.crew is crew}")
    print(f"  - crew.agents 包含所有 3 个 agent\n")
    
    # 测试 _safe_str
    from services.event_listener import EasyStatEventListener
    import asyncio
    
    loop = asyncio.new_event_loop()
    queue = asyncio.Queue()
    queue._my_loop = loop
    
    listener = EasyStatEventListener(event_queue=queue)
    
    print("测试对每个 Agent 调用 _safe_str()...")
    for i, agent in enumerate([agent1, agent2, agent3], 1):
        try:
            result = listener._safe_str(agent)
            print(f"  ✅ Agent{i}: {result[:100]}...")
        except RecursionError:
            print(f"  ❌ Agent{i}: 递归错误!")
            import traceback
            traceback.print_exc()
            return


def test_str_on_line_193():
    """
    测试4：专门测试第193行的 str(item) 调用
    通过构造一个不符合任何特殊条件的对象，强制走到第193行
    """
    print("\n\n=== 测试4: 第193行 str(item) 调用测试 ===\n")
    
    try:
        from crewai import Agent, Crew
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return
    
    # 创建 Agent 和 Crew
    agent = Agent(
        role="测试",
        goal="测试",
        backstory="测试"
    )
    
    crew = Crew(agents=[agent], tasks=[], verbose=False)
    
    # 创建一个包装对象，这个对象：
    # 1. 没有 'role' 属性（不会匹配第169行）
    # 2. 没有 'description' 和 'expected_output'（不会匹配第175行）
    # 3. 不是 list 或 dict（不会匹配第180、185行）
    # 4. 会走到第193行的 return str(item)
    
    class WeirdWrapper:
        """一个奇怪的包装类，内部引用 Agent"""
        def __init__(self, agent):
            self.wrapped_agent = agent
            self.data = {"agent": agent}  # 额外的循环路径
        
        def __str__(self):
            # 这个 __str__ 会尝试序列化 wrapped_agent
            # 如果 wrapped_agent 有循环引用，这会导致递归
            return f"WeirdWrapper(agent={self.wrapped_agent}, data={self.data})"
    
    wrapper = WeirdWrapper(agent)
    
    print(f"创建了 WeirdWrapper 对象")
    print(f"  - wrapper.wrapped_agent: {type(wrapper.wrapped_agent)}")
    print(f"  - wrapper.wrapped_agent.crew: {type(wrapper.wrapped_agent.crew)}\n")
    
    from services.event_listener import EasyStatEventListener
    import asyncio
    
    loop = asyncio.new_event_loop()
    queue = asyncio.Queue()
    queue._my_loop = loop
    
    listener = EasyStatEventListener(event_queue=queue)
    
    print("测试 _safe_str(wrapper)，应该会走到第193行...")
    try:
        result = listener._safe_str(wrapper)
        print(f"结果: {result[:200]}...")
        
        # 检查结果是否包含错误信息
        if "Error" in result or "Recursion" in result:
            print("\n⚠️ 注意：结果中包含错误信息，说明确实遇到了递归！")
            print(f"完整结果: {result}")
        else:
            print("\n✅ 成功处理，没有递归错误")
            
    except RecursionError:
        print("❌ 触发了 RecursionError!")
        import traceback
        traceback.print_exc()


def test_write_to_log_file():
    """
    测试5：测试 _write_to_log_file 是否会触发递归
    """
    print("\n\n=== 测试5: _write_to_log_file 递归测试 ===\n")
    
    try:
        from crewai import Agent, Crew
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return
    
    agent = Agent(role="测试", goal="测试", backstory="测试")
    crew = Crew(agents=[agent], tasks=[], verbose=False)
    
    from services.event_listener import EasyStatEventListener
    import asyncio
    
    loop = asyncio.new_event_loop()
    queue = asyncio.Queue()
    queue._my_loop = loop
    
    listener = EasyStatEventListener(event_queue=queue)
    
    # 构造包含复杂对象的消息
    message = {
        "event": "agent_complete",
        "data": {
            "agent": agent.role,  # 这是字符串，应该安全
            "output": "测试输出" * 100,  # 长字符串
            "timestamp": datetime.now().isoformat()
        }
    }
    
    print(f"测试 _write_to_log_file()...")
    try:
        listener._write_to_log_file(message)
        print(f"✅ _write_to_log_file() 成功")
        print(f"   日志文件: {listener.log_file}")
    except RecursionError:
        print(f"❌ _write_to_log_file() 触发递归!")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"⚠️ 其他错误: {e}")


if __name__ == "__main__":
    print("=" * 70)
    print("真实 CrewAI 对象递归错误深度测试")
    print("=" * 70)
    
    test_real_crewai_agent_recursion()
    test_real_agent_complete_event()
    test_complex_nested_structure()
    test_str_on_line_193()
    test_write_to_log_file()
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)
