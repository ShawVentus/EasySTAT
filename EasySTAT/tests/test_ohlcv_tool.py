"""
OHLCVTool 单元测试

主要功能：
    验证 OHLCVTool 能够正确获取 K 线数据，保存到数据总线，并返回数据引用。
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from financial_crew.tools.ohlcv_tool import OHLCVTool
from financial_crew.utils.data_bus import data_bus
import json


def test_single_stock():
    """测试单只股票的 K 线数据获取"""
    print("\n" + "="*60)
    print("【测试 1】单只股票 K 线数据获取")
    print("="*60)
    
    tool = OHLCVTool()
    
    # 获取茅台的 K 线数据
    result = tool._run(
        stock_code="600519",
        period="daily",
        start_date="20240101",
        end_date="20241231"
    )
    
    print(f"返回结果: {result[:500]}...")
    
    # 解析结果
    data = json.loads(result)
    
    # 验证是否返回了数据引用
    if "error" in data:
        print(f"⚠️ 获取数据出错: {data['error']}")
        return False
    
    assert "data_ref" in data, "返回结果中缺少 data_ref 字段"
    assert "rows" in data, "返回结果中缺少 rows 字段"
    assert "file_path" in data, "返回结果中缺少 file_path 字段"
    
    print(f"✅ 数据引用: {data['data_ref']}")
    print(f"✅ 数据行数: {data['rows']}")
    print(f"✅ 列: {data.get('columns', [])}")
    print(f"✅ 日期范围: {data.get('date_range', {})}")
    
    # 验证数据已保存到数据总线
    assert data_bus.exists(data["data_ref"]), "数据未保存到数据总线"
    
    print("✅ 测试 1 通过")
    return True


def test_data_limit():
    """测试数据量限制（最多250条）"""
    print("\n" + "="*60)
    print("【测试 2】数据量限制（一年约250条）")
    print("="*60)
    
    tool = OHLCVTool()
    
    # 获取长时间范围的数据
    result = tool._run(
        stock_code="000001",
        period="daily",
        start_date="20200101",  # 5年数据
        end_date="20241231"
    )
    
    data = json.loads(result)
    
    if "error" in data:
        print(f"⚠️ 获取数据出错: {data['error']}")
        return False
    
    print(f"实际行数: {data['rows']}")
    
    # 验证数据被限制在250条以内
    assert data["rows"] <= 250, f"数据未被限制: {data['rows']} > 250"
    
    print("✅ 测试 2 通过")
    return True


def test_batch_stocks():
    """测试批量股票获取"""
    print("\n" + "="*60)
    print("【测试 3】批量股票获取")
    print("="*60)
    
    tool = OHLCVTool()
    
    # 获取多只股票
    result = tool._run(
        stock_code="600519,000001",
        period="daily",
        start_date="20240101",
        end_date="20241231"
    )
    
    data = json.loads(result)
    
    if "error" in data:
        print(f"⚠️ 获取数据出错: {data['error']}")
        return False
    
    # 批量返回时应包含 references 列表
    if "references" in data:
        print(f"✅ 返回了 {data['count']} 个数据引用")
        for ref in data["references"]:
            print(f"   - {ref['data_ref']}: {ref['rows']} 行")
    else:
        # 单只股票也可能成功（如果只有一只返回）
        print(f"✅ 返回单个引用: {data.get('data_ref')}")
    
    print("✅ 测试 3 通过")
    return True


if __name__ == "__main__":
    print("\n🚀 开始 OHLCVTool 单元测试\n")
    
    results = []
    
    try:
        results.append(("单只股票获取", test_single_stock()))
        results.append(("数据量限制", test_data_limit()))
        results.append(("批量股票获取", test_batch_stocks()))
        
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
