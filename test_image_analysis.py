#!/usr/bin/env python3
"""
测试图像分析功能的脚本
"""
import sys
import os
import json
from pathlib import Path

# 添加后端路径到 Python path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.processing.tasks import perform_image_analysis

def test_image_analysis():
    """测试图像分析功能"""
    
    # 查找测试图像文件
    test_image_path = None
    possible_paths = [
        Path("uploads"),
        Path("backend/uploads"),
        Path("frontend/public"),
    ]
    
    for base_path in possible_paths:
        if base_path.exists():
            for image_file in base_path.glob("*.png"):
                test_image_path = image_file
                break
            if test_image_path:
                break
            for image_file in base_path.glob("*.jpg"):
                test_image_path = image_file
                break
            if test_image_path:
                break
    
    if not test_image_path:
        print("❌ 未找到测试图像文件")
        return False
    
    print(f"🔍 测试图像文件: {test_image_path}")
    
    try:
        # 执行图像分析
        result = perform_image_analysis(test_image_path)
        
        # 打印结果
        print("✅ 图像分析结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 验证结果结构
        if "analysis_type" in result and result["analysis_type"] == "image":
            print("✅ analysis_type 字段正确")
        else:
            print("❌ analysis_type 字段缺失或错误")
            return False
            
        if "image_properties" in result:
            print("✅ image_properties 字段存在")
            
            props = result["image_properties"]
            required_fields = ["dimensions", "format", "file_size_bytes", "phash"]
            
            for field in required_fields:
                if field in props:
                    print(f"✅ {field} 字段存在")
                else:
                    print(f"❌ {field} 字段缺失")
                    return False
                    
            # 检查 dimensions 结构
            if "dimensions" in props and "width" in props["dimensions"] and "height" in props["dimensions"]:
                print("✅ dimensions 结构正确")
            else:
                print("❌ dimensions 结构错误")
                return False
                
        else:
            print("❌ image_properties 字段缺失")
            return False
            
        print("🎉 所有测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 图像分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_image_analysis()
    sys.exit(0 if success else 1) 