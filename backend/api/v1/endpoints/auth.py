"""
认证相关的API端点
包含注册、登录、刷新令牌等功能
"""
from datetime import datetime, timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.services.user_service import UserService
from backend.models.user import UserCreate, UserResponse, TokenResponse, UserLogin
from backend.core import security
from backend.core.database import get_db
from backend.core.config import settings
import logging

logger = logging.getLogger("api")

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    注册新用户
    
    - **username**: 用户名（唯一）
    - **email**: 邮箱（唯一）
    - **password**: 密码（至少6位）
    - **full_name**: 全名（可选）
    - **bio**: 个人简介（可选）
    """
    # 验证密码长度
    if len(user_in.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 6 characters long"
        )
    
    # 创建用户
    user = await UserService.create_user(db, user_in)
    
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录
    
    支持用户名或邮箱登录
    """
    # 验证用户
    user = await UserService.authenticate_user(
        db, 
        form_data.username, 
        form_data.password
    )
    
    if not user:
        raise AuthenticationException("Incorrect username/email or password")
    
    # 创建访问令牌和刷新令牌
    access_token = security.create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )
    refresh_token = security.create_refresh_token(
        data={"sub": user.username, "user_id": user.id}
    )
    
    # 计算过期时间（秒）
    expires_in = settings.access_token_expire_minutes * 60
    
    logger.info(f"User logged in: {user.username}")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    刷新访问令牌
    
    使用refresh_token获取新的access_token
    """
    # 验证刷新令牌
    payload = verify_token(refresh_token)
    if not payload:
        raise AuthenticationException("Invalid refresh token")
    
    # 检查令牌类型
    if payload.get("type") != "refresh":
        raise AuthenticationException("Invalid token type")
    
    username = payload.get("sub")
    user_id = payload.get("user_id")
    
    if not username or not user_id:
        raise AuthenticationException("Invalid token payload")
    
    # 验证用户是否存在且激活
    user = await UserService.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise AuthenticationException("User not found or inactive")
    
    # 创建新的访问令牌
    access_token = security.create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )
    
    # 创建新的刷新令牌
    new_refresh_token = security.create_refresh_token(
        data={"sub": user.username, "user_id": user.id}
    )
    
    # 计算过期时间（秒）
    expires_in = settings.access_token_expire_minutes * 60
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=expires_in
    )


@router.post("/logout")
async def logout():
    """
    用户登出
    
    注意：由于使用JWT，实际的登出需要在客户端删除令牌
    这里可以用于记录登出事件或清理服务器端状态
    """
    # TODO: 如果需要，可以将令牌加入黑名单
    # 或者清理服务器端的会话状态
    
    return {"message": "Successfully logged out"} 