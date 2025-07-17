#!/usr/bin/env python3

"""
测试Docker容器中的文本优化服务
"""

import subprocess
import sys

def test_container_services():
    """测试容器中的服务"""
    
    # 测试脚本
    test_script = '''
import sys
sys.path.append("/app")

print("🔍 测试文本优化服务...")
try:
    from backend.services.text_optimization_service import TextOptimizationService
    print("✅ TextOptimizationService 导入成功")
    
    # 初始化服务
    optimizer = TextOptimizationService()
    print("✅ TextOptimizationService 初始化成功")
    
    # 测试处理
    test_text = "行行行行行行行行行行行行行行行行行行行行"
    result = optimizer.optimize_speech_text(test_text, "zh")
    print(f"📝 优化结果: {result.get('success', False)}")
    print(f"📝 优化文本: {result.get('optimized_text', '')[:50]}...")
    
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print()
print("🔍 检查 tasks.py 文件...")
try:
    with open("/app/backend/processing/tasks.py", "r") as f:
        content = f.read()
        if "text_optimization_result = None" in content:
            print("✅ 在 tasks.py 中找到文本优化代码")
        else:
            print("❌ 在 tasks.py 中没有找到文本优化代码")
            
        if "🧠 开始智能文本优化" in content:
            print("✅ 找到文本优化日志标记")
        else:
            print("❌ 没有找到文本优化日志标记")
            
except Exception as e:
    print(f"❌ 读取 tasks.py 失败: {e}")
'''
    
    # 执行测试
    cmd = f'docker-compose exec backend python3 -c "{test_script}"'
    
    print("执行容器测试...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        print("测试结果:")
        print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("❌ 测试超时")
        return False
    except Exception as e:
        print(f"❌ 执行测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_container_services()
    sys.exit(0 if success else 1) 