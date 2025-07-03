"""
测试数据源管理API
"""
import requests
import json
import os

BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "demo"
PASSWORD = "demo123"

def login():
    """登录并获取token"""
    print("🔐 登录...")
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/login",
            data={"username": USERNAME, "password": PASSWORD}
        )
        resp.raise_for_status()
        token = resp.json()["access_token"]
        print("✅ 登录成功")
        return {"Authorization": f"Bearer {token}"}
    except requests.exceptions.RequestException as e:
        print(f"❌ 登录失败: {e}")
        exit()

def create_project(headers):
    """创建一个测试项目"""
    print("\n🏗️ 创建测试项目...")
    project_data = {"name": "数据源测试项目", "description": "一个用于测试数据源的临时项目"}
    try:
        resp = requests.post(f"{BASE_URL}/projects", headers=headers, json=project_data)
        resp.raise_for_status()
        project_id = resp.json()["id"]
        print(f"✅ 项目创建成功 (ID: {project_id})")
        return project_id
    except requests.exceptions.RequestException as e:
        print(f"❌ 创建项目失败: {e.response.text}")
        exit()

def create_dummy_file(filename="test_upload.csv"):
    """创建一个用于上传的临时文件"""
    with open(filename, "w") as f:
        f.write("col1,col2,col3\n")
        f.write("1,2,3\n")
        f.write("4,5,6\n")
    return filename

def main():
    """主测试函数"""
    headers = login()
    project_id = create_project(headers)
    dummy_file = create_dummy_file()
    ds_id = None
    
    try:
        # 1. 上传文件
        print(f"\n🚀 1. 上传文件到项目 (ID: {project_id})...")
        with open(dummy_file, "rb") as f:
            files = {"file": (os.path.basename(dummy_file), f, "text/csv")}
            upload_url = f"{BASE_URL}/projects/{project_id}/datasources/upload"
            resp = requests.post(upload_url, headers=headers, files=files)
            resp.raise_for_status()
            uploaded_ds = resp.json()
            ds_id = uploaded_ds["id"]
            print(f"✅ 文件上传成功 (数据源ID: {ds_id})")
            assert uploaded_ds["name"] == dummy_file
            assert uploaded_ds["project_id"] == project_id

        # 2. 列出数据源
        print(f"\n📋 2. 列出项目 (ID: {project_id}) 的数据源...")
        list_url = f"{BASE_URL}/projects/{project_id}/datasources"
        resp = requests.get(list_url, headers=headers)
        resp.raise_for_status()
        data_sources = resp.json()
        print(f"✅ 成功获取 {len(data_sources)} 个数据源")
        assert any(ds['id'] == ds_id for ds in data_sources), "新上传的数据源不在列表中"
        print("✅ 验证新数据源存在于列表中")

        # 3. 删除数据源
        print(f"\n🗑️ 3. 删除数据源 (ID: {ds_id})...")
        delete_url = f"{BASE_URL}/projects/{project_id}/datasources/{ds_id}"
        resp = requests.delete(delete_url, headers=headers)
        resp.raise_for_status()
        print(f"✅ 数据源删除成功 (状态码: {resp.status_code})")

        # 4. 验证删除
        print(f"\n❓ 4. 验证数据源 (ID: {ds_id}) 是否已删除...")
        resp = requests.get(list_url, headers=headers)
        resp.raise_for_status()
        data_sources_after_delete = resp.json()
        assert not any(ds['id'] == ds_id for ds in data_sources_after_delete), "数据源未被成功删除"
        print("✅ 验证成功 (数据源已不在列表中)")
        
        print("\n✨✨✨ 所有数据源API测试通过! ✨✨✨")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ API请求失败: {e}")
        if e.response is not None:
            print(f"   响应内容: {e.response.text}")
    except Exception as e:
        print(f"\n❌ 测试过程中出现未知错误: {e}")
    finally:
        # 清理临时文件
        if os.path.exists(dummy_file):
            os.remove(dummy_file)
            print(f"\n🧹 清理临时文件: {dummy_file}")
        # 清理测试项目（可选）
        # requests.delete(f"{BASE_URL}/projects/{project_id}", headers=headers)

if __name__ == "__main__":
    main() 