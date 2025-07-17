#!/usr/bin/env python3
"""
文本优化服务测试脚本
用于验证语音识别后的文本优化功能
"""

import sys
import os
sys.path.append('./backend')

from backend.services.text_optimization_service import TextOptimizationService

def test_text_optimization():
    """测试文本优化功能"""
    
    # 模拟语音识别的原始输出（类似于您提供的截图中的文本）
    test_text = "运行工作搭建现场指挥部以实现以实现这个叫什么重点的领导人要关上呢啊呢好的好我现在发给你呢我找个阿我没问他更我就在这个问题我也不好意思说呢啊呢那都没换网呢这是呢我们平时开会也没换这个阿那就感这个走流程发给大家那还还设计给我学习好行行行行行行行行行行行行行行行行行行行行行行行行行行行行行行行行行行行行行行行行行行行行行行行行行行"
    
    print("🧪 文本优化服务测试")
    print("=" * 60)
    
    # 初始化文本优化服务
    optimizer = TextOptimizationService()
    
    print(f"📝 原始文本 ({len(test_text)} 字符):")
    print(f'"{test_text}"')
    print()
    
    # 进行文本优化
    print("🔄 正在进行文本优化...")
    result = optimizer.optimize_speech_text(test_text, language='zh')
    
    if result.get('success'):
        print("✅ 文本优化成功!")
        print()
        
        print(f"✨ 优化后文本 ({len(result['optimized_text'])} 字符):")
        print(f'"{result["optimized_text"]}"')
        print()
        
        # 显示应用的改进
        if result.get('improvements'):
            print("🔧 应用的改进:")
            for i, improvement in enumerate(result['improvements'], 1):
                print(f"  {i}. {improvement}")
            print()
        
        # 显示统计信息
        if result.get('statistics'):
            stats = result['statistics']
            print("📊 优化统计:")
            print(f"  • 原始字数: {stats.get('original_word_count', 0)}")
            print(f"  • 优化字数: {stats.get('optimized_word_count', 0)}")
            print(f"  • 句子数量: {stats.get('sentence_count', 0)}")
            print(f"  • 段落数量: {stats.get('paragraph_count', 0)}")
            print(f"  • 长度变化比: {stats.get('length_change_ratio', 1.0):.2f}")
            print(f"  • 可读性改善: {'是' if stats.get('readability_improved') else '否'}")
            print()
        
        # 显示分句结果
        if result.get('sentences'):
            print("🔤 分句结果:")
            for i, sentence in enumerate(result['sentences'], 1):
                print(f"  {i}. {sentence}")
            print()
        
        # 显示分段结果
        if result.get('paragraphs'):
            print("📄 分段结果:")
            for i, paragraph in enumerate(result['paragraphs'], 1):
                print(f"  段落 {i}: {len(paragraph)} 句")
                for j, sentence in enumerate(paragraph, 1):
                    print(f"    {i}.{j} {sentence}")
            print()
        
    else:
        print("❌ 文本优化失败!")
        print(f"错误: {result.get('error', '未知错误')}")
    
    print("=" * 60)
    print("测试完成! 🎉")

if __name__ == "__main__":
    test_text_optimization() 