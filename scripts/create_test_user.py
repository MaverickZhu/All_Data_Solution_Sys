"""
创建测试用户脚本
用于开发和测试环境
"""
import asyncio
import sys
import os

# 将项目根目录添加到Python的模块搜索路径中
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.database import AsyncSessionLocal, init_db
from backend.models.user import UserCreate
from backend.services.user_service import UserService

# 定义标准的测试用户数据
# 我们将统一使用这些用户进行所有测试
test_users_data = [
    {
        "username": "admin",
        "email": "admin@example.com",
        "password": "admin123",
        "full_name": "System Administrator",
        "bio": "平台管理员账号，拥有所有权限。",
        "is_superuser": True,
        "is_active": True
    },
    {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpass123",
        "full_name": "Standard Test User",
        "bio": "标准的测试用户账号，用于功能回归测试。",
        "is_superuser": False,
        "is_active": True
    }
]


async def create_standard_test_users():
    """
    一个统一的、标准的函数，用于创建或验证测试用户。
    它会检查用户是否存在，如果不存在则创建。
    """
    print("🚀 开始创建标准测试用户...")
    
    # 确保数据库和表已初始化
    await init_db()
    
    async with AsyncSessionLocal() as db:
        for user_data in test_users_data:
            try:
                # 1. 检查用户是否已存在
                # UserService的方法是静态的，直接通过类调用
                existing_user = await UserService.get_user_by_username(db, user_data["username"])
                if existing_user:
                    print(f"✅ 用户 '{user_data['username']}' 已存在，跳过创建。")
                    continue
                
                # 2. 如果不存在，则创建用户
                user_create = UserCreate(**user_data)
                # 直接通过类调用静态方法
                user = await UserService.create_user(db, user_create)
                print(f"👍 创建用户成功: {user.username} (超级用户: {user.is_superuser})")
                
            except Exception as e:
                print(f"❌ 创建用户 '{user_data['username']}' 时发生错误: {e}")
                import traceback
                traceback.print_exc()

    print("\n✨ 标准测试用户创建流程完成!")
    print("\n可用的测试账号：")
    print("┌────────────┬─────────────┬──────────┐")
    print("│ 用户名     │ 密码        │ 权限     │")
    print("├────────────┼─────────────┼──────────┤")
    print("│ admin      │ admin123    │ 管理员   │")
    print("│ testuser   │ testpass123 │ 普通用户 │")
    print("└────────────┴─────────────┴──────────┘")


if __name__ == "__main__":
    # 确保只运行这个标准的创建函数
    asyncio.run(create_standard_test_users())