#!/usr/bin/env python3
"""
测试项目创建功能的脚本
"""
import requests
import json

# API基础URL
BASE_URL = "http://localhost:8008/api/v1"

def test_login():
    """测试登录功能"""
    print("1. 测试登录...")
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/token",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        print(f"登录响应状态: {response.status_code}")
        if response.status_code == 200:
            token_data = response.json()
            print(f"登录成功，获取token: {token_data.get('access_token', 'N/A')[:20]}...")
            return token_data.get('access_token')
        else:
            print(f"登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"登录请求失败: {e}")
        return None

def test_create_project(token):
    """测试创建项目功能"""
    print("\n2. 测试创建项目...")
    if not token:
        print("没有有效的token，跳过项目创建测试")
        return
    
    project_data = {
        "name": "测试项目",
        "description": "这是一个用于测试的项目"
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/projects/",
            json=project_data,
            headers=headers
        )
        print(f"创建项目响应状态: {response.status_code}")
        if response.status_code == 201:
            project = response.json()
            print(f"项目创建成功: {json.dumps(project, indent=2, ensure_ascii=False)}")
            return project
        else:
            print(f"创建项目失败: {response.text}")
            return None
    except Exception as e:
        print(f"创建项目请求失败: {e}")
        return None

def test_get_projects(token):
    """测试获取项目列表功能"""
    print("\n3. 测试获取项目列表...")
    if not token:
        print("没有有效的token，跳过项目列表测试")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/projects/",
            headers=headers
        )
        print(f"获取项目列表响应状态: {response.status_code}")
        if response.status_code == 200:
            projects = response.json()
            print(f"项目列表: {json.dumps(projects, indent=2, ensure_ascii=False)}")
            return projects
        else:
            print(f"获取项目列表失败: {response.text}")
            return None
    except Exception as e:
        print(f"获取项目列表请求失败: {e}")
        return None

def main():
    print("开始测试项目创建功能...")
    print("=" * 50)
    
    # 测试登录
    token = test_login()
    
    # 测试创建项目
    project = test_create_project(token)
    
    # 测试获取项目列表
    projects = test_get_projects(token)
    
    print("\n" + "=" * 50)
    print("测试完成!")

if __name__ == "__main__":
    main() 