#!/usr/bin/env python3
"""
音频增强功能测试脚本
用于测试新实现的AudioEnhancementService功能
"""

import sys
import os
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
import tempfile

# 添加backend路径
sys.path.append(str(Path(__file__).parent / "backend"))

def generate_test_audio():
    """生成包含噪声的测试音频文件"""
    print("🎵 生成测试音频文件...")
    
    # 生成5秒的正弦波信号（440Hz A音）
    duration = 5.0
    sample_rate = 16000
    t = np.linspace(0, duration, int(duration * sample_rate), False)
    
    # 创建音调信号
    frequency = 440.0  # A4音符
    signal = 0.3 * np.sin(2 * np.pi * frequency * t)
    
    # 添加一些谐波使声音更丰富
    signal += 0.1 * np.sin(2 * np.pi * frequency * 2 * t)  # 第二谐波
    signal += 0.05 * np.sin(2 * np.pi * frequency * 3 * t)  # 第三谐波
    
    # 添加白噪声
    noise_level = 0.1
    noise = noise_level * np.random.randn(len(signal))
    noisy_signal = signal + noise
    
    # 保存测试音频
    test_file = "test_audio_noisy.wav"
    sf.write(test_file, noisy_signal, sample_rate)
    print(f"✅ 测试音频已生成: {test_file}")
    
    return test_file, sample_rate

def test_audio_enhancement():
    """测试音频增强功能"""
    try:
        # 导入音频增强服务
        from backend.services.audio_enhancement import AudioEnhancementService
        
        print("🚀 初始化音频增强服务...")
        enhancer = AudioEnhancementService()
        
        # 生成测试音频
        test_file, sr = generate_test_audio()
        test_path = Path(test_file)
        
        print("🔍 分析原始音频...")
        # 加载原始音频
        original_audio, _ = enhancer.load_audio(test_path)
        print(f"原始音频长度: {len(original_audio)} 样本")
        print(f"原始音频时长: {len(original_audio) / sr:.2f} 秒")
        
        # 分析噪声水平
        print("\n📊 噪声水平分析...")
        noise_analysis = enhancer.analyze_noise_level(test_path)
        print(f"噪声水平: {noise_analysis['noise_level']:.4f}")
        print(f"信噪比估计: {noise_analysis['snr_estimate']:.2f} dB")
        print(f"质量评估: {noise_analysis['quality_assessment']}")
        
        # 测试不同的增强算法
        print("\n🔧 测试音频增强算法...")
        
        # 1. 谱减法去噪
        print("1️⃣ 测试谱减法去噪...")
        enhanced_spectral = enhancer.spectral_subtraction(original_audio, sr)
        print(f"谱减法处理后长度: {len(enhanced_spectral)} 样本")
        
        # 2. 带通滤波
        print("2️⃣ 测试带通滤波...")
        filtered_audio = enhancer.apply_bandpass_filter(original_audio, sr)
        print(f"滤波后长度: {len(filtered_audio)} 样本")
        
        # 3. 音频标准化
        print("3️⃣ 测试音频标准化...")
        normalized_audio = enhancer.normalize_audio(original_audio)
        print(f"标准化后最大值: {np.max(np.abs(normalized_audio)):.4f}")
        
        # 4. 完整增强管道
        print("\n🎯 测试完整增强管道...")
        pipeline_result = enhancer.enhance_audio_pipeline(
            test_path,
            algorithms=['spectral_subtraction', 'bandpass_filter', 'normalize']
        )
        
        if pipeline_result['success']:
            enhanced_path = pipeline_result['enhanced_audio_path']
            print(f"✅ 增强音频已保存: {enhanced_path}")
            print(f"处理时间: {pipeline_result['processing_time']:.2f} 秒")
            print(f"增强算法: {', '.join(pipeline_result['algorithms_applied'])}")
            
            # 保存增强后的音频用于对比
            print("\n📁 保存音频文件用于对比...")
            enhanced_audio, _ = enhancer.load_audio(Path(enhanced_path))
            sf.write("test_audio_enhanced.wav", enhanced_audio, sr)
            print("✅ 增强音频已另存为: test_audio_enhanced.wav")
            
            # 计算增强效果统计
            print("\n📈 增强效果统计:")
            original_rms = np.sqrt(np.mean(original_audio ** 2))
            enhanced_rms = np.sqrt(np.mean(enhanced_audio ** 2))
            print(f"原始音频RMS: {original_rms:.4f}")
            print(f"增强音频RMS: {enhanced_rms:.4f}")
            print(f"RMS改善比例: {enhanced_rms/original_rms:.2f}x")
            
        else:
            print(f"❌ 增强管道失败: {pipeline_result.get('error', '未知错误')}")
        
        # 清理临时文件
        print("\n🧹 清理临时文件...")
        if test_path.exists():
            test_path.unlink()
        if 'enhanced_path' in locals() and Path(enhanced_path).exists():
            Path(enhanced_path).unlink()
        
        print("✅ 音频增强功能测试完成！")
        return True
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保后端环境已正确配置")
        return False
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gpu_audio_processing():
    """测试GPU音频处理能力"""
    try:
        import torch
        print(f"\n🔍 GPU环境检测:")
        print(f"PyTorch版本: {torch.__version__}")
        print(f"CUDA可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA版本: {torch.version.cuda}")
            print(f"GPU设备数量: {torch.cuda.device_count()}")
            print(f"当前GPU: {torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else 'None'}")
        return torch.cuda.is_available()
    except Exception as e:
        print(f"❌ GPU测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🎵 多模态智能数据分析平台 - 音频增强功能测试")
    print("=" * 60)
    
    # 测试GPU环境
    gpu_available = test_gpu_audio_processing()
    
    # 测试音频增强功能
    print("\n" + "=" * 60)
    success = test_audio_enhancement()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 所有测试通过！音频增强功能运行正常。")
        if gpu_available:
            print("🚀 GPU加速环境已就绪，可获得最佳性能。")
    else:
        print("❌ 测试失败，请检查错误信息并修复问题。")
    
    print("\n📝 测试文件说明:")
    print("- test_audio_noisy.wav: 原始包含噪声的测试音频")
    print("- test_audio_enhanced.wav: 经过增强处理的音频")
    print("可以使用音频播放器对比两个文件的音质差异。") 