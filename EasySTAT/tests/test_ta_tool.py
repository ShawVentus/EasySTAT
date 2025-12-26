"""
TATool 单元测试

主要功能：
    验证 TATool 能够正确从数据总线读取 OHLCV 数据并计算技术指标。
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from financial_crew.tools.ta_tool import TATool
from financial_crew.tools.ohlcv_tool import OHLCVTool
from financial_crew.utils.data_bus import data_bus
import json


def test_ta_with_data_bus():
    """测试 TATool 从数据总线读取数据并计算指标"""
    print("\n" + "="*60)
    print("【测试 1】从数据总线读取数据并计算技术指标")
    print("="*60)
    
    # 首先确保有测试数据
    if not data_bus.exists("ohlcv_600519"):
        print("准备测试数据: 调用 OHLCVTool 获取 600519 数据...")
        ohlcv_tool = OHLCVTool()
        ohlcv_tool._run(stock_code="600519", start_date="20240101", end_date="20241231")
    
    # 使用数据引用调用 TATool
    ref_json = json.dumps({"data_ref": "ohlcv_600519"})
    
    tool = TATool()
    result = tool._run(data_ref_json=ref_json)
    
    print(f"结果: {result}")
    
    data = json.loads(result)
    
    if "error" in data:
        print(f"⚠️ 计算失败: {data['error']}")
        return False
    
    # 验证返回字段
    assert "rsi" in data, "缺少 rsi 字段"
    assert "macd" in data, "缺少 macd 字段"
    assert "bollinger_hband" in data, "缺少 bollinger_hband 字段"
    assert "atr" in data, "缺少 atr 字段"
    
    print(f"✅ RSI: {data.get('rsi')}")
    print(f"✅ MACD: {data.get('macd')}")
    print(f"✅ MACD Signal: {data.get('macd_signal')}")
    print(f"✅ MACD Diff: {data.get('macd_diff')}")
    print(f"✅ 布林带上轨: {data.get('bollinger_hband')}")
    print(f"✅ 布林带中轨: {data.get('bollinger_mband')}")
    print(f"✅ 布林带下轨: {data.get('bollinger_lband')}")
    print(f"✅ ATR: {data.get('atr')}")
    
    print("✅ 测试 1 通过")
    return True


def test_ta_invalid_ref():
    """测试无效数据引用的错误处理"""
    print("\n" + "="*60)
    print("【测试 2】无效数据引用的错误处理")
    print("="*60)
    
    tool = TATool()
    
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


def test_ta_missing_data_ref():
    """测试缺少 data_ref 字段的错误处理"""
    print("\n" + "="*60)
    print("【测试 3】缺少 data_ref 字段的错误处理")
    print("="*60)
    
    tool = TATool()
    
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


def test_ta_batch_references():
    """测试处理批量数据引用"""
    print("\n" + "="*60)
    print("【测试 4】处理批量数据引用（取第一个）")
    print("="*60)
    
    # 确保有测试数据
    if not data_bus.exists("ohlcv_000001"):
        print("准备测试数据: 调用 OHLCVTool 获取 000001 数据...")
        ohlcv_tool = OHLCVTool()
        ohlcv_tool._run(stock_code="000001", start_date="20240101", end_date="20241231")
    
    tool = TATool()
    
    # 模拟批量引用格式
    batch_ref_json = json.dumps({
        "references": [
            {"data_ref": "ohlcv_600519"},
            {"data_ref": "ohlcv_000001"}
        ]
    })
    result = tool._run(data_ref_json=batch_ref_json)
    
    data = json.loads(result)
    
    if "error" in data:
        print(f"⚠️ 计算失败: {data['error']}")
        return False
    
    print(f"✅ 成功处理批量引用，使用第一个: {data.get('data_ref')}")
    print("✅ 测试 4 通过")
    return True


if __name__ == "__main__":
    print("\n🚀 开始 TATool 单元测试\n")
    
    results = []
    
    try:
        results.append(("数据总线读取计算", test_ta_with_data_bus()))
        results.append(("无效数据引用", test_ta_invalid_ref()))
        results.append(("缺少 data_ref", test_ta_missing_data_ref()))
        results.append(("批量数据引用", test_ta_batch_references()))
        
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
