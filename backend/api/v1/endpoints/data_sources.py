"""
数据源管理API端点
"""
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, status

from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_active_user
from models.user import User
from models.data_source import DataSourceResponse
from services.project_service import ProjectService
from services.data_source_service import DataSourceService

router = APIRouter()

@router.post(
    "/projects/{project_id}/datasources/upload", 
    response_model=DataSourceResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_data_source(
    project_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """上传文件作为新的数据源"""
    # 验证用户是否有权访问该项目
    project = await ProjectService.get_project_by_id(db, project_id, current_user)
    
    # 创建数据源
    data_source = await DataSourceService.create_data_source_from_upload(db, project, file)
    return data_source


@router.get(
    "/projects/{project_id}/datasources", 
    response_model=List[DataSourceResponse]
)
async def list_data_sources(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """列出项目的所有数据源"""
    # 验证用户是否有权访问该项目
    await ProjectService.get_project_by_id(db, project_id, current_user)
    
    # 获取数据源列表
    return await DataSourceService.get_data_sources_by_project(db, project_id)


@router.delete(
    "/projects/{project_id}/datasources/{ds_id}", 
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_data_source(
    project_id: int,
    ds_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除一个数据源"""
    # 验证用户是否有权访问该项目
    project = await ProjectService.get_project_by_id(db, project_id, current_user)
    
    # 获取并验证数据源
    ds = await DataSourceService.get_data_source_by_id(db, ds_id, project.id)

    # 删除数据源
    await DataSourceService.delete_data_source(db, ds)
    return None 