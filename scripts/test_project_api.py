"""
测试项目管理API
"""
import requests
import json
import random
import string

BASE_URL = "http://127.0.0.1:8000/api/v1"
AUTH_URL = f"{BASE_URL}/auth"
PROJECTS_URL = f"{BASE_URL}/projects"

# --- Helper Functions ---
def random_string(length=8):
    """生成随机字符串"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def print_response(name, res):
    """格式化打印响应"""
    print(f"--- {name} ---")
    print(f"URL: {res.url}")
    print(f"Status Code: {res.status_code}")
    try:
        print(f"Response JSON: {json.dumps(res.json(), indent=2, ensure_ascii=False)}")
    except json.JSONDecodeError:
        print(f"Response Text: {res.text}")
    print("-" * (len(name) + 8))
    print()

# --- Main Test Logic ---
def main():
    session = requests.Session()
    
    # 1. 准备一个已认证的用户
    username = f"proj_tester_{random_string()}"
    email = f"{username}@example.com"
    password = "a_secure_password"
    
    print("Step 1: Registering and logging in a user...")
    
    # 注册
    reg_data = {"username": username, "email": email, "password": password, "full_name": "Project Tester"}
    res = session.post(f"{AUTH_URL}/register", json=reg_data)
    if res.status_code != 201:
        print_response("Register User FAILED", res)
        return
    print_response("Register User SUCCESS", res)
    
    # 登录
    login_data = {"username": username, "password": password}
    res = session.post(f"{AUTH_URL}/login", data=login_data)
    if res.status_code != 200:
        print_response("Login FAILED", res)
        return
    
    token = res.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    print("User is now authenticated.")
    print()

    # 2. CRUD 操作
    project_id = None
    
    # 创建项目
    print("Step 2: Creating a new project...")
    project_name = f"My Test Project {random_string()}"
    project_data = {"name": project_name, "description": "This is a test project for the API."}
    res = session.post(PROJECTS_URL, json=project_data)
    if res.status_code != 201:
        print_response("Create Project FAILED", res)
        return
    project_id = res.json()["id"]
    print_response(f"Create Project (ID: {project_id}) SUCCESS", res)
    assert res.json()["name"] == project_name

    # 获取所有项目
    print("Step 3: Getting all projects for the user...")
    res = session.get(PROJECTS_URL)
    if res.status_code != 200:
        print_response("Get All Projects FAILED", res)
        return
    print_response("Get All Projects SUCCESS", res)
    assert len(res.json()) > 0
    assert any(p["id"] == project_id for p in res.json())

    # 获取单个项目
    print(f"Step 4: Getting the specific project (ID: {project_id})...")
    res = session.get(f"{PROJECTS_URL}/{project_id}")
    if res.status_code != 200:
        print_response("Get Single Project FAILED", res)
        return
    print_response("Get Single Project SUCCESS", res)
    assert res.json()["id"] == project_id

    # 更新项目
    print(f"Step 5: Updating the project (ID: {project_id})...")
    updated_description = "This is the updated description."
    update_data = {"description": updated_description}
    res = session.put(f"{PROJECTS_URL}/{project_id}", json=update_data)
    if res.status_code != 200:
        print_response("Update Project FAILED", res)
        return
    print_response("Update Project SUCCESS", res)
    assert res.json()["description"] == updated_description
    
    # 再次获取以验证更新
    res = session.get(f"{PROJECTS_URL}/{project_id}")
    assert res.json()["description"] == updated_description
    print("Update verified.")
    print()

    # 删除项目
    print(f"Step 6: Deleting the project (ID: {project_id})...")
    res = session.delete(f"{PROJECTS_URL}/{project_id}")
    if res.status_code != 204:
        print_response("Delete Project FAILED", res)
        return
    print(f"--- Delete Project SUCCESS (Status: {res.status_code}) ---")
    print()

    # 验证删除
    print(f"Step 7: Verifying deletion of project (ID: {project_id})...")
    res = session.get(f"{PROJECTS_URL}/{project_id}")
    if res.status_code != 404:
        print_response("Verify Deletion FAILED - Project still exists or wrong status code", res)
        return
    print("Deletion verified (Got 404 Not Found as expected).")
    print()

    print("✅ All project API tests passed! ✅")

if __name__ == "__main__":
    main() 