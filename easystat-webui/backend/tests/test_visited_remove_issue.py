"""
测试 visited.remove() 导致的循环检测失效问题

关键假设：finally 块中的 visited.remove(item_id) 可能导致：
1. 同一个对象在复杂嵌套结构中被"解锁"后再次访问
2. 导致无限递归
"""

def test_visited_remove_problem():
    """
    复现 finally 块中 visited.remove() 的问题
    """
    print("\n=== 测试 visited.remove() 导致的循环检测失效 ===\n")
    
    visited = set()
    
    class Node:
        def __init__(self, name):
            self.name = name
            self.children = []
            self.parent = None
        
        def add_child(self, child):
            self.children.append(child)
            child.parent = self
    
    # 创建一个复杂的循环结构：
    # A -> B -> C
    # ^         |
    # |_________|
    
    a = Node("A")
    b = Node("B")
    c = Node("C")
    
    a.add_child(b)
    b.add_child(c)
    c.add_child(a)  # 循环引用
    
    def traverse_with_remove(node, depth=0):
        """模拟 event_listener.py 的 _recursive_convert 逻辑"""
        indent = "  " * depth
        node_id = id(node)
        
        print(f"{indent}访问: {node.name} (id={node_id})")
        
        if node_id in visited:
            print(f"{indent}  └─ 检测到循环引用，跳过")
            return f"<CircularRef: {node.name}>"
        
        visited.add(node_id)
        print(f"{indent}  └─ 标记为已访问，visited={len(visited)}")
        
        try:
            result = [f"{node.name}"]
            for child in node.children:
                child_result = traverse_with_remove(child, depth + 1)
                result.append(child_result)
            return " -> ".join(result)
        finally:
            # 问题所在：回溯时移除标记
            try:
                visited.remove(node_id)
                print(f"{indent}  └─ finally: 移除标记，visited={len(visited)}")
            except KeyError:
                print(f"{indent}  └─ finally: 标记已被移除")
    
    print("开始遍历（带 visited.remove）:\n")
    try:
        result = traverse_with_remove(a)
        print(f"\n✅ 遍历完成: {result}")
    except RecursionError:
        print("\n❌ 递归错误！visited.remove() 导致循环检测失效")


def test_visited_without_remove():
    """
    对比测试：不使用 visited.remove() 的版本
    """
    print("\n\n=== 对比测试：不使用 visited.remove() ===\n")
    
    visited = set()
    
    class Node:
        def __init__(self, name):
            self.name = name
            self.children = []
            self.parent = None
        
        def add_child(self, child):
            self.children.append(child)
            child.parent = self
    
    a = Node("A")
    b = Node("B")
    c = Node("C")
    
    a.add_child(b)
    b.add_child(c)
    c.add_child(a)
    
    def traverse_without_remove(node, depth=0):
        """不移除标记的版本"""
        indent = "  " * depth
        node_id = id(node)
        
        print(f"{indent}访问: {node.name} (id={node_id})")
        
        if node_id in visited:
            print(f"{indent}  └─ 检测到循环引用，跳过")
            return f"<CircularRef: {node.name}>"
        
        visited.add(node_id)
        print(f"{indent}  └─ 标记为已访问，visited={len(visited)}")
        
        result = [f"{node.name}"]
        for child in node.children:
            child_result = traverse_without_remove(child, depth + 1)
            result.append(child_result)
        return " -> ".join(result)
    
    print("开始遍历（不移除标记）:\n")
    result = traverse_without_remove(a)
    print(f"\n✅ 遍历完成: {result}")


def test_real_scenario_simulation():
    """
    模拟真实场景：Agent 对象的复杂嵌套
    """
    print("\n\n=== 真实场景：Agent嵌套结构 ===\n")
    
    class MockAgent:
        def __init__(self, role):
            self.role = role
            self.crew = None
            self.tools = []
            self.memory = {}
        
        def __str__(self):
            return f"Agent({self.role}, crew={self.crew})"
    
    class MockCrew:
        def __init__(self):
            self.agents = []
        
        def add_agent(self, agent):
            self.agents.append(agent)
            agent.crew = self
        
        def __str__(self):
            return f"Crew(agents={[a.role for a in self.agents]})"
    
    # 创建真实的结构
    agent1 = MockAgent("数据采集专家")
    agent2 = MockAgent("分析专家")
    crew = MockCrew()
    crew.add_agent(agent1)
    crew.add_agent(agent2)
    
    # 测试当前 event_listener.py 的 _safe_str 实现
    import sys
    sys.path.insert(0, '/Users/mac/dev/personal/br_competition/easystat-webui/backend')
    
    from services.event_listener import EasyStatEventListener
    import asyncio
    
    loop = asyncio.new_event_loop()
    queue = asyncio.Queue()
    queue._my_loop = loop
    listener = EasyStatEventListener(event_queue=queue)
    
    print(f"测试对象: {agent1.role}")
    print(f"循环引用: agent1.crew.agents[0] is agent1 -> {agent1.crew.agents[0] is agent1}\n")
    
    try:
        result = listener._safe_str(agent1)
        print(f"✅ _safe_str() 成功: {result}\n")
    except RecursionError:
        print(f"❌ _safe_str() 递归错误\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 70)
    print("visited.remove() 循环检测失效诊断")
    print("=" * 70)
    
    test_visited_remove_problem()
    test_visited_without_remove()
    test_real_scenario_simulation()
    
    print("\n" + "=" * 70)
    print("诊断完成")
    print("=" * 70)
