"""
ArchTool 单元测试

主要功能：
    验证 ArchTool 能够正确从数据总线读取数据，并使用 GARCH 模型进行波动率建模。
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from financial_crew.tools.arch_tool import ArchTool
from financial_crew.tools.ohlcv_tool import OHLCVTool
from financial_crew.utils.data_bus import data_bus
import json
import pandas as pd


def test_arch_with_data_bus():
    """测试 ArchTool 从数据总线读取数据并建模"""
    print("\n" + "="*60)
    print("【测试 1】从数据总线读取数据并建模")
    print("="*60)
    
    # 首先确保有测试数据（如果 OHLCVTool 测试已运行）
    if not data_bus.exists("ohlcv_600519"):
        print("准备测试数据: 调用 OHLCVTool 获取 600519 数据...")
        ohlcv_tool = OHLCVTool()
        ohlcv_tool._run(stock_code="600519", start_date="20240101", end_date="20241231")
    
    # 使用数据引用调用 ArchTool
    ref_json = json.dumps({"data_ref": "ohlcv_600519"})
    
    tool = ArchTool()
    result = tool._run(data_ref_json=ref_json)
    
    print(f"结果: {result}")
    
    data = json.loads(result)
    
    if "error" in data:
        print(f"⚠️ 建模失败: {data['error']}")
        return False
    
    # 验证返回字段
    assert "conditional_volatility" in data, "缺少 conditional_volatility 字段"
    assert "omega" in data, "缺少 omega 字段"
    assert "alpha" in data, "缺少 alpha 字段"
    assert "beta" in data, "缺少 beta 字段"
    
    print(f"✅ 模型: {data.get('model')}")
    print(f"✅ 数据点数: {data.get('data_points')}")
    print(f"✅ 条件波动率: {data.get('conditional_volatility')}%")
    print(f"✅ Omega: {data.get('omega')}")
    print(f"✅ Alpha: {data.get('alpha')}")
    print(f"✅ Beta: {data.get('beta')}")
    print(f"✅ AIC: {data.get('aic')}")
    
    print("✅ 测试 1 通过")
    return True


def test_arch_invalid_ref():
    """测试无效数据引用的错误处理"""
    print("\n" + "="*60)
    print("【测试 2】无效数据引用的错误处理")
    print("="*60)
    
    tool = ArchTool()
    
    # 无效的引用
    ref_json = json.dumps({"data_ref": "nonexistent_data"})
    result = tool._run(data_ref_json=ref_json)
    
    data = json.loads(result)
    
    if "error" in data:
        print(f"✅ 正确捕获错误: {data['error']}")
        print("✅ 测试 2 通过")
        return True
    else:
        print("❌ 未正确处理无效引用")
        return False


def test_arch_missing_data_ref():
    """测试缺少 data_ref 字段的错误处理"""
    print("\n" + "="*60)
    print("【测试 3】缺少 data_ref 字段的错误处理")
    print("="*60)
    
    tool = ArchTool()
    
    # 缺少 data_ref 的输入
    invalid_json = json.dumps({"some_field": "value"})
    result = tool._run(data_ref_json=invalid_json)
    
    data = json.loads(result)
    
    if "error" in data and "无效" in data["error"]:
        print(f"✅ 正确捕获错误: {data['error']}")
        print("✅ 测试 3 通过")
        return True
    else:
        print(f"❌ 未正确处理: {data}")
        return False


if __name__ == "__main__":
    print("\n🚀 开始 ArchTool 单元测试\n")
    
    results = []
    
    try:
        results.append(("数据总线读取建模", test_arch_with_data_bus()))
        results.append(("无效数据引用", test_arch_invalid_ref()))
        results.append(("缺少 data_ref", test_arch_missing_data_ref()))
        
        print("\n" + "="*60)
        print("测试结果汇总")
        print("="*60)
        
        for name, passed in results:
            status = "✅ 通过" if passed else "❌ 失败"
            print(f"{name}: {status}")
        
        all_passed = all(r[1] for r in results)
        if all_passed:
            print("\n✅ 所有测试通过！")
        else:
            print("\n⚠️ 部分测试失败")
            
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
