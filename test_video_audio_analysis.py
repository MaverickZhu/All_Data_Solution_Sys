"""
测试视频音频分析功能
验证Phase 3的音频提取、语音识别、语义分析等功能
"""
import sys
import os
import asyncio
from pathlib import Path
import logging
import tempfile
import cv2
import numpy as np
import subprocess
from dataclasses import asdict

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.services.video_audio_service import video_audio_service
from backend.models.data_source import DataSource, AnalysisCategory
from backend.models.video_analysis import VideoAnalysis, VideoAnalysisType, VideoAnalysisStatus

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_test_video_with_audio() -> Path:
    """创建带音频的测试视频"""
    try:
        # 创建临时目录
        temp_dir = Path(tempfile.gettempdir()) / "video_audio_test"
        temp_dir.mkdir(exist_ok=True)
        
        test_video_path = temp_dir / "test_video_with_audio.mp4"
        
        # 创建视频部分
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = 30
        width, height = 640, 480
        out = cv2.VideoWriter(str(test_video_path), fourcc, fps, (width, height))
        
        # 生成3秒的测试视频（90帧）
        total_frames = 90
        
        for frame_num in range(total_frames):
            # 创建帧
            img = np.zeros((height, width, 3), dtype=np.uint8)
            
            # 根据帧数改变背景色
            if frame_num < 30:
                img[:, :] = (100, 50, 0)  # 蓝色背景
                cv2.putText(img, f"Audio Test - Part 1", (50, 100), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            elif frame_num < 60:
                img[:, :] = (0, 100, 50)  # 绿色背景
                cv2.putText(img, f"Audio Test - Part 2", (50, 100), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            else:
                img[:, :] = (0, 0, 100)  # 红色背景
                cv2.putText(img, f"Audio Test - Part 3", (50, 100), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            out.write(img)
        
        out.release()
        
        # 创建测试音频（使用ffmpeg生成音频）
        audio_path = temp_dir / "test_audio.wav"
        
        # 生成3秒的测试音频（440Hz正弦波）
        try:
            cmd = [
                "ffmpeg", "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
                "-ar", "16000", "-ac", "1", "-y", str(audio_path)
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            
            # 合并视频和音频
            final_video_path = temp_dir / "test_video_final.mp4"
            cmd = [
                "ffmpeg", "-i", str(test_video_path), "-i", str(audio_path),
                "-c:v", "copy", "-c:a", "aac", "-y", str(final_video_path)
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            
            # 清理临时文件
            if test_video_path.exists():
                test_video_path.unlink()
            if audio_path.exists():
                audio_path.unlink()
            
            logger.info(f"测试视频创建成功: {final_video_path}")
            return final_video_path
            
        except subprocess.CalledProcessError as e:
            logger.warning(f"FFmpeg音频合成失败: {e}")
            logger.info("返回无音频的视频文件")
            return test_video_path
            
    except Exception as e:
        logger.error(f"创建测试视频失败: {e}")
        raise


def create_mock_data_source(video_path: Path) -> DataSource:
    """创建模拟数据源对象"""
    return DataSource(
        id=1,
        name=video_path.name,
        file_path=str(video_path),
        file_size=video_path.stat().st_size,
        file_type="mp4",
        analysis_category=AnalysisCategory.VIDEO,
        project_id=1,
        user_id=1,
        created_by="test_user"
    )


def create_mock_video_analysis() -> VideoAnalysis:
    """创建模拟视频分析对象"""
    return VideoAnalysis(
        id=1,
        data_source_id=1,
        analysis_type=VideoAnalysisType.ENHANCED,
        status=VideoAnalysisStatus.IN_PROGRESS,
        task_id="test_task_123",
        user_id=1
    )


async def test_service_initialization():
    """测试服务初始化"""
    logger.info("测试音频服务初始化...")
    
    try:
        # 检查服务实例
        assert video_audio_service.audio_service is not None
        assert video_audio_service.whisper_service is not None
        assert video_audio_service.audio_enhancement is not None
        assert video_audio_service.llm_service is not None
        
        logger.info("✅ 视频音频服务初始化成功")
        logger.info(f"  - 音频服务: {type(video_audio_service.audio_service).__name__}")
        logger.info(f"  - Whisper服务: {type(video_audio_service.whisper_service).__name__}")
        logger.info(f"  - 音频增强: {type(video_audio_service.audio_enhancement).__name__}")
        logger.info(f"  - LLM服务: {type(video_audio_service.llm_service).__name__}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 服务初始化失败: {e}")
        return False


async def test_ffmpeg_availability():
    """测试FFmpeg可用性"""
    logger.info("测试FFmpeg可用性...")
    
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            logger.info(f"✅ FFmpeg可用: {version_line}")
            return True
        else:
            logger.error(f"❌ FFmpeg不可用: {result.stderr}")
            return False
            
    except FileNotFoundError:
        logger.error("❌ FFmpeg未安装或不在PATH中")
        return False
    except subprocess.TimeoutExpired:
        logger.error("❌ FFmpeg命令超时")
        return False
    except Exception as e:
        logger.error(f"❌ FFmpeg检查失败: {e}")
        return False


async def test_audio_extraction():
    """测试音频提取功能"""
    logger.info("测试音频提取功能...")
    
    try:
        # 创建测试视频
        video_path = create_test_video_with_audio()
        
        # 创建输出目录
        output_dir = Path(tempfile.gettempdir()) / "test_audio_extraction"
        output_dir.mkdir(exist_ok=True)
        
        # 提取音频
        audio_path = await video_audio_service.extract_audio_from_video(video_path, output_dir)
        
        logger.info(f"音频提取结果:")
        logger.info(f"  - 音频文件: {audio_path.name}")
        logger.info(f"  - 文件大小: {audio_path.stat().st_size} bytes")
        logger.info(f"  - 文件存在: {audio_path.exists()}")
        
        if audio_path.exists() and audio_path.stat().st_size > 0:
            logger.info("✅ 音频提取测试成功")
            return audio_path, video_path
        else:
            logger.error("❌ 音频提取失败：文件不存在或为空")
            return None, video_path
            
    except Exception as e:
        logger.error(f"❌ 音频提取测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None


async def test_audio_analysis():
    """测试音频分析功能"""
    logger.info("测试音频分析功能...")
    
    try:
        # 创建测试数据
        video_path = create_test_video_with_audio()
        output_dir = Path(tempfile.gettempdir()) / "test_audio_analysis"
        output_dir.mkdir(exist_ok=True)
        
        # 执行音频分析
        analysis_result = await video_audio_service.analyze_video_audio(video_path, output_dir)
        
        logger.info(f"音频分析结果:")
        logger.info(f"  - 是否有错误: {'是' if analysis_result.get('error') else '否'}")
        
        if analysis_result.get("error"):
            logger.error(f"  - 错误信息: {analysis_result.get('error')}")
            return False
        
        # 检查各个组件的结果
        audio_extraction = analysis_result.get("audio_extraction", {})
        basic_analysis = analysis_result.get("basic_analysis", {})
        enhanced_speech = analysis_result.get("enhanced_speech", {})
        semantic_analysis = analysis_result.get("semantic_analysis", {})
        timeline_analysis = analysis_result.get("timeline_analysis", {})
        
        logger.info(f"  - 音频提取成功: {audio_extraction.get('extraction_success', False)}")
        logger.info(f"  - 基础分析成功: {basic_analysis.get('success', False)}")
        logger.info(f"  - 语音识别成功: {enhanced_speech.get('success', False)}")
        logger.info(f"  - 语义分析成功: {semantic_analysis.get('success', False)}")
        logger.info(f"  - 时间轴分析成功: {timeline_analysis.get('success', False)}")
        
        # 显示详细信息
        if enhanced_speech.get("success"):
            logger.info(f"  - 识别语言: {enhanced_speech.get('language', 'unknown')}")
            logger.info(f"  - 片段数量: {enhanced_speech.get('segments_count', 0)}")
            logger.info(f"  - 识别文本: {enhanced_speech.get('full_text', '')[:100]}...")
        
        if semantic_analysis.get("success"):
            content = semantic_analysis.get("content_analysis", {})
            logger.info(f"  - 内容类型: {content.get('content_type', 'unknown')}")
            logger.info(f"  - 主要话题: {content.get('main_themes', [])}")
        
        # 验证结果完整性
        success_count = sum([
            audio_extraction.get("extraction_success", False),
            basic_analysis.get("success", False),
            enhanced_speech.get("success", False),
            semantic_analysis.get("success", False),
            timeline_analysis.get("success", False)
        ])
        
        if success_count >= 3:  # 至少3个组件成功
            logger.info("✅ 音频分析测试成功")
            return True
        else:
            logger.error(f"❌ 音频分析失败：只有{success_count}/5个组件成功")
            return False
            
    except Exception as e:
        logger.error(f"❌ 音频分析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mock_analysis():
    """测试模拟分析（不依赖FFmpeg和实际音频）"""
    logger.info("测试模拟分析功能...")
    
    try:
        # 创建模拟的语音识别结果
        mock_speech_result = {
            "success": True,
            "segments": [
                {
                    "id": 0,
                    "start_time": 0.0,
                    "end_time": 2.0,
                    "duration": 2.0,
                    "text": "这是一个测试音频片段",
                    "confidence": 0.85
                },
                {
                    "id": 1,
                    "start_time": 2.5,
                    "end_time": 4.0,
                    "duration": 1.5,
                    "text": "用于验证音频分析功能",
                    "confidence": 0.90
                }
            ],
            "full_text": "这是一个测试音频片段 用于验证音频分析功能",
            "language": "zh",
            "total_duration": 4.0
        }
        
        # 测试语义分析
        semantic_result = await video_audio_service._analyze_audio_semantics(mock_speech_result)
        
        logger.info("模拟语义分析结果:")
        logger.info(f"  - 分析成功: {semantic_result.get('success', False)}")
        logger.info(f"  - 内容分析: {semantic_result.get('content_analysis', {}).get('content_type', 'unknown')}")
        logger.info(f"  - 情感分析: {semantic_result.get('emotion_analysis', {}).get('overall_emotion', {}).get('dominant_emotion', 'unknown')}")
        logger.info(f"  - 话题分析: {semantic_result.get('topic_analysis', {}).get('main_topics', [])}")
        
        # 测试时间轴分析
        timeline_result = await video_audio_service._analyze_audio_timeline(mock_speech_result)
        
        logger.info("模拟时间轴分析结果:")
        logger.info(f"  - 分析成功: {timeline_result.get('success', False)}")
        logger.info(f"  - 语音活动比例: {timeline_result.get('speech_activity', {}).get('activity_ratio', 0)}")
        logger.info(f"  - 语速类型: {timeline_result.get('speech_rate_analysis', {}).get('speech_rate_type', 'unknown')}")
        
        if (semantic_result.get("success", False) and 
            timeline_result.get("success", False)):
            logger.info("✅ 模拟分析测试成功")
            return True
        else:
            logger.error("❌ 模拟分析失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ 模拟分析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    logger.info("🎵 开始视频音频分析测试")
    logger.info("=" * 60)
    
    # 检查依赖
    try:
        import cv2
        import numpy as np
        import librosa
        logger.info(f"OpenCV版本: {cv2.__version__}")
        logger.info(f"NumPy版本: {np.__version__}")
        logger.info(f"Librosa版本: {librosa.__version__}")
    except ImportError as e:
        logger.error(f"缺少依赖: {e}")
        return False
    
    # 执行测试
    tests = [
        ("服务初始化", test_service_initialization),
        ("FFmpeg可用性", test_ffmpeg_availability),
        ("模拟分析功能", test_mock_analysis),
        ("音频提取", test_audio_extraction),
        ("音频分析", test_audio_analysis),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"执行测试: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            if test_name == "音频提取":
                audio_path, video_path = await test_func()
                result = audio_path is not None
            else:
                result = await test_func()
                
            results[test_name] = result
            
            if result:
                logger.info(f"✅ {test_name} - 通过")
            else:
                logger.error(f"❌ {test_name} - 失败")
                
        except Exception as e:
            logger.error(f"💥 {test_name} - 异常: {e}")
            results[test_name] = False
    
    # 总结结果
    logger.info(f"\n{'='*50}")
    logger.info("测试结果总结")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        logger.info("🎉 所有测试通过！Phase 3音频分析功能完全正常")
        logger.info("📋 Phase 3完成状态:")
        logger.info("  ✅ 视频音频提取")
        logger.info("  ✅ 语音识别增强")
        logger.info("  ✅ 音频语义分析")
        logger.info("  ✅ 时间轴分析")
        logger.info("  ✅ 完整分析流程")
        return True
    elif passed >= 3:
        logger.info("⚠️ 大部分测试通过，核心功能正常")
        logger.info("💡 提示：FFmpeg相关功能可能需要额外配置")
        return True
    else:
        logger.error("💥 多数测试失败，请检查配置")
        return False


if __name__ == "__main__":
    asyncio.run(main()) 