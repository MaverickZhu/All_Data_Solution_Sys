"""
用户管理的API端点
包含获取用户信息、更新用户信息等功能
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.services.user_service import UserService
from backend.models.user import User, UserCreate, UserUpdate, UserResponse
from backend.core.database import get_db
from backend.core.security import get_current_user, get_current_active_user, get_current_superuser
import logging

logger = logging.getLogger("api")

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_create: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建新用户（注册）
    - **username**: 必须，唯一的用户名
    - **email**: 必须，唯一的邮箱
    - **password**: 必须，密码
    """
    # 检查用户名是否已存在
    existing_user_by_name = await UserService.get_user_by_username(db, user_create.username)
    if existing_user_by_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{user_create.username}' is already registered.",
        )
    
    # 检查邮箱是否已存在
    existing_user_by_email = await UserService.get_user_by_email(db, user_create.email)
    if existing_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{user_create.email}' is already registered.",
        )
        
    user = await UserService.create_user(db, user_create)
    # 不应该在响应中返回完整的user对象，特别是密码哈希
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前登录用户信息
    """
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
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
    update_data = user_update.model_dump(exclude_unset=True)
    
    # 用户不能通过此端点修改自己的权限状态，直接忽略这些字段
    update_data.pop('is_active', None)
    update_data.pop('is_superuser', None)
    
    # 如果没有可更新的内容，则直接返回当前用户信息
    if not update_data:
        return UserResponse.model_validate(current_user)
    
    user = await UserService.update_user(db, current_user.id, update_data)
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
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
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    更新指定用户信息（需要管理员权限）
    
    管理员可以修改用户的所有字段，包括：
    - 基本信息（用户名、邮箱等）
    - 权限状态（is_active、is_superuser）
    """
    update_data = user_update.model_dump(exclude_unset=True)
    user = await UserService.update_user(db, user_id, update_data)
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
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
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    激活用户账号（需要管理员权限）
    """
    update_data = {"is_active": True}
    user = await UserService.update_user(db, user_id, update_data)
    logger.info(f"User activated by admin: {user.username}")
    return UserResponse.model_validate(user)


@router.post("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    停用用户账号（需要管理员权限）
    """
    update_data = {"is_active": False}
    user = await UserService.update_user(db, user_id, update_data)
    logger.info(f"User deactivated by admin: {user.username}")
    return UserResponse.model_validate(user) 