"""
EasySTAT Phase 6 - 后端稳定性与中断机制验证脚本

测试目标：
1. 验证 _safe_str 能否处理循环引用，避免 RecursionError。
2. 验证 _safe_str 对 Agent/Task 等复杂对象的安全提取。
3. 验证协作式中断信号 (CrewStopException) 的抛出逻辑。

使用说明：
python tests/05.22_1030_Phase6_Backend_Test/test_backend.py
"""

import sys
import os
import threading
import asyncio

# 将后端服务路径加入系统路径
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from services.event_listener import EasyStatEventListener
from services.executor import CrewStopException

def test_safe_str():
    """
    测试 _safe_str 的健壮性
    """
    print(">>> [测试] 开始验证 _safe_str 健壮性...")
    
    # 模拟异步队列和循环
    queue = asyncio.Queue()
    queue._my_loop = asyncio.get_event_loop()
    listener = EasyStatEventListener(queue)
    
    # 1. 测试循环引用
    a = {}
    b = {"a": a}
    a["b"] = b
    result = listener._safe_str(a)
    print(f"   [1] 循环引用处理结果: {result}")
    assert "..." in result or "object at" in result
    
    # 2. 测试模拟 Agent 对象
    class MockAgent:
        def __init__(self, role):
            self.role = role
    agent = MockAgent("数据分析师")
    result = listener._safe_str(agent)
    print(f"   [2] Agent 对象处理结果: {result}")
    assert "Agent(role=数据分析师)" in result
    
    # 3. 测试模拟 Task 对象
    class MockTask:
        def __init__(self, description):
            self.description = description
    task = MockTask("执行茅台股票深度分析")
    result = listener._safe_str(task)
    print(f"   [3] Task 对象处理结果: {result}")
    assert "执行茅台股票深度分析" in result
    
    # 4. 测试 3.13 潜在的 Cell 冲突对象
    class ComplexObj:
        def __init__(self):
            def inner(): return self
            # 模拟 Python 内部的 cell 对象
            self.data = inner.__closure__[0]
    
    comp = ComplexObj()
    result = listener._safe_str(comp)
    print(f"   [4] 复杂 Cell 对象处理结果: {result}")
    assert "object at" in result
    
    print(">>> [成功] _safe_str 健壮性验证通过。\n")

def test_interruption_logic():
    """
    测试协作式中断逻辑
    """
    print(">>> [测试] 开始验证协作式中断逻辑...")
    
    queue = asyncio.Queue()
    queue._my_loop = asyncio.get_event_loop()
    stop_event = threading.Event()
    listener = EasyStatEventListener(queue, stop_event)
    
    # 1. 正常状态检查
    try:
        listener._check_interruption()
        print("   [1] 正常状态检查: 未抛出异常 (符合预期)")
    except CrewStopException:
        print("   [1] 正常状态检查: 错误抛出了异常")
        assert False
        
    # 2. 触发停止信号后检查
    stop_event.set()
    try:
        listener._check_interruption()
        print("   [2] 停止信号检查: 未抛出异常 (失败)")
        assert False
    except CrewStopException:
        print("   [2] 停止信号检查: 成功抛出 CrewStopException (符合预期)")
    
    print(">>> [成功] 协作式中断逻辑验证通过。")

if __name__ == "__main__":
    # 创建结果目录（如果不存在）
    os.makedirs(os.path.join(os.path.dirname(__file__), "result"), exist_ok=True)
    
    try:
        test_safe_str()
        test_interruption_logic()
        
        # 将测试成功信息写入结果文件
        with open(os.path.join(os.path.dirname(__file__), "result/success.txt"), "w") as f:
            f.write("Phase 6 Backend Logic Test Passed Successfully.")
            
    except Exception as e:
        print(f"\n>>> [失败] 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
