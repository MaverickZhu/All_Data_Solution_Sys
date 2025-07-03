"""
测试认证API的脚本
验证用户注册、登录、获取信息等功能
"""
import requests
import json
import sys

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

# 测试数据
test_user = {
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "test123",
    "full_name": "Test User",
    "bio": "This is a test user"
}


def test_register():
    """测试用户注册"""
    print("\n📝 测试用户注册...")
    
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json=test_user
    )
    
    if response.status_code == 201:
        user_data = response.json()
        print(f"✅ 注册成功! 用户ID: {user_data['id']}")
        print(f"   用户名: {user_data['username']}")
        print(f"   邮箱: {user_data['email']}")
        return True
    elif response.status_code == 409:
        print("⚠️ 用户已存在")
        return True
    else:
        print(f"❌ 注册失败: {response.status_code}")
        print(f"   错误信息: {response.json()}")
        return False


def test_login():
    """测试用户登录"""
    print("\n🔐 测试用户登录...")
    
    # OAuth2登录需要使用表单数据
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": test_user["username"],
            "password": test_user["password"],
            "grant_type": "password"
        }
    )
    
    if response.status_code == 200:
        token_data = response.json()
        print("✅ 登录成功!")
        print(f"   Token类型: {token_data['token_type']}")
        print(f"   过期时间: {token_data['expires_in']}秒")
        print(f"   Access Token: {token_data['access_token'][:50]}...")
        return token_data
    else:
        print(f"❌ 登录失败: {response.status_code}")
        print(f"   错误信息: {response.json()}")
        return None


def test_get_user_info(access_token):
    """测试获取用户信息"""
    print("\n👤 测试获取当前用户信息...")
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(
        f"{BASE_URL}/users/me",
        headers=headers
    )
    
    if response.status_code == 200:
        user_info = response.json()
        print("✅ 获取用户信息成功!")
        print(f"   ID: {user_info['id']}")
        print(f"   用户名: {user_info['username']}")
        print(f"   邮箱: {user_info['email']}")
        print(f"   全名: {user_info.get('full_name', 'N/A')}")
        print(f"   激活状态: {user_info['is_active']}")
        return True
    else:
        print(f"❌ 获取用户信息失败: {response.status_code}")
        print(f"   错误信息: {response.json()}")
        return False


def test_update_user_info(access_token):
    """测试更新用户信息"""
    print("\n✏️ 测试更新用户信息...")
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    update_data = {
        "bio": "Updated bio for test user",
        "full_name": "Updated Test User"
    }
    
    response = requests.put(
        f"{BASE_URL}/users/me",
        headers=headers,
        json=update_data
    )
    
    if response.status_code == 200:
        user_info = response.json()
        print("✅ 更新用户信息成功!")
        print(f"   新的全名: {user_info['full_name']}")
        print(f"   新的简介: {user_info['bio']}")
        return True
    else:
        print(f"❌ 更新用户信息失败: {response.status_code}")
        print(f"   错误信息: {response.json()}")
        return False


def test_admin_login():
    """测试管理员登录"""
    print("\n👑 测试管理员登录...")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": "admin",
            "password": "admin123",
            "grant_type": "password"
        }
    )
    
    if response.status_code == 200:
        token_data = response.json()
        print("✅ 管理员登录成功!")
        return token_data["access_token"]
    else:
        print(f"❌ 管理员登录失败: {response.status_code}")
        return None


def main():
    """主测试函数"""
    print("🚀 开始测试认证API...")
    print(f"   API地址: {BASE_URL}")
    
    # 1. 测试注册
    if not test_register():
        print("\n❌ 测试失败：注册功能异常")
        return
    
    # 2. 测试登录
    token_data = test_login()
    if not token_data:
        print("\n❌ 测试失败：登录功能异常")
        return
    
    access_token = token_data["access_token"]
    
    # 3. 测试获取用户信息
    if not test_get_user_info(access_token):
        print("\n❌ 测试失败：获取用户信息功能异常")
        return
    
    # 4. 测试更新用户信息
    if not test_update_user_info(access_token):
        print("\n❌ 测试失败：更新用户信息功能异常")
        return
    
    # 5. 测试管理员登录
    admin_token = test_admin_login()
    if admin_token:
        print("   管理员功能正常")
    
    print("\n✨ 所有测试完成!")
    print("\n📊 测试结果汇总：")
    print("   ✅ 用户注册: 通过")
    print("   ✅ 用户登录: 通过")
    print("   ✅ 获取用户信息: 通过")
    print("   ✅ 更新用户信息: 通过")
    if admin_token:
        print("   ✅ 管理员登录: 通过")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器，请确保后端服务正在运行")
        print("   运行命令: cd backend && python main.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        sys.exit(1) 