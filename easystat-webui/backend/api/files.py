"""
EasySTAT WebUI 后端 - 文件管理 API 路由

主要功能：
- 获取生成的文件列表（结果、日志、中间数据）
- 预览文件内容
- 下载文件
- 删除文件
"""

import os
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from services.file_service import file_service
from core.config import settings

router = APIRouter()

@router.get("/files", response_model=List[Dict[str, Any]])
async def list_files():
    """
    获取生成的文件列表
    
    扫描 result/ 和 logs/ 目录，返回文件元数据。
    
    Returns:
        List[Dict]: 文件信息列表
    """
    return file_service.list_files()

@router.get("/files/content")
async def get_file_content(
    path: str = Query(..., description="相对于项目根目录的文件路径")
):
    """
    获取文件内容（用于预览）
    
    Args:
        path (str): 文件的相对路径
        
    Returns:
        dict: 包含 content 字段的字典
    """
    content = file_service.get_file_content(path)
    if content is None:
        raise HTTPException(status_code=404, detail="文件不存在或无法读取")
    return {"content": content}

@router.get("/files/download")
async def download_file(
    path: str = Query(..., description="相对于项目根目录的文件路径")
):
    """
    下载文件
    
    Args:
        path (str): 文件的相对路径
        
    Returns:
        FileResponse: 文件下载响应
    """
    full_path = os.path.join(settings.EASYSTAT_PROJECT_PATH, path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        full_path, 
        filename=os.path.basename(full_path),
        media_type='application/octet-stream'
    )

@router.delete("/files")
async def delete_file(
    path: str = Query(..., description="相对于项目根目录的文件路径")
):
    """
    删除文件
    
    Args:
        path (str): 文件的相对路径
        
    Returns:
        dict: 包含 success 字段的字典
    """
    success = file_service.delete_file(path)
    if not success:
        raise HTTPException(status_code=400, detail="删除失败，文件可能不存在或路径不安全")
    return {"success": True}
