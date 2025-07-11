"""
测试认证API的脚本
验证用户注册、登录、获取信息等功能
"""
import requests
import json
import sys
import random
import string

# API基础URL
BASE_URL = "http://127.0.0.1:8000/api/v1"
# BASE_URL = "http://localhost:8000/api/v1"

def random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def print_response(name, res):
    print(f"--- {name} ---")
    print(f"URL: {res.url}")
    print(f"Status Code: {res.status_code}")
    try:
        print(f"Response JSON: {json.dumps(res.json(), indent=2, ensure_ascii=False)}")
    except json.JSONDecodeError:
        print(f"Response Text: {res.text}")
    print("-" * (len(name) + 8))
    print()

def main():
    # 使用随机用户名和邮箱以确保每次测试的独立性
    username = f"testuser_{random_string()}"
    email = f"{username}@example.com"
    password = "testpassword"
    full_name = "Test User"
    bio = "This is a test user."
    
    session = requests.Session()
    access_token = None

    # 1. 注册新用户
    print("Step 1: Registering a new user...")
    register_data = {
        "username": username,
        "email": email,
        "password": password,
        "full_name": full_name,
        "bio": bio
    }
    res_register = session.post(f"{BASE_URL}/auth/register", json=register_data)
    print_response("Register User", res_register)
    if res_register.status_code != 201:
        print("Registration failed. Aborting test.")
        return

    # 2. 用户登录
    print("Step 2: Logging in...")
    login_data = {
        "username": username,
        "password": password
    }
    res_login = session.post(f"{BASE_URL}/auth/login", data=login_data)
    print_response("Login", res_login)
    if res_login.status_code != 200:
        print("Login failed. Aborting test.")
        return
    access_token = res_login.json().get("access_token")
    session.headers.update({"Authorization": f"Bearer {access_token}"})

    # 3. 获取当前用户信息
    print("Step 3: Getting current user info...")
    res_get_me = session.get(f"{BASE_URL}/users/me")
    print_response("Get User (/me)", res_get_me)
    if res_get_me.status_code != 200:
        print("Failed to get user info. Aborting test.")
        return
    assert res_get_me.json()["username"] == username
    assert res_get_me.json()["bio"] == bio
    print("User info verified.")

    # 4. 更新用户信息
    print("Step 4: Updating user info...")
    new_bio = "This is the updated bio."
    update_data = {
        "bio": new_bio
    }
    res_update_me = session.put(f"{BASE_URL}/users/me", json=update_data)
    print_response("Update User (/me)", res_update_me)
    if res_update_me.status_code != 200:
        print("Failed to update user info. Aborting test.")
        return
    assert res_update_me.json()["bio"] == new_bio
    print("User info update verified.")

    # 5. 再次获取用户信息进行验证
    print("Step 5: Verifying user info update...")
    res_verify_me = session.get(f"{BASE_URL}/users/me")
    print_response("Verify Update (/me)", res_verify_me)
    if res_verify_me.status_code != 200:
        print("Failed to get user info after update. Aborting test.")
        return
    assert res_verify_me.json()["bio"] == new_bio
    print("User info successfully updated and verified!")
    print("\n✅ All auth API tests passed! ✅")


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