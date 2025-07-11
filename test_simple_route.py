#!/usr/bin/env python3
"""
简单的路由测试
"""

import requests

API_BASE = "http://localhost:8008/api/v1"

def test_route():
    """测试路由是否工作"""
    try:
        # 测试根路径
        response = requests.get(f"{API_BASE}/")
        print(f"根路径状态: {response.status_code}")
        
        # 测试项目路径
        response = requests.get(f"{API_BASE}/projects/")
        print(f"项目路径状态: {response.status_code}")
        
        # 测试数据源路径（应该返回401未授权）
        response = requests.get(f"{API_BASE}/projects/1/datasources/")
        print(f"数据源路径状态: {response.status_code}")
        
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    test_route() 