"""
存储模块

功能说明：
    提供统一的文件存储接口，支持 MinIO 对象存储和本地文件夹存储两种模式。
    通过环境变量 STORAGE_TYPE 控制使用哪种存储方式。

主要类：
    - MinioStorage: MinIO 对象存储（生产环境推荐）
    - LocalStorage: 本地文件夹存储（开发环境推荐）

环境变量：
    - STORAGE_TYPE: 存储类型，可选值为 "local" 或 "minio"，默认为 "local"
    - MINIO_ENDPOINT: MinIO 服务地址
    - MINIO_ACCESS_KEY: MinIO 访问密钥
    - MINIO_SECRET_KEY: MinIO 密钥
    - MINIO_BUCKET: MinIO 存储桶名称

作者：Financial_Program
日期：2024-12
"""

from minio import Minio
import os
from dotenv import load_dotenv
from datetime import timedelta

# 加载环境变量
load_dotenv()

# ========================================
# 存储类型配置
# ========================================
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local")  # "local" 或 "minio"


class MinioStorage:
    """
    MinIO 对象存储类
    
    功能说明：
        提供基于 MinIO 的对象存储功能，适用于生产环境。
        支持文件上传、下载 URL 生成、文件列表查询等操作。
    """
    
    def __init__(self):
        """
        初始化 MinIO 存储
        
        功能说明：
            连接 MinIO 服务，并确保存储桶存在。
        """
        self.client = Minio(
            os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            secure=os.getenv("MINIO_SECURE", "False").lower() in ["true", "1", "t"],
        )
        self.bucket = os.getenv("MINIO_BUCKET", "data")
        # 确保存储桶存在
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
        print(f"[MinioStorage] 已连接到 MinIO: {os.getenv('MINIO_ENDPOINT', 'localhost:9000')}")

    def upload_image(self, file_path, object_name=None):
        """
        上传文件到 MinIO
        
        Args:
            file_path: 源文件的完整路径
            object_name: 可选，存储后的对象名称
            
        Returns:
            str: 存储后的对象名称
        """
        if not object_name:
            object_name = os.path.basename(file_path)
        file_stat = os.stat(file_path)
        # 根据文件扩展名确定 content_type
        ext = os.path.splitext(file_path)[1].lower()
        content_type_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".md": "text/markdown",
            ".pdf": "application/pdf",
            ".txt": "text/plain",
        }
        content_type = content_type_map.get(ext, "application/octet-stream")
        with open(file_path, "rb") as f:
            self.client.put_object(
                self.bucket,
                object_name,
                f,
                file_stat.st_size,
                content_type=content_type,
            )
        print(f"[MinioStorage] 文件已上传: {object_name}")
        return object_name

    def get_image_url(self, object_name):
        """
        获取文件的预签名访问 URL
        
        Args:
            object_name: 对象名称
            
        Returns:
            str: 预签名 URL，有效期 1 天
        """
        return self.client.presigned_get_object(
            self.bucket, object_name, expires=timedelta(seconds=60 * 60 * 24)
        )

    def list_files(self, bucket=None):
        """
        列出存储桶中的所有文件
        
        Args:
            bucket: 可选，存储桶名称
            
        Returns:
            list: 文件名列表
        """
        bucket = bucket or self.bucket
        objects = self.client.list_objects(bucket, recursive=True)
        return [obj.object_name for obj in objects]


# ========================================
# 存储实例选择逻辑
# ========================================
def _create_storage_instance():
    """
    根据环境变量创建存储实例
    
    Returns:
        存储实例（MinioStorage 或 LocalStorage）
    """
    if STORAGE_TYPE.lower() == "minio":
        print("[Storage] 使用 MinIO 对象存储")
        return MinioStorage()
    else:
        # 导入本地存储类
        from storage.local_storage import LocalStorage
        print("[Storage] 使用本地文件夹存储")
        return LocalStorage()


# 创建全局存储实例
# 注意：变量名保持为 minio_storage 以兼容现有代码
minio_storage = _create_storage_instance()

