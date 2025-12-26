"""
关键发现测试：agent.crew 引用问题

测试发现: agent.crew is not crew，这很奇怪
需要深入调查 CrewAI 的内部行为
"""

import os
import sys

from dotenv import load_dotenv
load_dotenv('/Users/mac/dev/personal/br_competition/EasySTAT/.env')

sys.path.insert(0, '/Users/mac/dev/personal/br_competition/easystat-webui/backend')

import asyncio


def test_agent_crew_reference_mystery():
    """
    深入调查 agent.crew 的引用关系
    """
    print("\n=== agent.crew 引用关系调查 ===\n")
    
    from crewai import Agent, Crew
    
    agent1 = Agent(role="Agent1", goal="Goal1", backstory="Back1")
    agent2 = Agent(role="Agent2", goal="Goal2", backstory="Back2")
    
    print(f"创建 Agent 后:")
    print(f"  agent1.crew: {agent1.crew}")
    print(f"  agent2.crew: {agent2.crew}\n")
    
    crew = Crew(agents=[agent1, agent2], tasks=[], verbose=False)
    
    print(f"创建 Crew 后:")
    print(f"  crew: {crew}")
    print(f"  crew.agents: {crew.agents}")
    print(f"  crew.agents[0] is agent1: {crew.agents[0] is agent1}")
    print(f"  crew.agents[1] is agent2: {crew.agents[1] is agent2}\n")
    
    print(f"  agent1.crew: {agent1.crew}")
    print(f"  agent2.crew: {agent2.crew}")
    print(f"  agent1.crew is crew: {agent1.crew is crew}")
    print(f"  agent2.crew is crew: {agent2.crew is crew}")
    print(f"  agent1.crew is agent2.crew: {agent1.crew is agent2.crew}\n")
    
    # 检查 crew 对象的属性
    print(f"Crew 对象的类型: {type(crew)}")
    print(f"Agent 的 crew 属性类型: {type(agent1.crew) if agent1.crew else None}\n")
    
    # 尝试触发实际的 crew 执行
    print("=" * 60)
    print("尝试让 crew.kickoff() 触发实际执行...")
    print("=" * 60)


def test_after_crew_execution():
    """
    测试在 crew 实际执行后会发生什么
    这可能会建立循环引用
    """
    print("\n\n=== Crew 执行后的引用关系测试 ===\n")
    
    from crewai import Agent, Crew, Task
    
    # 创建 Agent
    agent = Agent(
        role="测试专家",
        goal="完成测试任务",
        backstory="专业测试人员",
        verbose=False
    )
    
    # 创建一个简单的 Task
    task = Task(
        description="输出一个简单的测试结果",
        expected_output="测试完成",
        agent=agent
    )
    
    print(f"创建 Task 后:")
    print(f"  task.agent: {task.agent}")
    print(f"  task.agent is agent: {task.agent is agent}\n")
    
    # 创建 Crew
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=False
    )
    
    print(f"创建 Crew 后（执行前）:")
    print(f"  agent.crew: {agent.crew}")
    print(f"  agent.crew is crew: {agent.crew is crew if agent.crew else 'N/A'}\n")
    
    # ⚠️ 关键：实际执行 crew
    # 这可能会改变对象的引用关系
    
    print("⚠️ 准备执行 crew.kickoff()...")
    print("这可能会触发循环引用的建立\n")
    
    try:
        # 注意：我们不真正执行，因为这需要真实的 LLM 调用
        # 但我们可以看看对象的状态变化
        
        # result = crew.kickoff()
        
        print("（跳过实际执行，避免 LLM 调用）\n")
        
    except Exception as e:
        print(f"执行出错: {e}\n")
    
    print(f"（假设执行后）:")
    print(f"  agent.crew: {agent.crew}")
    print(f"  如果引用关系改变，这里可能建立循环引用\n")


def test_pydantic_copy_behavior():
    """
    测试 Pydantic 的 copy 和深拷贝行为
    CrewAI 的 Agent 是 Pydantic BaseModel，可能有特殊的拷贝逻辑
    """
    print("\n\n=== Pydantic Copy 行为测试 ===\n")
    
    from crewai import Agent, Crew
    
    agent = Agent(role="原始Agent", goal="目标", backstory="背景")
    
    print(f"原始 agent: {id(agent)}")
    print(f"原始 agent.crew: {agent.crew}\n")
    
    # 测试 model_copy
    copied_agent = agent.model_copy()
    
    print(f"复制后的 agent: {id(copied_agent)}")
    print(f"复制后的 agent.crew: {copied_agent.crew}")
    print(f"copied_agent is agent: {copied_agent is agent}")
    print(f"copied_agent == agent: {copied_agent == agent}\n")
    
    # Crew 可能在内部做了 agent 的复制
    crew = Crew(agents=[agent], tasks=[], verbose=False)
    
    print(f"创建 Crew 后:")
    print(f"  crew.agents[0]: {id(crew.agents[0])}")
    print(f"  原始 agent: {id(agent)}")
    print(f"  crew.agents[0] is agent: {crew.agents[0] is agent}\n")


def test_actual_recursion_trigger():
    """
    尝试找到真正触发递归的场景
    """
    print("\n\n=== 寻找真正触发递归的场景 ===\n")
    
    from crewai import Agent, Crew
    from services.event_listener import EasyStatEventListener
    
    # 创建一个复杂的对象结构
    agent1 = Agent(role="A1", goal="G1", backstory="B1")
    agent2 = Agent(role="A2", goal="G2", backstory="B2")
    
    crew = Crew(agents=[agent1, agent2], tasks=[], verbose=False)
    
    loop = asyncio.new_event_loop()
    queue = asyncio.Queue()
    queue._my_loop = loop
    listener = EasyStatEventListener(event_queue=queue)
    
    # 测试各种可能导致递归的对象
    test_objects = [
        ("agent1", agent1),
        ("agent2", agent2),
        ("crew", crew),
        ("crew.agents", crew.agents),
        ("agent1.crew", agent1.crew),
    ]
    
    for name, obj in test_objects:
        print(f"测试 _safe_str({name})...")
        try:
            result = listener._safe_str(obj)
            if "Error" in str(result) or "Recursion" in str(result):
                print(f"  ⚠️ 发现错误: {result}")
            else:
                print(f"  ✅ 成功: {result[:80]}...")
        except RecursionError:
            print(f"  ❌ RecursionError!")
            import traceback
            traceback.print_exc()
        except Exception as e:
            print(f"  ⚠️ 其他错误: {e}")
        print()


if __name__ == "__main__":
    print("=" * 70)
    print("agent.crew 引用关系深度调查")
    print("=" * 70)
    
    test_agent_crew_reference_mystery()
    test_after_crew_execution()
    test_pydantic_copy_behavior()
    test_actual_recursion_trigger()
    
    print("\n" + "=" * 70)
    print("调查完成")
    print("=" * 70)
