"""
数据总线单元测试

主要功能：
    验证 DataBus 的 save/load/exists/delete 功能是否正常工作。
"""

import sys
import os
import tempfile
import shutil

# 添加 src 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import pandas as pd
import json

from financial_crew.utils.data_bus import DataBus


def test_save_and_load():
    """测试数据保存和加载"""
    print("\n" + "="*60)
    print("【测试 1】数据保存和加载")
    print("="*60)
    
    # 使用临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        bus = DataBus(storage_dir=temp_dir)
        
        # 创建测试数据
        test_df = pd.DataFrame({
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "Open": [100.0, 101.0, 102.0],
            "High": [105.0, 106.0, 107.0],
            "Low": [99.0, 100.0, 101.0],
            "Close": [104.0, 105.0, 106.0],
            "Volume": [1000, 1100, 1200]
        })
        
        # 保存数据
        ref = bus.save("test_ohlcv_600519", test_df)
        
        print(f"保存返回的引用: {json.dumps(ref, ensure_ascii=False, indent=2)}")
        
        # 验证引用格式
        assert "data_ref" in ref, "引用中缺少 data_ref 字段"
        assert "file_path" in ref, "引用中缺少 file_path 字段"
        assert "rows" in ref, "引用中缺少 rows 字段"
        assert ref["rows"] == 3, f"行数不正确: 期望 3，实际 {ref['rows']}"
        
        # 加载数据
        loaded_df = bus.load("test_ohlcv_600519")
        
        print(f"加载的数据:\n{loaded_df}")
        
        # 验证数据内容
        assert len(loaded_df) == 3, f"加载的行数不正确: {len(loaded_df)}"
        assert list(loaded_df.columns) == ["Date", "Open", "High", "Low", "Close", "Volume"]
        
        print("✅ 测试 1 通过")


def test_exists_and_delete():
    """测试数据存在检查和删除"""
    print("\n" + "="*60)
    print("【测试 2】数据存在检查和删除")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        bus = DataBus(storage_dir=temp_dir)
        
        # 创建测试数据
        test_df = pd.DataFrame({"value": [1, 2, 3]})
        
        # 保存前检查
        assert not bus.exists("test_key"), "保存前不应存在"
        
        # 保存
        bus.save("test_key", test_df)
        
        # 保存后检查
        assert bus.exists("test_key"), "保存后应存在"
        
        # 删除
        result = bus.delete("test_key")
        assert result, "删除应返回 True"
        
        # 删除后检查
        assert not bus.exists("test_key"), "删除后不应存在"
        
        # 再次删除
        result = bus.delete("test_key")
        assert not result, "再次删除应返回 False"
        
        print("✅ 测试 2 通过")


def test_list_keys():
    """测试列出所有数据键"""
    print("\n" + "="*60)
    print("【测试 3】列出所有数据键")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        bus = DataBus(storage_dir=temp_dir)
        
        # 保存多个数据
        for i in range(3):
            bus.save(f"stock_{i}", pd.DataFrame({"value": [i]}))
        
        # 列出所有键
        keys = bus.list_keys()
        print(f"所有键: {keys}")
        
        assert len(keys) == 3, f"键数量不正确: {len(keys)}"
        assert set(keys) == {"stock_0", "stock_1", "stock_2"}
        
        print("✅ 测试 3 通过")


def test_date_range_extraction():
    """测试日期范围提取"""
    print("\n" + "="*60)
    print("【测试 4】日期范围提取")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        bus = DataBus(storage_dir=temp_dir)
        
        # 创建包含日期的数据
        test_df = pd.DataFrame({
            "Date": ["2024-01-15", "2024-03-20", "2024-06-30"],
            "Close": [100, 110, 120]
        })
        
        ref = bus.save("date_test", test_df)
        
        print(f"日期范围: {ref.get('date_range')}")
        
        assert ref["date_range"]["start"] == "2024-01-15"
        assert ref["date_range"]["end"] == "2024-06-30"
        
        print("✅ 测试 4 通过")


if __name__ == "__main__":
    print("\n🚀 开始数据总线单元测试\n")
    
    try:
        test_save_and_load()
        test_exists_and_delete()
        test_list_keys()
        test_date_range_extraction()
        
        print("\n" + "="*60)
        print("✅ 所有测试通过！")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
