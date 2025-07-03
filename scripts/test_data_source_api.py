"""
测试数据源管理API
"""
import requests
import json
import os
import random
import string
from pathlib import Path

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
        # 避免打印文件内容
        response_json = res.json()
        if "content" in response_json:
            response_json["content"] = "[...content omitted...]"
        print(f"Response JSON: {json.dumps(response_json, indent=2, ensure_ascii=False)}")
    except json.JSONDecodeError:
        print(f"Response Text: {res.text}")
    print("-" * (len(name) + 8))
    print()

def create_dummy_file(filename="test.txt", content="hello world"):
    """创建一个用于上传的临时文件"""
    Path(filename).write_text(content, encoding='utf-8')
    return filename

# --- Main Test Logic ---
def main():
    session = requests.Session()
    
    # 1. 准备一个已认证的用户
    username = f"ds_tester_{random_string()}"
    email = f"{username}@example.com"
    password = "a_secure_password"
    
    print("Step 1: Registering and logging in a user...")
    
    reg_data = {"username": username, "email": email, "password": password, "full_name": "Data Source Tester"}
    res = session.post(f"{AUTH_URL}/register", json=reg_data)
    if res.status_code != 201:
        print_response("Register User FAILED", res)
        return
    
    login_data = {"username": username, "password": password}
    res = session.post(f"{AUTH_URL}/login", data=login_data)
    if res.status_code != 200:
        print_response("Login FAILED", res)
        return
    
    token = res.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    print("User is now authenticated.")
    print()

    # 2. 准备一个项目
    print("Step 2: Creating a project to host the data source...")
    project_name = f"Data Source Test Project {random_string()}"
    project_data = {"name": project_name}
    res = session.post(PROJECTS_URL, json=project_data)
    if res.status_code != 201:
        print_response("Create Project FAILED", res)
        return
    project_id = res.json()["id"]
    print(f"Project created with ID: {project_id}")
    print()

    # 3. 数据源操作
    ds_id = None
    dummy_filename = "upload_test.txt"
    
    # 上传数据源
    print(f"Step 3: Uploading a data source to project {project_id}...")
    create_dummy_file(dummy_filename, content=f"some test data {random_string()}")
    with open(dummy_filename, "rb") as f:
        upload_url = f"{PROJECTS_URL}/{project_id}/datasources/upload"
        res = session.post(upload_url, files={"file": (dummy_filename, f, "text/plain")})
    
    # 清理临时文件
    Path(dummy_filename).unlink()

    if res.status_code != 201:
        print_response("Upload Data Source FAILED", res)
        return
    ds_id = res.json()["id"]
    print_response(f"Upload Data Source (ID: {ds_id}) SUCCESS", res)
    assert res.json()["name"] == dummy_filename

    # 列出数据源
    print(f"Step 4: Listing data sources for project {project_id}...")
    list_url = f"{PROJECTS_URL}/{project_id}/datasources"
    res = session.get(list_url)
    if res.status_code != 200:
        print_response("List Data Sources FAILED", res)
        return
    print_response("List Data Sources SUCCESS", res)
    assert len(res.json()) > 0
    assert any(ds["id"] == ds_id for ds in res.json())

    # 删除数据源
    print(f"Step 5: Deleting data source {ds_id}...")
    delete_url = f"{PROJECTS_URL}/{project_id}/datasources/{ds_id}"
    res = session.delete(delete_url)
    if res.status_code != 204:
        print_response("Delete Data Source FAILED", res)
        return
    print(f"--- Delete Data Source SUCCESS (Status: {res.status_code}) ---")
    print()

    # 验证删除
    print(f"Step 6: Verifying deletion of data source {ds_id}...")
    res = session.get(list_url)
    if res.status_code == 200 and not any(ds["id"] == ds_id for ds in res.json()):
        print("Deletion verified (Data source no longer in list).")
    else:
        print_response("Verify Deletion FAILED", res)
        return
    print()

    print("✅ All data source API tests passed! ✅")

if __name__ == "__main__":
    main() 