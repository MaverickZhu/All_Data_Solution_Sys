"""
用户服务层
处理用户相关的业务逻辑
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timezone

from backend.models.user import User, UserCreate, UserUpdate
from backend.core.security import get_password_hash, verify_password
from backend.core.exceptions import NotFoundException, DuplicateException, ValidationException
import logging

logger = logging.getLogger(__name__)


class UserService:
    """用户服务类"""
    
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """
        创建新用户
        
        Args:
            db: 数据库会话
            user_data: 用户创建数据
            
        Returns:
            创建的用户对象
            
        Raises:
            DuplicateException: 用户名或邮箱已存在
        """
        # 检查用户名是否已存在
        result = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        if result.scalar_one_or_none():
            raise DuplicateException("User", "username", user_data.username)
        
        # 检查邮箱是否已存在
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        if result.scalar_one_or_none():
            raise DuplicateException("User", "email", user_data.email)
        
        # 创建用户
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=get_password_hash(user_data.password),
            bio=user_data.bio,
            is_active=user_data.is_active,
            is_superuser=user_data.is_superuser
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        logger.info(f"Created new user: {db_user.username}")
        return db_user
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
        """
        通过ID获取用户
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            用户对象
            
        Raises:
            NotFoundException: 用户不存在
        """
        result = await db.execute(
            select(User).where(User.id == user_id, User.is_deleted == False)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundException("User", user_id)
        
        return user
    
    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """
        通过用户名获取用户
        
        Args:
            db: 数据库会话
            username: 用户名
            
        Returns:
            用户对象或None
        """
        result = await db.execute(
            select(User).where(User.username == username, User.is_deleted == False)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """
        通过邮箱获取用户
        
        Args:
            db: 数据库会话
            email: 邮箱
            
        Returns:
            用户对象或None
        """
        result = await db.execute(
            select(User).where(User.email == email, User.is_deleted == False)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    def get_user_by_username_sync(db: Session, username: str) -> Optional[User]:
        """
        通过用户名获取用户 (同步版本)
        """
        return db.query(User).filter(User.username == username, User.is_deleted == False).first()

    @staticmethod
    def get_user_by_email_sync(db: Session, email: str) -> Optional[User]:
        """
        通过邮箱获取用户 (同步版本)
        """
        return db.query(User).filter(User.email == email, User.is_deleted == False).first()

    @staticmethod
    async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
        """
        验证用户身份
        
        Args:
            db: 数据库会话
            username: 用户名
            password: 密码
            
        Returns:
            验证成功返回用户对象，否则返回None
        """
        user = await UserService.get_user_by_username(db, username)
        if not user:
            # 也尝试通过邮箱登录 (修正拼写错误)
            user = await UserService.get_user_by_email(db, username)
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        return user

    @staticmethod
    def authenticate_user_sync(db: Session, username: str, password: str) -> Optional[User]:
        """
        验证用户身份 (同步版本)
        
        Args:
            db: 同步数据库会话
            username: 用户名
            password: 密码
            
        Returns:
            验证成功返回用户对象，否则返回None
        """
        user = UserService.get_user_by_username_sync(db, username)
        if not user:
            # 也尝试通过邮箱登录
            user = UserService.get_user_by_email_sync(db, username)
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        return user
    
    @staticmethod
    async def update_user(
        db: AsyncSession, 
        user_id: int, 
        update_data: dict
    ) -> User:
        """
        更新用户信息
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            update_data: 包含更新字段的字典
            
        Returns:
            更新后的用户对象
            
        Raises:
            NotFoundException: 用户不存在
            DuplicateException: 用户名或邮箱已被使用
        """
        user = await UserService.get_user_by_id(db, user_id)
        
        # 检查用户名是否被其他用户使用
        if "username" in update_data and update_data["username"] and update_data["username"] != user.username:
            result = await db.execute(
                select(User).where(User.username == update_data["username"])
            )
            if result.scalar_one_or_none():
                raise DuplicateException("User", "username", update_data["username"])
        
        # 检查邮箱是否被其他用户使用
        if "email" in update_data and update_data["email"] and update_data["email"] != user.email:
            result = await db.execute(
                select(User).where(User.email == update_data["email"])
            )
            if result.scalar_one_or_none():
                raise DuplicateException("User", "email", update_data["email"])
        
        # 如果更新密码，需要加密
        if "password" in update_data and update_data["password"]:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        elif "password" in update_data:
            # 如果密码字段存在但为空或None，则从更新数据中移除，避免将密码设置为空
            update_data.pop("password")
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"Updated user: {user.username}")
        return user
    
    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int) -> None:
        """
        软删除用户
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Raises:
            NotFoundException: 用户不存在
        """
        user = await UserService.get_user_by_id(db, user_id)
        
        user.is_deleted = True
        user.deleted_at = datetime.utcnow()
        user.is_active = False
        
        await db.commit()
        logger.info(f"Soft deleted user: {user.username}") 