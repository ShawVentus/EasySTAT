"""
Phase 5 修复验证脚本

主要功能：
- 验证 TATool 是否支持 dict 类型输入
- 验证 OHLCVTool 是否能正确区分历史数据和最新数据的 Key
- 验证 DataBus 的保存与加载功能
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path

# 设置项目路径
PROJECT_ROOT = "/Users/mac/dev/personal/br_competition"
sys.path.insert(0, os.path.join(PROJECT_ROOT, "EasySTAT/src"))

from financial_crew.tools.ta_tool import TATool
from financial_crew.tools.ohlcv_tool import OHLCVTool
from financial_crew.utils.data_bus import data_bus

def test_ta_tool_compatibility():
    """
    测试 TATool 的参数兼容性
    
    验证 TATool 是否能同时接受 JSON 字符串和 Python 字典作为输入。
    """
    print("\n--- 开始测试 TATool 兼容性 ---")
    tool = TATool()
    
    # 模拟一个已存在的数据 Key
    test_key = "test_data_600519"
    df = pd.DataFrame({
        "Date": ["2023-01-01", "2023-01-02"],
        "Open": [100, 101],
        "Close": [102, 103],
        "High": [104, 105],
        "Low": [99, 100],
        "Volume": [1000, 1100]
    })
    data_bus.save(test_key, df)
    
    # 1. 测试字典输入
    print("[测试] 传入字典对象...")
    input_dict = {"data_ref": test_key}
    try:
        result = tool._run(data_ref_json=input_dict)
        print(f"[结果] 成功! 输出长度: {len(result)}")
    except Exception as e:
        print(f"[失败] 字典输入报错: {e}")

    # 2. 测试字符串输入
    print("[测试] 传入 JSON 字符串...")
    input_str = json.dumps({"data_ref": test_key})
    try:
        result = tool._run(data_ref_json=input_str)
        print(f"[结果] 成功! 输出长度: {len(result)}")
    except Exception as e:
        print(f"[失败] 字符串输入报错: {e}")

def test_ohlcv_key_isolation():
    """
    测试 OHLCVTool 的 Key 隔离逻辑
    
    验证获取多条数据时使用 'ohlcv_hist_' 前缀，获取单条数据时使用 'ohlcv_latest_' 前缀。
    """
    print("\n--- 开始测试 OHLCVTool Key 隔离 ---")
    tool = OHLCVTool()
    
    # 1. 模拟获取历史数据（多条）
    print("[测试] 获取历史数据 (20230101-20230110)...")
    res_hist = tool._run(stock_code="600519", start_date="20230101", end_date="20230110")
    ref_hist = json.loads(res_hist)
    print(f"[结果] 生成的 Key: {ref_hist.get('data_ref')}")
    
    # 2. 模拟获取最新价（单条）
    print("[测试] 获取最新单日数据 (20231229-20231229)...")
    res_latest = tool._run(stock_code="600519", start_date="20231229", end_date="20231229")
    ref_latest = json.loads(res_latest)
    print(f"[结果] 生成的 Key: {ref_latest.get('data_ref')}")
    
    # 验证 Key 是否不同
    if ref_hist.get('data_ref') != ref_latest.get('data_ref'):
        print("[成功] Key 已成功隔离，不会发生覆盖。")
    else:
        print("[失败] Key 仍然相同，存在覆盖风险。")

if __name__ == "__main__":
    # 确保在 conda br 环境下运行
    print(f"当前 Python 路径: {sys.executable}")
    
    try:
        test_ta_tool_compatibility()
        test_ohlcv_key_isolation()
        print("\n=== 所有修复验证完成 ===")
    except Exception as e:
        print(f"\n验证过程中发生错误: {e}")
