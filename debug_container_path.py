#!/usr/bin/env python3

"""
调试脚本：验证Docker容器中的文本优化代码
"""

# 直接在容器中运行的测试脚本
container_test_script = """
cd /app
python3 -c "
print('🔍 检查文本优化服务...')
try:
    from backend.services.text_optimization_service import TextOptimizationService
    print('✅ TextOptimizationService 导入成功')
    
    # 测试初始化
    optimizer = TextOptimizationService()
    print('✅ TextOptimizationService 初始化成功')
    
    # 测试处理
    test_text = '行行行行行行行行行行行行行行行行行行行行'
    result = optimizer.optimize_speech_text(test_text, 'zh')
    print(f'📝 测试结果: {result.get(\"success\", False)}')
    print(f'📝 优化文本: {result.get(\"optimized_text\", \"\")}')
    print(f'📝 改进措施: {result.get(\"improvements\", [])}')
    
except Exception as e:
    print(f'❌ 错误: {e}')
    import traceback
    traceback.print_exc()

print()
print('🔍 检查 tasks.py 中的文本优化代码...')
with open('/app/backend/processing/tasks.py', 'r') as f:
    content = f.read()
    if 'text_optimization_result = None' in content:
        print('✅ 在 tasks.py 中找到文本优化代码')
        if '🧠 开始智能文本优化' in content:
            print('✅ 找到调试日志')
        else:
            print('❌ 没有找到调试日志')
    else:
        print('❌ 在 tasks.py 中没有找到文本优化代码')

print()
print('🔍 检查 perform_audio_analysis 函数...')
import re
pattern = r'def perform_audio_analysis.*?return.*?}'
matches = re.findall(pattern, content, re.DOTALL)
if matches:
    if 'text_optimization' in matches[0]:
        print('✅ perform_audio_analysis 函数包含 text_optimization')
    else:
        print('❌ perform_audio_analysis 函数不包含 text_optimization')
else:
    print('❌ 没有找到 perform_audio_analysis 函数')
"
"""

print("Docker容器调试脚本：")
print(container_test_script) 