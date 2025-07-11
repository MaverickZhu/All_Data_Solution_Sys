"""
安全认证模块
包含JWT令牌生成、验证、密码哈希等功能
"""
from datetime import datetime, timedelta
from typing import Optional, Union, TYPE_CHECKING
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.database import get_db

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2密码承载令牌
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/login")

if TYPE_CHECKING:
    from backend.models.user import User


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希值"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌
    
    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量
    
    Returns:
        编码后的JWT令牌
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    创建刷新令牌
    
    Args:
        data: 要编码的数据
    
    Returns:
        编码后的刷新令牌
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> "User":
    """
    解码令牌, 从数据库获取并返回当前用户对象
    
    Args:
        token: JWT令牌
        db: 数据库会话
    
    Returns:
        SQLAlchemy User object
    
    Raises:
        HTTPException: 认证失败时抛出
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        # 检查令牌类型
        token_type = payload.get("type", "access")
        if token_type != "access":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # 从payload中获取用户ID
    user_id = payload.get("user_id")
    if user_id is None:
        raise credentials_exception
    
    # 从数据库获取用户实际信息
    from backend.models.user import User
    from sqlalchemy import select
    
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_deleted == False)
    )
    db_user = result.scalar_one_or_none()
    
    if not db_user:
        raise credentials_exception
    
    # Refresh the user object to eagerly load all relationships and prevent
    # unexpected lazy loading errors in later processing steps.
    await db.refresh(db_user)
    
    return db_user


async def get_current_active_user(
    current_user: "User" = Depends(get_current_user)
) -> "User":
    """
    获取当前活跃用户
    
    Args:
        current_user: 当前用户对象
    
    Returns:
        活跃用户对象
    
    Raises:
        HTTPException: 用户未激活时抛出
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_superuser(
    current_user: "User" = Depends(get_current_active_user)
) -> "User":
    """
    获取当前超级用户
    
    Args:
        current_user: 当前用户对象
    
    Returns:
        超级用户对象
    
    Raises:
        HTTPException: 用户不是超级用户时抛出
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user


def verify_token(token: str) -> Optional[dict]:
    """
    验证令牌（用于WebSocket等场景）
    
    Args:
        token: JWT令牌
    
    Returns:
        解码后的令牌数据，验证失败返回None
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None


class RateLimiter:
    """
    简单的速率限制器
    基于内存的实现，生产环境建议使用Redis
    """
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        初始化速率限制器
        
        Args:
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口大小（秒）
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    async def check_rate_limit(self, key: str) -> bool:
        """
        检查是否超过速率限制
        
        Args:
            key: 限制键（如用户ID、IP地址等）
        
        Returns:
            True表示未超限，False表示超限
        """
        now = datetime.utcnow()
        
        # 清理过期记录
        if key in self.requests:
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if (now - req_time).total_seconds() < self.window_seconds
            ]
        else:
            self.requests[key] = []
        
        # 检查是否超限
        if len(self.requests[key]) >= self.max_requests:
            return False
        
        # 记录新请求
        self.requests[key].append(now)
        return True


# 全局速率限制器实例
rate_limiter = RateLimiter() 