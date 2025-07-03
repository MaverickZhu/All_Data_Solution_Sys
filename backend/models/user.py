"""
用户数据模型
"""
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, Text
from sqlalchemy.orm import relationship
from backend.core.database import Base
from .base import TimestampMixin, SoftDeleteMixin, BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema


class User(Base, TimestampMixin, SoftDeleteMixin):
    """用户模型"""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    
    # 账号状态
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # 关系
    # projects = relationship("Project", back_populates="owner")
    # analyses = relationship("Analysis", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"


# ==================== Pydantic模式 ====================

class UserBase(BaseCreateSchema):
    """用户基础模式"""
    username: str
    email: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    """创建用户模式"""
    password: str


class UserUpdate(BaseUpdateSchema):
    """更新用户模式"""
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    password: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class UserInDB(UserBase, BaseResponseSchema):
    """数据库中的用户模式"""
    hashed_password: str
    avatar_url: Optional[str] = None
    is_verified: bool = False


class UserResponse(BaseResponseSchema):
    """用户响应模式"""
    username: str
    email: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False


class UserLogin(BaseCreateSchema):
    """用户登录模式"""
    username: str
    password: str


class TokenResponse(BaseCreateSchema):
    """令牌响应模式"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒


class TokenPayload(BaseCreateSchema):
    """令牌载荷模式"""
    sub: str  # 用户名
    exp: int  # 过期时间
    iat: int  # 签发时间
    type: str = "access"  # 令牌类型: access or refresh 