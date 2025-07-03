"""
测试项目管理API
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "demo"
PASSWORD = "demo123"

def login():
    """登录并获取token"""
    print("🔐 登录...")
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": USERNAME, "password": PASSWORD}
    )
    resp.raise_for_status()
    token = resp.json()["access_token"]
    print("✅ 登录成功")
    return {"Authorization": f"Bearer {token}"}

def main():
    """主测试函数"""
    try:
        headers = login()
        project_id = None
        
        # 1. 创建项目
        print("\n🏗️ 1. 创建新项目...")
        project_data = {
            "name": "我的第一个AI项目",
            "description": "用于测试项目API的描述"
        }
        create_resp = requests.post(f"{BASE_URL}/projects", headers=headers, json=project_data)
        create_resp.raise_for_status()
        created_project = create_resp.json()
        project_id = created_project["id"]
        print(f"✅ 项目创建成功 (ID: {project_id})")
        print(json.dumps(created_project, indent=2, ensure_ascii=False))

        # 2. 获取所有项目
        print("\n📋 2. 获取所有项目...")
        list_resp = requests.get(f"{BASE_URL}/projects", headers=headers)
        list_resp.raise_for_status()
        projects = list_resp.json()
        print(f"✅ 成功获取 {len(projects)} 个项目")
        assert any(p['id'] == project_id for p in projects), "新创建的项目不在列表中"
        print("✅ 验证新项目存在于列表中")

        # 3. 更新项目
        print(f"\n✏️ 3. 更新项目 (ID: {project_id})...")
        update_data = {
            "name": "更新后的AI项目",
            "description": "这是一个更新后的描述。",
            "status": "archived"
        }
        update_resp = requests.put(f"{BASE_URL}/projects/{project_id}", headers=headers, json=update_data)
        update_resp.raise_for_status()
        updated_project = update_resp.json()
        print("✅ 项目更新成功")
        print(json.dumps(updated_project, indent=2, ensure_ascii=False))
        assert updated_project["name"] == "更新后的AI项目"
        assert updated_project["status"] == "archived"
        
        # 4. 获取单个项目
        print(f"\nℹ️ 4. 获取单个项目 (ID: {project_id})...")
        get_resp = requests.get(f"{BASE_URL}/projects/{project_id}", headers=headers)
        get_resp.raise_for_status()
        single_project = get_resp.json()
        print("✅ 获取单个项目成功")
        assert single_project["id"] == project_id
        
        # 5. 删除项目
        print(f"\n🗑️ 5. 删除项目 (ID: {project_id})...")
        delete_resp = requests.delete(f"{BASE_URL}/projects/{project_id}", headers=headers)
        delete_resp.raise_for_status()
        print("✅ 项目删除成功 (状态码: 204)")

        # 6. 验证删除
        print("\n❓ 6. 验证项目是否已删除...")
        get_deleted_resp = requests.get(f"{BASE_URL}/projects/{project_id}", headers=headers)
        assert get_deleted_resp.status_code == 404, f"项目未被删除，返回了 {get_deleted_resp.status_code}"
        print("✅ 验证成功 (获取已删除项目返回 404)")

        print("\n✨✨✨ 所有项目API测试通过! ✨✨✨")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ API请求失败: {e}")
        if e.response is not None:
            print(f"   响应内容: {e.response.text}")
    except Exception as e:
        print(f"\n❌ 测试过程中出现未知错误: {e}")

if __name__ == "__main__":
    main() 