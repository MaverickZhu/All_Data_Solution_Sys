"""
用户管理的API端点
包含获取用户信息、更新用户信息等功能
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_user, get_current_active_user, get_current_superuser
from models.user import UserResponse, UserUpdate
from services.user_service import UserService
import logging

logger = logging.getLogger("api")

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前登录用户信息
    """
    user = await UserService.get_user_by_id(db, current_user["id"])
    return UserResponse.model_validate(user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新当前用户信息
    
    可更新字段：
    - **username**: 用户名
    - **email**: 邮箱
    - **full_name**: 全名
    - **bio**: 个人简介
    - **password**: 密码
    - **avatar_url**: 头像URL
    """
    # 普通用户不能修改自己的权限状态
    if user_update.is_active is not None or user_update.is_superuser is not None:
        # 创建新的更新对象，排除权限字段
        update_dict = user_update.model_dump(exclude_unset=True)
        update_dict.pop('is_active', None)
        update_dict.pop('is_superuser', None)
        user_update = UserUpdate(**update_dict)
    
    user = await UserService.update_user(db, current_user["id"], user_update)
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定用户信息
    
    任何登录用户都可以查看其他用户的公开信息
    """
    user = await UserService.get_user_by_id(db, user_id)
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    更新指定用户信息（需要管理员权限）
    
    管理员可以修改用户的所有字段，包括：
    - 基本信息（用户名、邮箱等）
    - 权限状态（is_active、is_superuser）
    """
    user = await UserService.update_user(db, user_id, user_update)
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    删除用户（软删除，需要管理员权限）
    """
    await UserService.delete_user(db, user_id)
    return None


@router.post("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: int,
    current_user: dict = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    激活用户账号（需要管理员权限）
    """
    user_update = UserUpdate(is_active=True)
    user = await UserService.update_user(db, user_id, user_update)
    logger.info(f"User activated by admin: {user.username}")
    return UserResponse.model_validate(user)


@router.post("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: int,
    current_user: dict = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    停用用户账号（需要管理员权限）
    """
    user_update = UserUpdate(is_active=False)
    user = await UserService.update_user(db, user_id, user_update)
    logger.info(f"User deactivated by admin: {user.username}")
    return UserResponse.model_validate(user) 