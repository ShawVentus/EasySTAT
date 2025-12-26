"""
本地文件存储模块

功能说明：
    提供本地文件夹存储功能，作为 MinIO 对象存储的轻量级替代。
    适用于本地开发和小规模部署场景。

主要类：
    - LocalStorage: 本地存储类，提供与 MinioStorage 兼容的接口
    - LocalStorageClient: 模拟 MinIO client 的删除操作

环境变量：
    - LOCAL_STORAGE_DIR: 本地存储目录路径，默认为 ./data/reports

作者：Financial_Program
日期：2024-12
"""

import os
import shutil
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ========================================
# 本地存储配置常量
# ========================================
LOCAL_STORAGE_DIR = os.getenv("LOCAL_STORAGE_DIR", "./data/reports")


class LocalStorageClient:
    """
    模拟 MinIO Client 的本地存储客户端
    
    功能说明：
        提供与 MinIO client 兼容的 remove_object 方法，
        用于删除本地存储的文件。
    """
    
    def __init__(self, base_dir):
        """
        初始化本地存储客户端
        
        Args:
            base_dir: 存储根目录路径
        """
        self.base_dir = base_dir
    
    def remove_object(self, bucket, object_name):
        """
        删除指定的文件对象
        
        Args:
            bucket: 存储桶名称（本地存储中忽略此参数）
            object_name: 要删除的文件名
            
        Returns:
            None
            
        Raises:
            FileNotFoundError: 如果文件不存在
        """
        file_path = os.path.join(self.base_dir, object_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"[LocalStorage] 已删除文件: {object_name}")
        else:
            raise FileNotFoundError(f"文件不存在: {object_name}")


class LocalStorage:
    """
    本地文件存储类
    
    功能说明：
        提供与 MinioStorage 兼容的接口，将文件存储到本地目录。
        适用于本地开发环境，无需启动 MinIO 服务。
        
    使用示例：
        >>> storage = LocalStorage()
        >>> object_name = storage.upload_image("/tmp/report.md")
        >>> url = storage.get_image_url(object_name)
    """
    
    def __init__(self):
        """
        初始化本地存储
        
        功能说明：
            创建存储目录（如果不存在），并初始化客户端实例。
        """
        self.base_dir = LOCAL_STORAGE_DIR
        self.bucket = "reports"  # 保持与 MinIO 接口兼容
        
        # 确保存储目录存在
        os.makedirs(self.base_dir, exist_ok=True)
        print(f"[LocalStorage] 初始化本地存储目录: {os.path.abspath(self.base_dir)}")
        
        # 创建模拟客户端，用于兼容 minio_storage.client.remove_object 调用
        self._client = LocalStorageClient(self.base_dir)
    
    @property
    def client(self):
        """
        获取存储客户端（兼容 MinIO 接口）
        
        Returns:
            LocalStorageClient: 本地存储客户端实例
        """
        return self._client
    
    def upload_image(self, file_path, object_name=None):
        """
        上传文件到本地存储目录
        
        Args:
            file_path: 源文件的完整路径
            object_name: 可选，存储后的文件名。如果不指定，使用源文件名
            
        Returns:
            str: 存储后的文件名（object_name）
        """
        if not object_name:
            object_name = os.path.basename(file_path)
        
        dest_path = os.path.join(self.base_dir, object_name)
        
        # 如果源文件和目标路径不同，则复制文件
        if os.path.abspath(file_path) != os.path.abspath(dest_path):
            shutil.copy2(file_path, dest_path)
            print(f"[LocalStorage] 文件已保存: {object_name}")
        else:
            print(f"[LocalStorage] 文件已存在: {object_name}")
        
        return object_name
    
    def get_image_url(self, object_name):
        """
        获取文件的访问 URL
        
        Args:
            object_name: 文件名
            
        Returns:
            str: 文件的本地访问路径或 HTTP URL
            
        说明：
            - 本地存储返回相对路径，如 /reports/filename.md
            - 配合 FastAPI 的 StaticFiles 可通过 HTTP 访问
        """
        # 返回相对于静态文件服务的 URL 路径
        return f"/reports/{object_name}"
    
    def list_files(self, bucket=None):
        """
        列出存储目录中的所有文件
        
        Args:
            bucket: 存储桶名称（本地存储中忽略此参数）
            
        Returns:
            list: 文件名列表
        """
        if not os.path.exists(self.base_dir):
            return []
        
        files = []
        for filename in os.listdir(self.base_dir):
            file_path = os.path.join(self.base_dir, filename)
            if os.path.isfile(file_path):
                files.append(filename)
        
        return files
    
    def get_file_path(self, object_name):
        """
        获取文件的本地完整路径
        
        Args:
            object_name: 文件名
            
        Returns:
            str: 文件的完整本地路径
        """
        return os.path.join(self.base_dir, object_name)
    
    def file_exists(self, object_name):
        """
        检查文件是否存在
        
        Args:
            object_name: 文件名
            
        Returns:
            bool: 文件是否存在
        """
        file_path = os.path.join(self.base_dir, object_name)
        return os.path.exists(file_path) and os.path.isfile(file_path)


# ========================================
# 模块测试代码
# ========================================
if __name__ == "__main__":
    print("=== 本地存储模块测试 ===\n")
    
    # 创建存储实例
    storage = LocalStorage()
    print(f"存储目录: {storage.base_dir}")
    print(f"Bucket: {storage.bucket}")
    
    # 创建测试文件
    test_file = "/tmp/test_local_storage.md"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("# 测试报告\n\n这是一个测试文件。")
    
    # 上传文件
    object_name = storage.upload_image(test_file, "test_report_001.md")
    print(f"上传结果: {object_name}")
    
    # 获取 URL
    url = storage.get_image_url(object_name)
    print(f"访问 URL: {url}")
    
    # 列出文件
    files = storage.list_files()
    print(f"存储目录文件列表: {files}")
    
    # 检查文件存在
    exists = storage.file_exists(object_name)
    print(f"文件是否存在: {exists}")
    
    # 测试删除
    storage.client.remove_object(storage.bucket, object_name)
    print(f"删除后文件是否存在: {storage.file_exists(object_name)}")
