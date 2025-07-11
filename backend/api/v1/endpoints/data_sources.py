"""
数据源管理API端点
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, status, Form, HTTPException, Path
from sqlalchemy.orm import Session
import os

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.security import get_current_active_user
from backend.models.user import User
from backend.models.data_source import DataSourceResponse, DataSourceCreate
from backend.services.project_service import ProjectService
from backend.services.data_source_service import DataSourceService

router = APIRouter()
logger = logging.getLogger("api")

@router.post(
    "/", 
    response_model=DataSourceResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_data_source(
    project_id: int = Path(..., description="The ID of the project"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """上传文件作为新的数据源"""
    logger.debug(f"Entering upload endpoint for project_id: {project_id}")
    try:
        logger.info(
            f"Starting file upload: {file.filename} for project_id: {project_id} by user: {current_user.email}",
            extra={"upload_filename": file.filename, "project_id": project_id, "user": current_user.email}
        )
        
        # 验证用户是否有权访问该项目
        project = await ProjectService.get_project_by_id(db, project_id, current_user)
        logger.info(f"Project validation successful: {project.name}", extra={"project_id": project.id})
        
        # 创建数据源
        data_source = await DataSourceService.create_data_source_from_upload(db, project, file, current_user)
        logger.info(f"Data source created successfully: ID={data_source.id}", extra={"data_source_id": data_source.id})
        
        return data_source
        
    except HTTPException as http_exc:
        # Re-raise HTTPExceptions directly as they are expected responses
        raise http_exc
    except Exception as e:
        logger.error(f"An unexpected error occurred during file upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during upload."
        )


@router.get(
    "/", 
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


@router.get(
    "/{ds_id}",
    response_model=DataSourceResponse
)
async def get_data_source_details(
    project_id: int,
    ds_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取单个数据源的详细信息"""
    # 验证项目访问权限
    project = await ProjectService.get_project_by_id(db, project_id, current_user)
    # 获取数据源详情
    return await DataSourceService.get_data_source_by_id(db, ds_id, project.id)


@router.get(
    "/{ds_id}/similar",
    response_model=List[DataSourceResponse],
    summary="Find similar images",
    description="Finds and returns a list of data sources containing images similar to the one in the specified data source, based on perceptual hash.",
)
async def find_similar_images_endpoint(
    project_id: int,
    ds_id: int,
    threshold: int = 4,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Finds data sources with similar images.

    - **project_id**: The ID of the project.
    - **ds_id**: The ID of the data source containing the source image.
    - **threshold**: The maximum Hamming distance for images to be considered similar.
      Lower values mean higher similarity. Default is 4.
    """
    # First, verify the user has access to the project
    project = await ProjectService.get_project_by_id(db, project_id, current_user)
    
    # Now, find similar images
    similar_data_sources = await DataSourceService.find_similar_images(
        db, ds_id=ds_id, project_id=project.id, threshold=threshold
    )
    return similar_data_sources


@router.delete(
    "/{ds_id}", 
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