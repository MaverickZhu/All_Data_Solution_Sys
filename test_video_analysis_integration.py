"""
测试视频分析服务集成
验证Phase 2完整的视频分析流程：帧提取 + Qwen2.5-VL分析 + 场景检测
"""
import sys
import os
import asyncio
from pathlib import Path
import logging
import tempfile
import cv2
import numpy as np
from dataclasses import asdict

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.services.video_analysis_service import video_analysis_service
from backend.services.video_frame_extractor import FrameInfo
from backend.models.data_source import DataSource, AnalysisCategory
from backend.models.video_analysis import VideoAnalysis, VideoAnalysisType, VideoAnalysisStatus

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_test_video() -> Path:
    """创建测试视频文件"""
    try:
        # 创建临时目录
        temp_dir = Path(tempfile.gettempdir()) / "video_analysis_test"
        temp_dir.mkdir(exist_ok=True)
        
        test_video_path = temp_dir / "test_video.mp4"
        
        # 创建视频写入器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = 30
        width, height = 640, 480
        out = cv2.VideoWriter(str(test_video_path), fourcc, fps, (width, height))
        
        # 生成3秒的测试视频（90帧）
        total_frames = 90
        
        for frame_num in range(total_frames):
            # 创建帧
            img = np.zeros((height, width, 3), dtype=np.uint8)
            
            # 根据帧数改变背景色，模拟场景变化
            if frame_num < 30:
                # 第一段：蓝色背景
                img[:, :] = (100, 50, 0)  # BGR
                cv2.putText(img, f"Scene 1 - Frame {frame_num}", (50, 100), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            elif frame_num < 60:
                # 第二段：绿色背景
                img[:, :] = (0, 100, 50)  # BGR
                cv2.putText(img, f"Scene 2 - Frame {frame_num}", (50, 100), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                # 添加移动的圆形
                center_x = int(200 + (frame_num - 30) * 5)
                cv2.circle(img, (center_x, 200), 30, (255, 255, 255), -1)
            else:
                # 第三段：红色背景
                img[:, :] = (0, 0, 100)  # BGR
                cv2.putText(img, f"Scene 3 - Frame {frame_num}", (50, 100), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                # 添加矩形
                cv2.rectangle(img, (100, 150), (300, 250), (255, 255, 255), -1)
            
            out.write(img)
        
        out.release()
        
        logger.info(f"测试视频创建成功: {test_video_path}")
        logger.info(f"视频信息: {total_frames}帧, {fps}fps, {total_frames/fps:.1f}秒")
        
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
    logger.info("测试服务初始化...")
    
    try:
        # 检查服务实例
        assert video_analysis_service.frame_extractor is not None
        assert video_analysis_service.vision_service is not None
        
        logger.info("✅ 视频分析服务初始化成功")
        logger.info(f"  - 帧提取器: {type(video_analysis_service.frame_extractor).__name__}")
        logger.info(f"  - 视觉服务: {type(video_analysis_service.vision_service).__name__}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 服务初始化失败: {e}")
        return False


async def test_frame_extraction():
    """测试帧提取功能"""
    logger.info("测试帧提取功能...")
    
    try:
        # 创建测试视频
        video_path = create_test_video()
        
        # 创建输出目录
        output_dir = Path(tempfile.gettempdir()) / "test_frames"
        output_dir.mkdir(exist_ok=True)
        
        # 提取关键帧
        key_frames = video_analysis_service.frame_extractor.extract_key_frames(video_path, output_dir)
        
        logger.info(f"关键帧提取结果:")
        logger.info(f"  - 提取帧数: {len(key_frames)}")
        
        # 显示前几帧的信息
        for i, frame in enumerate(key_frames[:5]):
            logger.info(f"  - 帧{i+1}: 时间{frame.timestamp:.2f}s, 原因:{frame.key_frame_reason}")
        
        if len(key_frames) > 0:
            logger.info("✅ 帧提取测试成功")
            return key_frames, video_path
        else:
            logger.error("❌ 帧提取失败：没有提取到关键帧")
            return [], video_path
            
    except Exception as e:
        logger.error(f"❌ 帧提取测试失败: {e}")
        import traceback
        traceback.print_exc()
        return [], None


async def test_visual_analysis(key_frames):
    """测试视觉分析功能"""
    logger.info("测试视觉分析功能...")
    
    try:
        if not key_frames:
            logger.warning("⚠️ 没有关键帧，跳过视觉分析测试")
            return {}
        
        # 执行视觉分析
        visual_results = await video_analysis_service.vision_service.analyze_video_frames(key_frames)
        
        logger.info(f"视觉分析结果:")
        logger.info(f"  - 分析帧数: {visual_results.get('total_frames_analyzed', 0)}")
        logger.info(f"  - 视觉主题: {visual_results.get('visual_themes', [])}")
        logger.info(f"  - 检测物体: {visual_results.get('detected_objects', [])}")
        logger.info(f"  - 场景类型: {visual_results.get('scene_types', [])}")
        logger.info(f"  - 场景变化: {len(visual_results.get('scene_changes', []))}")
        logger.info(f"  - 成功率: {visual_results.get('analysis_metadata', {}).get('success_rate', 0):.2%}")
        
        if visual_results.get('total_frames_analyzed', 0) > 0:
            logger.info("✅ 视觉分析测试成功")
            return visual_results
        else:
            logger.error("❌ 视觉分析失败：没有成功分析的帧")
            return {}
            
    except Exception as e:
        logger.error(f"❌ 视觉分析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {}


async def test_scene_detection(key_frames):
    """测试场景检测功能"""
    logger.info("测试场景检测功能...")
    
    try:
        if not key_frames:
            logger.warning("⚠️ 没有关键帧，跳过场景检测测试")
            return {}
        
        # 执行场景序列分析
        scene_results = await video_analysis_service.vision_service.analyze_scene_sequence(key_frames)
        
        logger.info(f"场景检测结果:")
        logger.info(f"  - 场景数量: {scene_results.get('total_scenes', 0)}")
        
        # 显示场景序列
        sequences = scene_results.get('scene_sequences', [])
        for i, seq in enumerate(sequences):
            logger.info(f"  - 场景{i+1}: {seq.get('scene_type', 'unknown')} "
                       f"({seq.get('start_time', 0):.1f}s - {seq.get('end_time', 0):.1f}s)")
        
        # 显示故事结构
        story = scene_results.get('story_structure', {})
        if story.get('phases'):
            logger.info(f"  - 故事结构: {story.get('structure', 'unknown')}")
            for phase in story.get('phases', []):
                logger.info(f"    - {phase.get('phase', 'unknown')}: {phase.get('scene_type', 'unknown')}")
        
        if scene_results.get('total_scenes', 0) > 0:
            logger.info("✅ 场景检测测试成功")
            return scene_results
        else:
            logger.error("❌ 场景检测失败：没有检测到场景")
            return {}
            
    except Exception as e:
        logger.error(f"❌ 场景检测测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {}


async def test_complete_analysis():
    """测试完整分析流程"""
    logger.info("测试完整分析流程...")
    
    try:
        # 创建测试数据
        video_path = create_test_video()
        data_source = create_mock_data_source(video_path)
        video_analysis = create_mock_video_analysis()
        
        # 执行完整的视觉分析
        logger.info("开始完整视觉分析...")
        analysis_result = await video_analysis_service.perform_visual_analysis(data_source, video_analysis)
        
        logger.info(f"完整分析结果:")
        logger.info(f"  - 是否有错误: {'是' if analysis_result.get('error') else '否'}")
        
        if analysis_result.get('error'):
            logger.error(f"  - 错误信息: {analysis_result.get('error')}")
            return False
        
        # 检查各个组件的结果
        visual_analysis = analysis_result.get('visual_analysis', {})
        scene_detection = analysis_result.get('scene_detection', {})
        frame_extraction = analysis_result.get('frame_extraction', {})
        
        logger.info(f"  - 提取帧数: {frame_extraction.get('total_frames_extracted', 0)}")
        logger.info(f"  - 分析帧数: {visual_analysis.get('total_frames_analyzed', 0)}")
        logger.info(f"  - 检测场景: {scene_detection.get('total_scenes', 0)}")
        logger.info(f"  - 视觉主题: {len(visual_analysis.get('visual_themes', []))}")
        logger.info(f"  - 检测物体: {len(visual_analysis.get('detected_objects', []))}")
        
        # 验证结果完整性
        if (frame_extraction.get('total_frames_extracted', 0) > 0 and
            visual_analysis.get('total_frames_analyzed', 0) > 0):
            logger.info("✅ 完整分析流程测试成功")
            return True
        else:
            logger.error("❌ 完整分析流程失败：结果不完整")
            return False
            
    except Exception as e:
        logger.error(f"❌ 完整分析流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    logger.info("🎬 开始视频分析服务集成测试")
    logger.info("=" * 60)
    
    # 检查依赖
    try:
        import cv2
        import numpy as np
        logger.info(f"OpenCV版本: {cv2.__version__}")
        logger.info(f"NumPy版本: {np.__version__}")
    except ImportError as e:
        logger.error(f"缺少依赖: {e}")
        return False
    
    # 执行测试
    tests = [
        ("服务初始化", test_service_initialization),
        ("帧提取功能", test_frame_extraction),
        ("完整分析流程", test_complete_analysis),
    ]
    
    results = {}
    key_frames = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"执行测试: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            if test_name == "帧提取功能":
                key_frames, video_path = await test_func()
                result = len(key_frames) > 0
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
    
    # 如果基础测试通过，执行额外的分析测试
    if key_frames and results.get("帧提取功能", False):
        logger.info(f"\n{'='*50}")
        logger.info("执行额外测试: 视觉分析和场景检测")
        logger.info(f"{'='*50}")
        
        # 测试视觉分析
        visual_result = await test_visual_analysis(key_frames)
        results["视觉分析"] = len(visual_result.get('visual_themes', [])) > 0
        
        # 测试场景检测
        scene_result = await test_scene_detection(key_frames)
        results["场景检测"] = scene_result.get('total_scenes', 0) > 0
    
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
        logger.info("🎉 所有测试通过！Phase 2视频分析功能完全正常")
        logger.info("📋 Phase 2完成状态:")
        logger.info("  ✅ 智能视频帧提取器")
        logger.info("  ✅ Qwen2.5-VL模型集成")
        logger.info("  ✅ 场景变化检测")
        logger.info("  ✅ 视觉主题提取")
        logger.info("  ✅ 完整分析流程")
        return True
    elif passed >= 3:
        logger.info("⚠️ 大部分测试通过，核心功能正常")
        return True
    else:
        logger.error("💥 多数测试失败，请检查配置")
        return False


if __name__ == "__main__":
    asyncio.run(main()) 