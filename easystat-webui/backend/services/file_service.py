"""
EasySTAT 文件管理服务

主要功能：
- 管理 result/ 和 logs/ 目录下的文件
- 提供文件列表获取、内容读取及安全检查功能
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from core.config import settings

class FileService:
    """
    文件管理服务类
    
    负责处理与生成文件（报告、日志、数据）相关的 IO 操作。
    """
    
    def __init__(self):
        """
        初始化文件服务
        
        设置结果目录和日志目录的路径。
        """
        self.project_path = Path(settings.EASYSTAT_PROJECT_PATH)
        self.result_dir = self.project_path / "result"
        self.logs_dir = self.project_path / "logs"
        
        # 动态获取数据总线路径，支持相对路径和环境变量
        data_bus_config = os.getenv("DATA_BUS_PATH", "./data/shared")
        if os.path.isabs(data_bus_config):
            self.shared_data_dir = Path(data_bus_config)
        else:
            self.shared_data_dir = self.project_path / data_bus_config
        
        # 记录路径映射
        print(f"[FileService] 初始化完成")
        print(f"  - 项目根目录: {self.project_path}")
        print(f"  - 结果目录: {self.result_dir}")
        print(f"  - 日志目录: {self.logs_dir}")
        print(f"  - 数据总线(Shared): {self.shared_data_dir}")
        
        # 确保目录存在
        for d in [self.result_dir, self.logs_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def list_files(self) -> List[Dict[str, Any]]:
        """
        列出所有可管理的文件
        
        扫描结果目录、日志目录和共享数据目录，返回文件元数据列表。
        
        Returns:
            List[Dict]: 包含文件名、类型、大小、修改时间等信息的字典列表
        """
        files = []
        
        # 扫描目录配置
        scan_configs = [
            {"dir": self.result_dir, "type": "result", "label": "分析结果"},
            {"dir": self.logs_dir, "type": "log", "label": "执行日志"},
            {"dir": self.shared_data_dir, "type": "data", "label": "中间数据"}
        ]
        
        for config in scan_configs:
            target_dir = config["dir"]
            if not target_dir.exists():
                continue
                
            for item in target_dir.iterdir():
                if item.is_file() and not item.name.startswith('.'):
                    stat = item.stat()
                    files.append({
                        "name": item.name,
                        "path": str(item.relative_to(self.project_path)),
                        "type": config["type"],
                        "category": config["label"],
                        "size": stat.st_size,
                        "mtime": stat.st_mtime,
                        "extension": item.suffix.lower()
                    })
        
        # 按修改时间倒序排列
        files.sort(key=lambda x: x["mtime"], reverse=True)
        return files

    def get_file_content(self, relative_path: str) -> Optional[str]:
        """
        读取文件内容
        
        Args:
            relative_path (str): 相对于项目根目录的文件路径
            
        Returns:
            Optional[str]: 文件内容字符串，若文件不存在或读取失败则返回 None
        """
        full_path = self.project_path / relative_path
        
        # 安全检查：防止路径穿越攻击
        if not self._is_safe_path(full_path):
            print(f"[FileService] 拒绝访问不安全路径: {full_path}")
            return None
            
        if not full_path.exists():
            return None
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"[FileService] 读取文件失败: {e}")
            return None

    def _is_safe_path(self, path: Path) -> bool:
        """
        检查路径是否安全（是否在允许的目录内）
        
        Args:
            path (Path): 要检查的绝对路径
            
        Returns:
            bool: 安全返回 True，否则返回 False
        """
        try:
            resolved_path = path.resolve()
            # 必须在项目根目录下
            return str(resolved_path).startswith(str(self.project_path.resolve()))
        except Exception:
            return False

    def delete_file(self, relative_path: str) -> bool:
        """
        删除指定文件
        
        Args:
            relative_path (str): 相对于项目根目录的文件路径
            
        Returns:
            bool: 删除成功返回 True，否则返回 False
        """
        full_path = self.project_path / relative_path
        if not self._is_safe_path(full_path) or not full_path.exists():
            return False
            
        try:
            full_path.unlink()
            return True
        except Exception as e:
            print(f"[FileService] 删除文件失败: {e}")
            return False

# 全局单例
file_service = FileService()
