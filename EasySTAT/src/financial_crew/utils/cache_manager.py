import os
import functools
from joblib import Memory
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class CacheManager:
    """
    缓存管理器
    
    主要功能：
    1. 管理本地文件缓存路径
    2. 提供基于 joblib 的缓存装饰器
    3. 支持缓存过期时间控制（通过 clear_cache 机制或文件名管理，此处简化为持久化缓存）
    """
    
    def __init__(self):
        """
        初始化缓存管理器
        """
        # 统一使用绝对路径，防止 WebUI 模式下工作目录偏移
        env_path = os.getenv('AKSHARE_CACHE_PATH', './data/cache')
        self.cache_dir = os.path.abspath(env_path)
        
        self._ensure_cache_dir()
        self.memory = Memory(location=self.cache_dir, verbose=0)

    def _ensure_cache_dir(self):
        """
        确保缓存目录存在
        
        Returns:
            None
        """
        if not os.path.exists(self.cache_dir):
            try:
                os.makedirs(self.cache_dir)
                print(f"已创建缓存目录: {self.cache_dir}")
            except OSError as e:
                print(f"创建缓存目录失败: {e}")

    def cache(self):
        """
        获取缓存装饰器
        
        Returns:
            callable: joblib 的缓存装饰器
        """
        return self.memory.cache

# 全局单例
_cache_manager = CacheManager()

def get_cache_decorator():
    """
    获取全局缓存装饰器
    
    Returns:
        callable: 缓存装饰器
    """
    return _cache_manager.cache()
