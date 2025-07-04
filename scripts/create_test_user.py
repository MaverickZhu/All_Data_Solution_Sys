"""
创建测试用户脚本
用于开发和测试环境
"""
import asyncio
import sys
import os

# 将项目根目录添加到Python的模块搜索路径中
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import AsyncSessionLocal, init_db
from backend.models.user import UserCreate, User
from backend.models.project import Project
from backend.models.data_source import DataSource
from backend.models.task import ProcessingTask
from backend.services.user_service import UserService

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
                user_service = UserService(db)
                existing_user = await user_service.get_user_by_username(user_data["username"])
                if existing_user:
                    print(f"⚠️ 用户 '{user_data['username']}' 已存在，跳过创建")
                    continue
                
                # 创建用户
                user_create = UserCreate(**user_data)
                user = await user_service.create_user(user_create)
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


async def main():
    """主函数，创建测试用户"""
    print("开始创建测试用户...")
    db: AsyncSession = AsyncSessionLocal()
    try:
        # 在这里定义测试用户信息
        user_in = UserCreate(
            username="demo",
            email="demo@example.com",
            password="password",
            full_name="Demo User",
            bio="This is a demo user for testing purposes."
        )
        
        existing_user = await UserService.get_user_by_username(db, user_in.username)
        
        if existing_user:
            print(f"用户 '{user_in.username}' 已存在，跳过创建。")
        else:
            new_user = await UserService.create_user(db, user_in)
            print(f"✅ 用户 '{new_user.username}' 创建成功！")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"创建用户时发生错误: {e}")
    finally:
        await db.close()
        print("数据库连接已关闭。")

if __name__ == "__main__":
    asyncio.run(main())