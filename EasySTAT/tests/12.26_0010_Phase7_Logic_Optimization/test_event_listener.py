"""
事件监听器循环引用修复测试 (Cycle Detection Test)

主要功能：
    验证 event_listener.py 中的 _safe_str 方法是否实现了循环检测机制。
    确保 A -> B -> A 等死循环场景能被优雅处理并保留信息，而不抛出 RecursionError。
"""

import unittest
from unittest.mock import MagicMock
import sys
import os

# 修正导入路径：添加到 easystat-webui/backend 目录
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../easystat-webui/backend"))
if backend_path not in sys.path:
    sys.path.append(backend_path)

from services.event_listener import EasyStatEventListener

# 模拟 Agent 类
class MockAgent:
    def __init__(self, role, desc=None):
        self.role = role
        self.description = desc
    
    def __repr__(self):
        return f"MockAgent(role={self.role})"

class TestEventListenerCycleDetection(unittest.TestCase):
    
    def setUp(self):
        self.mock_queue = MagicMock()
        self.listener = EasyStatEventListener(self.mock_queue)
        
    def test_safe_str_circular_reference(self):
        """测试循环引用的情况"""
        # 1. 简单字典自引用
        circular_dict = {"name": "loop"}
        circular_dict["self"] = circular_dict
        
        result = self.listener._safe_str(circular_dict)
        print(f"字典自引用测试结果: {result}")
        
        # 验证是否检测到了循环引用并切断
        self.assertIn("CircularReference", result)
        self.assertIn("dict", result) # 应该保留类型信息
        self.assertNotIn("RecursionError", result)

    def test_safe_str_agent_complex(self):
        """测试 Agent 对象的复杂属性提取与潜在循环"""
        agent = MockAgent(role="超级分析师", desc="非常厉害")
        agent.goal = "赚一个亿"
        
        # 制造该 Agent 的循环引用
        agent.self_ref = agent
        
        result = self.listener._safe_str(agent)
        print(f"Agent循环测试结果: {result}")
        
        # 验证非循环部分是否保留
        self.assertIn("超级分析师", result)
        self.assertIn("赚一个亿", result)
        # 验证循环部分是否被切断 (str(agent) 会调用 repr)
        # 注意：我们的 impl 中兜底是 str(item)，如果 item 自身 repr 没有死循环抗性，那一层会挂
        # 但 MockAgent repr 很简单。
        # 关键是 _recursive_convert 内部逻辑是否能处理
        
    def test_mutual_recursion(self):
        """测试 A <-> B 相互引用"""
        a = {"name": "A"}
        b = {"name": "B"}
        a["link"] = b
        b["link"] = a
        
        result = self.listener._safe_str(a)
        print(f"相互引用测试结果: {result}")
        
        self.assertIn("A", result)
        self.assertIn("B", result)
        self.assertIn("CircularReference", result)

if __name__ == "__main__":
    unittest.main()
