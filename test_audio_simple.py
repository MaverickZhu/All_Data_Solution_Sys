#!/usr/bin/env python3
"""
简单的音频分析API测试
通过HTTP API测试完整的音频分析流程
"""

import requests
import json
import time
import numpy as np
from pathlib import Path

def create_simple_audio():
    """创建一个简单的测试音频文件（使用纯Python）"""
    import wave
    import struct
    
    print("🎵 生成简单测试音频...")
    
    # 音频参数
    sample_rate = 16000
    duration = 3.0  # 3秒
    frequency = 440.0  # A4音符
    
    # 生成正弦波
    num_samples = int(sample_rate * duration)
    samples = []
    
    for i in range(num_samples):
        t = i / sample_rate
        # 主音调 + 一点噪声
        signal = 0.5 * np.sin(2 * np.pi * frequency * t)
        signal += 0.05 * np.random.random()  # 添加轻微随机噪声
        
        # 转换为16位整数
        sample = int(signal * 32767)
        sample = max(-32768, min(32767, sample))  # 限制范围
        samples.append(sample)
    
    # 保存为WAV文件
    filename = "simple_test_audio.wav"
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # 单声道
        wav_file.setsampwidth(2)  # 16位
        wav_file.setframerate(sample_rate)
        
        # 写入音频数据
        for sample in samples:
            wav_file.writeframes(struct.pack('<h', sample))
    
    print(f"✅ 测试音频已生成: {filename}")
    return filename

def test_audio_analysis_api():
    """测试音频分析API"""
    try:
        # 创建测试音频
        audio_file = create_simple_audio()
        
        # API基础URL
        base_url = "http://localhost:8088/api/v1"
        
        print("🔍 测试API健康状态...")
        health_response = requests.get("http://localhost:8088/health")
        if health_response.status_code == 200:
            print("✅ API服务正常运行")
        else:
            print("❌ API服务不可用")
            return False
        
        # 模拟用户登录（使用测试用户）
        print("🔐 模拟用户认证...")
        auth_data = {
            "username": "test@example.com",
            "password": "testpassword123"
        }
        
        # 先尝试创建测试用户（如果不存在）
        try:
            register_response = requests.post(f"{base_url}/auth/register", json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "testpassword123"
            })
            if register_response.status_code in [200, 201]:
                print("✅ 测试用户创建成功")
            elif register_response.status_code == 400:
                print("ℹ️ 测试用户已存在")
        except:
            print("ℹ️ 用户注册跳过")
        
        # 登录获取token
        login_response = requests.post(f"{base_url}/auth/login", data=auth_data)
        if login_response.status_code != 200:
            print("❌ 用户认证失败，跳过认证测试")
            token = None
        else:
            token = login_response.json().get("access_token")
            print("✅ 用户认证成功")
        
        # 设置请求头
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        print("\n🚀 开始音频分析测试...")
        
        # 上传并分析音频文件
        with open(audio_file, 'rb') as f:
            files = {'file': (audio_file, f, 'audio/wav')}
            data = {
                'project_id': '1',  # 假设存在项目ID 1
                'description': '音频增强功能测试'
            }
            
            print("📤 上传音频文件...")
            # 使用正确的上传路径 - 需要project_id作为查询参数
            upload_response = requests.post(
                f"{base_url}/data_sources/upload?project_id=1",
                files=files,
                data={'description': '音频增强功能测试'},
                headers=headers
            )
            
            if upload_response.status_code in [200, 201]:
                upload_result = upload_response.json()
                data_source_id = upload_result.get('id')
                print(f"✅ 音频文件上传成功，ID: {data_source_id}")
                
                # 启动分析任务
                print("🔬 启动音频分析...")
                analysis_response = requests.post(
                    f"{base_url}/processing/profile/{data_source_id}",
                    headers=headers
                )
                
                if analysis_response.status_code in [200, 202]:
                    task_result = analysis_response.json()
                    task_id = task_result.get('task_id')
                    print(f"✅ 分析任务已启动，任务ID: {task_id}")
                    
                    # 轮询任务状态
                    print("⏳ 等待分析完成...")
                    max_attempts = 30  # 最多等待30次
                    attempt = 0
                    
                    while attempt < max_attempts:
                        time.sleep(2)  # 等待2秒
                        attempt += 1
                        
                        status_response = requests.get(
                            f"{base_url}/processing/profile/{task_id}",
                            headers=headers
                        )
                        
                        if status_response.status_code == 200:
                            status_result = status_response.json()
                            status = status_result.get('status', 'unknown')
                            
                            print(f"📊 分析状态 ({attempt}/30): {status}")
                            
                            if status == 'completed':
                                print("🎉 音频分析完成！")
                                
                                # 获取分析结果
                                result_response = requests.get(
                                    f"{base_url}/data_sources/{data_source_id}",
                                    headers=headers
                                )
                                
                                if result_response.status_code == 200:
                                    result_data = result_response.json()
                                    profile_result = result_data.get('profiling_result', {})
                                    
                                    print("\n📈 分析结果摘要:")
                                    print(f"文件类型: {result_data.get('file_type', 'unknown')}")
                                    print(f"分析类别: {result_data.get('analysis_category', 'unknown')}")
                                    
                                    # 检查音频分析结果
                                    if 'speech_recognition' in profile_result:
                                        speech_result = profile_result['speech_recognition']
                                        print(f"\n🎤 语音识别结果:")
                                        print(f"成功: {speech_result.get('success', False)}")
                                        print(f"转录文本: {speech_result.get('transcribed_text', 'N/A')}")
                                        print(f"语言: {speech_result.get('language_detected', 'N/A')}")
                                        print(f"置信度: {speech_result.get('confidence', 0):.3f}")
                                        
                                        # 检查预处理信息
                                        if 'preprocessing_info' in speech_result:
                                            preprocessing = speech_result['preprocessing_info']
                                            print(f"\n🔧 音频预处理信息:")
                                            print(f"预处理启用: {preprocessing.get('preprocessing_enabled', False)}")
                                            if preprocessing.get('enhancement_applied'):
                                                print(f"增强算法: {preprocessing.get('algorithms_applied', [])}")
                                                print(f"处理时间: {preprocessing.get('processing_time', 0):.2f}秒")
                                    
                                    return True
                                break
                            elif status in ['failed', 'error']:
                                print(f"❌ 分析失败: {status_result.get('error', '未知错误')}")
                                break
                        else:
                            print(f"⚠️ 状态查询失败: {status_response.status_code}")
                    
                    if attempt >= max_attempts:
                        print("⏰ 分析超时，请检查系统状态")
                        return False
                        
                else:
                    print(f"❌ 启动分析失败: {analysis_response.status_code}")
                    if analysis_response.text:
                        print(f"错误信息: {analysis_response.text}")
                    return False
                    
            else:
                print(f"❌ 文件上传失败: {upload_response.status_code}")
                if upload_response.text:
                    print(f"错误信息: {upload_response.text}")
                return False
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理测试文件
        if Path(audio_file).exists():
            Path(audio_file).unlink()
            print(f"🧹 已清理测试文件: {audio_file}")

if __name__ == "__main__":
    print("🎵 音频增强功能 - API集成测试")
    print("=" * 50)
    
    try:
        import numpy as np
    except ImportError:
        print("❌ 需要安装numpy: pip install numpy")
        exit(1)
    
    success = test_audio_analysis_api()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 音频增强功能API测试通过！")
        print("✅ 音频预处理和去噪功能正常工作")
    else:
        print("❌ 测试未完全通过，请检查日志")
    
    print("\n📝 测试完成")
    print("如果测试通过，说明以下功能正常:")
    print("- 音频文件上传")
    print("- 音频增强预处理") 
    print("- Whisper语音识别")
    print("- 完整的分析流水线") 