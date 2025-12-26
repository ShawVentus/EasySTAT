"""
DataBus Registry 功能测试

主要功能：
    验证 DataBus 的 Registry 功能是否正常工作。
    包括：save 时的 category 注册、get_latest 的正确返回。

测试场景：
    1. 保存数据并注册到 Registry
    2. 从 Registry 获取已注册的 data_key
    3. 获取未注册的 category 应返回 None
    4. 覆盖策略验证（后写入覆盖先写入）
"""

import sys
import os
import pandas as pd
import pytest

# 添加项目路径
sys.path.insert(0, '/Users/mac/dev/personal/br_competition/EasySTAT/src')

from financial_crew.utils.data_bus import DataBus


class TestDataBusRegistry:
    """DataBus Registry 功能测试类"""
    
    @pytest.fixture
    def temp_data_bus(self, tmp_path):
        """
        创建临时 DataBus 实例
        
        Args:
            tmp_path: pytest 提供的临时目录
            
        Returns:
            DataBus: 使用临时目录的 DataBus 实例
        """
        return DataBus(storage_dir=str(tmp_path))
    
    def test_save_with_category_registers_to_registry(self, temp_data_bus):
        """
        测试场景1：保存数据并注册到 Registry
        
        预期行为：
            调用 save(key, data, category="ohlcv") 后，
            Registry 中应包含 {"ohlcv": key} 的映射。
        """
        # 准备测试数据
        df = pd.DataFrame({"Close": [100.0, 101.0, 102.0]})
        data_key = "ohlcv_hist_600519"
        
        # 执行保存（带 category）
        ref = temp_data_bus.save(data_key, df, category="ohlcv")
        
        # 验证返回值
        assert ref["data_ref"] == data_key
        
        # 验证 Registry 已注册
        assert temp_data_bus._registry.get("ohlcv") == data_key
    
    def test_get_latest_returns_registered_key(self, temp_data_bus):
        """
        测试场景2：从 Registry 获取已注册的 data_key
        
        预期行为：
            get_latest("ohlcv") 应返回之前注册的 data_key。
        """
        # 准备并保存数据
        df = pd.DataFrame({"Close": [100.0]})
        data_key = "ohlcv_hist_600519"
        temp_data_bus.save(data_key, df, category="ohlcv")
        
        # 调用 get_latest
        result = temp_data_bus.get_latest("ohlcv")
        
        # 验证
        assert result == data_key
    
    def test_get_latest_returns_none_for_unregistered_category(self, temp_data_bus):
        """
        测试场景3：获取未注册的 category 应返回 None
        
        预期行为：
            get_latest("unknown_category") 应返回 None。
        """
        result = temp_data_bus.get_latest("unknown_category")
        assert result is None
    
    def test_registry_overwrite_strategy(self, temp_data_bus):
        """
        测试场景4：覆盖策略验证
        
        预期行为：
            同一 category 多次注册时，后写入的覆盖先写入的。
        """
        # 第一次保存
        df1 = pd.DataFrame({"Close": [100.0]})
        temp_data_bus.save("ohlcv_hist_600519", df1, category="ohlcv")
        
        # 第二次保存（不同的 key）
        df2 = pd.DataFrame({"Close": [200.0]})
        temp_data_bus.save("ohlcv_hist_000001", df2, category="ohlcv")
        
        # 验证：应返回最新的 key
        result = temp_data_bus.get_latest("ohlcv")
        assert result == "ohlcv_hist_000001"
    
    def test_save_without_category_does_not_register(self, temp_data_bus):
        """
        测试场景5：不指定 category 时不应注册
        
        预期行为：
            调用 save(key, data) 不传 category，Registry 应保持为空。
        """
        # 保存数据（不指定 category）
        df = pd.DataFrame({"Close": [100.0]})
        temp_data_bus.save("some_key", df)
        
        # 验证 Registry 为空
        assert len(temp_data_bus._registry) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
