"""
数据总线模块 (Data Bus)

主要功能：
    管理多智能体工具之间的大数据共享。
    将 DataFrame 数据保存到本地 JSON 文件，并生成轻量级数据引用。
    下游工具通过数据引用读取完整数据，避免 JSON 在 LLM 上下文中被截断。

使用方法：
    from financial_crew.utils.data_bus import data_bus
    
    # 保存数据
    ref = data_bus.save("ohlcv_600519", df)
    
    # 读取数据
    df = data_bus.load("ohlcv_600519")
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class DataBus:
    """
    数据总线类
    
    负责管理工具间的大数据共享，通过文件系统实现持久化存储。
    
    Attributes:
        storage_dir: 数据存储目录路径
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        初始化数据总线
        
        Args:
            storage_dir: 存储目录路径，默认从环境变量 DATA_BUS_PATH 读取，
                        若未配置则使用 ./data/shared
        """
        # 1. 显式加载环境变量
        # 首先尝试加载当前目录下或默认搜索路径的 .env
        load_dotenv()
        
        # 针对 EasySTAT 可能作为子项目运行的情况，尝试向上查找并加载根目录 .env
        # 找到 src 目录的父目录即为项目根目录
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent # data_bus.py 在 src/financial_crew/utils/
        env_path = project_root / '.env'
        if env_path.exists():
            load_dotenv(env_path, override=True)
            # print(f"[DataBus] 已从项目根目录加载环境配置: {env_path}")
        
        # 2. 优先使用参数，其次环境变量，最后使用默认值
        if storage_dir:
            self.storage_dir = Path(storage_dir).absolute()
        else:
            env_path = os.getenv('DATA_BUS_PATH', './data/shared')
            self.storage_dir = Path(env_path).absolute()
        
        # 确保存储目录存在
        self._ensure_storage_dir()
        
        # Registry（注册表）：记录 {category: data_key} 映射
        # 用途：让下游工具可以通过 category 自动获取上游数据的 key，无需依赖 LLM 传递
        self._registry: Dict[str, str] = {}
        
        print(f"[DataBus] 初始化完成，存储目录: {self.storage_dir}")
    
    def _ensure_storage_dir(self) -> None:
        """确保存储目录存在"""
        if not self.storage_dir.exists():
            try:
                self.storage_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                print(f"[DataBus] 创建存储目录失败: {e}")
                raise
    
    def _get_file_path(self, key: str) -> Path:
        """根据 key 生成文件路径"""
        safe_key = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in key)
        return self.storage_dir / f"{safe_key}.json"
    
    def save(self, key: str, data: Union[pd.DataFrame, Dict, List], category: Optional[str] = None) -> Dict[str, Any]:
        """
        保存数据到文件（原子写入），并返回数据引用
        
        主要功能：
            将 DataFrame、Dict 或 List 数据保存为 JSON 文件。
            如果指定了 category，会同时注册到 Registry，供下游工具自动获取。
        
        Args:
            key: 数据唯一标识符，也是文件名（不含扩展名）
            data: 要保存的数据，支持 DataFrame、Dict、List 类型
            category: 可选，数据类别名称（如 "ohlcv"、"capital_flow"），
                     指定后会注册到 Registry
        
        Returns:
            包含 data_ref、file_path 等信息的字典
        """
        file_path = self._get_file_path(key)
        temp_path = file_path.with_suffix('.tmp')
        
        try:
            # 判断数据类型并处理
            if isinstance(data, pd.DataFrame):
                # DataFrame 处理逻辑
                df_copy = data.copy()
                for col in df_copy.columns:
                    if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
                        df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d')
                records = df_copy.to_dict(orient='records')
                data_info = {
                    "type": "DataFrame",
                    "rows": len(data),
                    "columns": list(data.columns),
                    "date_range": self._extract_date_range(data)
                }
            elif isinstance(data, (dict, list)):
                # Dict/List 直接作为记录
                records = data
                data_info = {
                    "type": type(data).__name__,
                    "structure": "hybrid" if isinstance(data, dict) and "target_stock" in data else "simple"
                }
            else:
                raise ValueError(f"不支持的数据类型: {type(data)}")

            # 1. 先写入临时文件
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2, default=str)
            
            # 2. 原子重命名
            os.replace(temp_path, file_path)
            
            # 构建数据引用
            ref = {
                "data_ref": key,
                "file_path": str(file_path.absolute()),
                "saved_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                **data_info
            }
            
            print(f"[DataBus] 已安全保存数据: {key}, 类型: {data_info['type']}")
            
            # 注册到 Registry（如果指定了 category）
            if category:
                self._registry[category] = key
                print(f"[DataBus] Registry 注册: {category} -> {key}")
            
            return ref
            
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            print(f"[DataBus] 保存数据失败: {e}")
            raise
    
    def _extract_date_range(self, df: pd.DataFrame) -> Optional[Dict[str, str]]:
        """
        从 DataFrame 中提取日期范围
        
        Args:
            df: pandas DataFrame
        
        Returns:
            dict: 包含 start 和 end 的字典，若无日期列则返回 None
        """
        # 尝试查找日期列
        date_col = None
        for col in ['Date', 'date', '日期', 'datetime']:
            if col in df.columns:
                date_col = col
                break
        
        if date_col is None or df.empty:
            return None
        
        try:
            dates = pd.to_datetime(df[date_col])
            return {
                "start": dates.min().strftime('%Y-%m-%d'),
                "end": dates.max().strftime('%Y-%m-%d')
            }
        except Exception:
            return None
    
    def load(self, key: str) -> pd.DataFrame:
        """
        根据 key 读取数据文件并返回 DataFrame
        
        Args:
            key: 数据标识符
        
        Returns:
            pd.DataFrame: 读取的数据
        
        Raises:
            FileNotFoundError: 当数据文件不存在时抛出
        """
        file_path = self._get_file_path(key)
        
        if not file_path.exists():
            error_msg = f"数据文件不存在: {key} (路径: {file_path})"
            print(f"[DataBus] 错误: {error_msg}")
            raise FileNotFoundError(error_msg)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            records = json.load(f)
        
        df = pd.DataFrame(records)
        print(f"[DataBus] 已加载数据: {key}, 行数: {len(df)}")
        
        return df
    
    def exists(self, key: str) -> bool:
        """
        检查指定 key 的数据是否存在
        
        Args:
            key: 数据标识符
        
        Returns:
            bool: 存在返回 True，否则返回 False
        """
        file_path = self._get_file_path(key)
        return file_path.exists()
    
    def delete(self, key: str) -> bool:
        """
        删除指定 key 的数据文件
        
        Args:
            key: 数据标识符
        
        Returns:
            bool: 删除成功返回 True，文件不存在返回 False
        """
        file_path = self._get_file_path(key)
        
        if file_path.exists():
            file_path.unlink()
            print(f"[DataBus] 已删除数据: {key}")
            return True
        
        return False
    
    def list_keys(self) -> List[str]:
        """
        列出所有已保存的数据 key
        
        Args:
            无
        
        Returns:
            List[str]: key 列表
        """
        keys = []
        for file_path in self.storage_dir.glob("*.json"):
            keys.append(file_path.stem)
        return keys
    
    def get_latest(self, category: str) -> Optional[str]:
        """
        从 Registry 获取指定类别的最新数据 key
        
        主要功能：
            下游工具通过 category 获取上游工具保存的数据 key，
            无需依赖 LLM 传递 data_ref 参数。
        
        Args:
            category: 数据类别名称，如 "ohlcv"（K线）、"capital_flow"（资金流）
        
        Returns:
            对应的 data_key 字符串，如 "ohlcv_hist_600519"；
            如果 category 未注册，返回 None
        """
        key = self._registry.get(category)
        if key:
            print(f"[DataBus] Registry 查询成功: {category} -> {key}")
        else:
            print(f"[DataBus] Registry 未找到类别: {category}")
        return key


# 全局单例实例
# 使用单例模式确保整个应用使用同一个 DataBus 实例
_data_bus_instance: Optional[DataBus] = None


def get_data_bus() -> DataBus:
    """
    获取全局 DataBus 实例（单例模式）
    
    Args:
        无
    
    Returns:
        DataBus: 全局数据总线实例
    """
    global _data_bus_instance
    if _data_bus_instance is None:
        _data_bus_instance = DataBus()
    return _data_bus_instance


# 便捷访问的全局实例
data_bus = get_data_bus()
