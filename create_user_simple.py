#!/usr/bin/env python3
"""
简化的用户创建脚本，用于在Docker容器中运行
"""
import asyncio
import os
import sys

# 设置环境变量
os.environ['APP_ENV'] = 'docker'
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://postgres:password@postgres:5432/multimodal_analysis'

# 将backend目录添加到Python路径
sys.path.insert(0, '/app/backend')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.models.user import User
from backend.core.security import get_password_hash

async def create_test_user():
    """创建测试用户"""
    # 创建数据库引擎
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:password@postgres:5432/multimodal_analysis",
        echo=False
    )
    
    # 创建会话
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # 检查用户是否已存在
        result = await session.execute(
            "SELECT id FROM users WHERE username = 'testuser'"
        )
        if result.fetchone():
            print("用户 'testuser' 已存在")
            return
        
        # 创建新用户
        hashed_password = get_password_hash("testpass123")
        
        # 直接执行SQL插入
        await session.execute(
            """
            INSERT INTO users (username, email, full_name, hashed_password, is_active, is_superuser, is_deleted, created_at, updated_at)
            VALUES ('testuser', 'test@example.com', 'Test User', :password, true, false, false, NOW(), NOW())
            """,
            {"password": hashed_password}
        )
        
        await session.commit()
        print("测试用户创建成功: testuser / testpass123")

if __name__ == "__main__":
    asyncio.run(create_test_user()) 