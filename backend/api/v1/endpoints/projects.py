"""
项目管理API端点
"""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.security import get_current_active_user
from backend.models.user import User
from backend.models.project import Project, ProjectCreate, ProjectUpdate, ProjectResponse
from backend.services.project_service import ProjectService
from backend.api.v1.endpoints import data_sources

router = APIRouter()

# 将数据源路由作为子路由包含进来
router.include_router(data_sources.router, prefix="/{project_id}/datasources", tags=["Data Sources"])

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建新项目"""
    return await ProjectService.create_project(db, project_in, current_user)

@router.get("/", response_model=List[ProjectResponse])
async def read_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100
):
    """获取当前用户的所有项目"""
    return await ProjectService.get_user_projects(db, user_id=current_user.id)

@router.get("/{project_id}", response_model=ProjectResponse)
async def read_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取单个项目详情"""
    return await ProjectService.get_project_by_id(db, project_id, current_user)

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新项目"""
    return await ProjectService.update_project(db, project_id, project_in, current_user)

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除项目"""
    await ProjectService.delete_project(db, project_id, current_user)
    return None 