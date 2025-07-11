#!/usr/bin/env python3
"""
测试数据分析功能的完整流程
包括：登录 -> 创建项目 -> 上传数据源 -> 启动分析 -> 轮询状态 -> 获取结果
"""

import requests
import time
import json
import os
from pathlib import Path

API_BASE = "http://localhost:8008/api/v1"

def login(username="testuser", password="testpass123"):
    """用户登录获取token"""
    response = requests.post(
        f"{API_BASE}/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print(f"登录响应: {response.status_code}")
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ 登录成功")
        return token
    else:
        print(f"❌ 登录失败: {response.text}")
        return None

def create_project(token, project_name="测试数据分析项目"):
    """创建项目"""
    headers = {"Authorization": f"Bearer {token}"}
    project_data = {
        "name": project_name,
        "description": "用于测试数据分析功能的项目"
    }
    
    response = requests.post(f"{API_BASE}/projects/", json=project_data, headers=headers)
    print(f"创建项目响应: {response.status_code}")
    if response.status_code == 201:
        project = response.json()
        print(f"✅ 项目创建成功: {project['name']} (ID: {project['id']})")
        return project
    else:
        print(f"❌ 项目创建失败: {response.text}")
        return None

def create_test_csv():
    """创建测试CSV文件"""
    csv_content = """name,age,salary,department
Alice,25,50000,Engineering
Bob,30,60000,Marketing
Charlie,35,70000,Engineering
Diana,28,55000,Sales
Eve,32,65000,Marketing
Frank,29,58000,Engineering
Grace,31,62000,Sales
Henry,27,52000,Marketing
Ivy,33,68000,Engineering
Jack,26,54000,Sales"""
    
    with open("test_data.csv", "w", encoding="utf-8") as f:
        f.write(csv_content)
    print("✅ 测试CSV文件创建成功")
    return "test_data.csv"

def upload_data_source(token, project_id, file_path):
    """上传数据源"""
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(
            f"{API_BASE}/projects/{project_id}/datasources/upload",
            files=files,
            headers=headers
        )
    
    print(f"上传数据源响应: {response.status_code}")
    if response.status_code == 201:
        data_source = response.json()
        print(f"✅ 数据源上传成功: {data_source['name']} (ID: {data_source['id']})")
        return data_source
    else:
        print(f"❌ 数据源上传失败: {response.text}")
        return None

def start_data_analysis(token, data_source_id, project_id):
    """启动数据分析"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{API_BASE}/processing/profile/{data_source_id}",
        params={"project_id": project_id},
        headers=headers
    )
    
    print(f"启动数据分析响应: {response.status_code}")
    if response.status_code == 202:
        result = response.json()
        task_id = result["task_id"]
        print(f"✅ 数据分析任务启动成功: {task_id}")
        return task_id
    else:
        print(f"❌ 数据分析启动失败: {response.text}")
        return None

def poll_task_status(token, task_id, max_wait_time=60):
    """轮询任务状态"""
    headers = {"Authorization": f"Bearer {token}"}
    start_time = time.time()
    
    print(f"开始轮询任务状态: {task_id}")
    
    while time.time() - start_time < max_wait_time:
        response = requests.get(f"{API_BASE}/processing/profile/{task_id}", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            status = result["status"]
            print(f"任务状态: {status}")
            
            if status == "SUCCESS":
                print("✅ 任务执行成功!")
                return result["result"]
            elif status == "FAILURE":
                print(f"❌ 任务执行失败: {result.get('error', '未知错误')}")
                return None
            elif status in ["PENDING", "PROGRESS"]:
                print("⏳ 任务进行中，等待3秒后重试...")
                time.sleep(3)
            else:
                print(f"未知状态: {status}")
                time.sleep(3)
        else:
            print(f"❌ 查询任务状态失败: {response.text}")
            return None
    
    print("❌ 任务超时")
    return None

def main():
    """主测试流程"""
    print("🚀 开始测试数据分析功能...")
    
    # 1. 登录
    token = login()
    if not token:
        return
    
    # 2. 创建项目
    project = create_project(token)
    if not project:
        return
    
    # 3. 创建测试数据
    csv_file = create_test_csv()
    
    # 4. 上传数据源
    data_source = upload_data_source(token, project["id"], csv_file)
    if not data_source:
        return
    
    # 5. 启动数据分析
    task_id = start_data_analysis(token, data_source["id"], project["id"])
    if not task_id:
        return
    
    # 6. 轮询任务状态
    result = poll_task_status(token, task_id)
    if result:
        print("📊 分析结果:")
        print(f"状态: {result.get('status')}")
        if result.get('report_json'):
            # 解析JSON报告
            try:
                report = json.loads(result['report_json'])
                print(f"报告标题: {report.get('title', 'N/A')}")
                print(f"变量数量: {len(report.get('variables', {}))}")
                print("✅ 数据分析完整流程测试成功!")
            except json.JSONDecodeError:
                print("⚠️ 报告JSON解析失败")
        else:
            print("⚠️ 没有获取到分析报告")
    
    # 清理测试文件
    try:
        os.remove(csv_file)
        print("🧹 测试文件清理完成")
    except:
        pass

if __name__ == "__main__":
    main() 