"""
创建测试用户脚本
用于开发和测试环境
"""
import asyncio
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from core.database import AsyncSessionLocal, init_db
from services.user_service import UserService
from models.user import UserCreate

test_users = [
    {
        "username": "admin",
        "email": "admin@example.com",
        "password": "admin123",
        "full_name": "System Administrator",
        "bio": "平台管理员账号",
        "is_superuser": True,
        "is_active": True
    },
    {
        "username": "demo",
        "email": "demo@example.com",
        "password": "demo123",
        "full_name": "Demo User",
        "bio": "演示用户账号",
        "is_superuser": False,
        "is_active": True
    }
]


async def create_test_users():
    """创建测试用户"""
    print("🚀 开始创建测试用户...")
    
    # 初始化数据库表
    print("📊 初始化数据库表...")
    await init_db()
    
    async with AsyncSessionLocal() as db:
        for user_data in test_users:
            try:
                # 检查用户是否已存在
                existing_user = await UserService.get_user_by_username(db, user_data["username"])
                if existing_user:
                    print(f"⚠️ 用户 '{user_data['username']}' 已存在，跳过创建")
                    continue
                
                # 创建用户
                user_create = UserCreate(**user_data)
                user = await UserService.create_user(db, user_create)
                print(f"✅ 创建用户成功: {user.username} (超级用户: {user.is_superuser})")
                
            except Exception as e:
                print(f"❌ 创建用户 '{user_data['username']}' 失败: {e}")
    
    print("\n✨ 测试用户创建完成!")
    print("\n可用的测试账号：")
    print("┌─────────────┬──────────────┬─────────────┐")
    print("│ 用户名      │ 密码         │ 权限        │")
    print("├─────────────┼──────────────┼─────────────┤")
    print("│ admin       │ admin123     │ 管理员      │")
    print("│ demo        │ demo123      │ 普通用户    │")
    print("└─────────────┴──────────────┴─────────────┘")


if __name__ == "__main__":
    asyncio.run(create_test_users()) 