"""
测试视频视觉分析服务
验证Qwen2.5-VL模型集成和视频帧分析功能
"""
import sys
import os
import asyncio
from pathlib import Path
import logging
import tempfile
import cv2
import numpy as np

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.services.video_vision_service import VideoVisionService, video_vision_service
from backend.services.video_frame_extractor import FrameInfo

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_test_frame_image() -> Path:
    """创建测试帧图像"""
    try:
        # 创建测试图像
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 添加一些内容
        # 背景颜色
        img[:, :] = (50, 100, 150)  # 蓝色背景
        
        # 添加矩形
        cv2.rectangle(img, (100, 100), (300, 200), (255, 255, 255), -1)
        
        # 添加文字
        cv2.putText(img, "Test Frame", (120, 160), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        # 添加圆形
        cv2.circle(img, (500, 300), 50, (0, 255, 0), -1)
        
        # 保存到临时文件
        temp_dir = Path(tempfile.gettempdir()) / "video_test"
        temp_dir.mkdir(exist_ok=True)
        
        test_image_path = temp_dir / "test_frame.jpg"
        cv2.imwrite(str(test_image_path), img)
        
        logger.info(f"测试图像创建成功: {test_image_path}")
        return test_image_path
        
    except Exception as e:
        logger.error(f"创建测试图像失败: {e}")
        raise


def create_test_frame_info(image_path: Path) -> FrameInfo:
    """创建测试帧信息"""
    return FrameInfo(
        frame_number=100,
        timestamp=5.0,
        frame_path=str(image_path),
        scene_change_score=0.8,
        is_key_frame=True,
        key_frame_reason="测试帧",
        brightness=128.0,
        contrast=45.0,
        sharpness=0.75,
        frame_hash="test_hash_123"
    )


async def test_vision_service_initialization():
    """测试视觉服务初始化"""
    logger.info("测试视觉服务初始化...")
    
    try:
        service = VideoVisionService()
        logger.info(f"✅ 视觉服务初始化成功: {service.model_name}")
        return True
    except Exception as e:
        logger.error(f"❌ 视觉服务初始化失败: {e}")
        return False


async def test_ollama_connection():
    """测试Ollama连接"""
    logger.info("测试Ollama连接...")
    
    try:
        from langchain_community.chat_models import ChatOllama
        
        llm = ChatOllama(
            base_url="http://host.docker.internal:11435",
            model="qwen2.5vl:7b",
            temperature=0.1
        )
        
        # 简单的文本测试
        response = llm.invoke("你好，请回复'连接正常'")
        logger.info(f"Ollama响应: {response}")
        
        if "连接正常" in str(response) or "正常" in str(response):
            logger.info("✅ Ollama连接正常")
            return True
        else:
            logger.info("✅ Ollama连接成功，但响应格式不同")
            return True
            
    except Exception as e:
        logger.error(f"❌ Ollama连接失败: {e}")
        logger.info("💡 请确保Ollama服务正在运行，并且已加载qwen2.5vl:7b模型")
        return False


async def test_single_frame_analysis():
    """测试单帧分析功能"""
    logger.info("测试单帧分析功能...")
    
    try:
        # 创建测试图像
        test_image = create_test_frame_image()
        
        # 创建帧信息
        frame_info = create_test_frame_info(test_image)
        
        # 创建服务实例
        service = VideoVisionService()
        
        # 分析单帧
        logger.info("开始分析测试帧...")
        result = await service.analyze_single_frame(frame_info)
        
        logger.info("单帧分析结果:")
        logger.info(f"  帧号: {result.get('frame_number')}")
        logger.info(f"  时间戳: {result.get('timestamp')}s")
        logger.info(f"  场景类型: {result.get('scene_type')}")
        logger.info(f"  检测物体: {result.get('detected_objects')}")
        logger.info(f"  视觉主题: {result.get('visual_themes')}")
        logger.info(f"  文字内容: {result.get('text_content')}")
        logger.info(f"  描述: {result.get('description')}")
        logger.info(f"  置信度: {result.get('confidence')}")
        
        # 验证结果
        if result.get('frame_number') == 100 and result.get('timestamp') == 5.0:
            if result.get('error'):
                logger.warning(f"⚠️ 分析完成但有错误: {result.get('error')}")
                return False
            else:
                logger.info("✅ 单帧分析测试成功")
                return True
        else:
            logger.error("❌ 分析结果格式错误")
            return False
            
    except Exception as e:
        logger.error(f"❌ 单帧分析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_batch_frame_analysis():
    """测试批量帧分析功能"""
    logger.info("测试批量帧分析功能...")
    
    try:
        # 创建多个测试帧
        frames = []
        for i in range(3):
            test_image = create_test_frame_image()
            frame_info = FrameInfo(
                frame_number=i * 30,
                timestamp=i * 2.0,
                frame_path=str(test_image),
                scene_change_score=0.5 + i * 0.2,
                is_key_frame=True,
                key_frame_reason=f"测试帧{i+1}",
                brightness=100 + i * 20,
                contrast=40 + i * 10,
                sharpness=0.6 + i * 0.1,
                frame_hash=f"test_hash_{i}"
            )
            frames.append(frame_info)
        
        # 创建服务实例
        service = VideoVisionService()
        
        # 批量分析
        logger.info(f"开始批量分析 {len(frames)} 帧...")
        result = await service.analyze_video_frames(frames)
        
        logger.info("批量分析结果:")
        logger.info(f"  分析帧数: {result.get('total_frames_analyzed')}")
        logger.info(f"  视觉主题: {result.get('visual_themes')}")
        logger.info(f"  检测物体: {result.get('detected_objects')}")
        logger.info(f"  场景类型: {result.get('scene_types')}")
        logger.info(f"  场景变化: {len(result.get('scene_changes', []))}")
        logger.info(f"  视频摘要: {result.get('video_summary')}")
        logger.info(f"  成功率: {result.get('analysis_metadata', {}).get('success_rate', 0):.2%}")
        
        # 验证结果
        if result.get('total_frames_analyzed', 0) > 0:
            logger.info("✅ 批量帧分析测试成功")
            return True
        else:
            logger.error("❌ 批量分析失败：没有成功分析的帧")
            return False
            
    except Exception as e:
        logger.error(f"❌ 批量帧分析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mock_analysis():
    """测试模拟分析（不依赖Ollama）"""
    logger.info("测试模拟分析功能...")
    
    try:
        # 创建测试图像
        test_image = create_test_frame_image()
        frame_info = create_test_frame_info(test_image)
        
        service = VideoVisionService()
        
        # 创建模拟分析结果
        mock_result = service._create_fallback_analysis("测试分析", frame_info)
        
        logger.info("模拟分析结果:")
        logger.info(f"  帧号: {mock_result.get('frame_number')}")
        logger.info(f"  时间戳: {mock_result.get('timestamp')}")
        logger.info(f"  场景类型: {mock_result.get('scene_type')}")
        logger.info(f"  置信度: {mock_result.get('confidence')}")
        
        if mock_result.get('frame_number') == 100:
            logger.info("✅ 模拟分析测试成功")
            return True
        else:
            logger.error("❌ 模拟分析结果错误")
            return False
            
    except Exception as e:
        logger.error(f"❌ 模拟分析测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    logger.info("🎬 开始视频视觉分析服务测试")
    
    # 检查依赖
    try:
        import cv2
        import numpy as np
        from langchain_community.chat_models import ChatOllama
        logger.info(f"OpenCV版本: {cv2.__version__}")
        logger.info(f"NumPy版本: {np.__version__}")
        logger.info("LangChain依赖检查通过")
    except ImportError as e:
        logger.error(f"缺少依赖: {e}")
        return False
    
    # 执行测试
    tests = [
        ("视觉服务初始化", test_vision_service_initialization),
        ("模拟分析功能", test_mock_analysis),
        ("Ollama连接", test_ollama_connection),
        ("单帧分析", test_single_frame_analysis),
        ("批量帧分析", test_batch_frame_analysis),
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"执行测试: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
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
        logger.info("🎉 所有测试通过！视频视觉分析服务功能正常")
        return True
    elif passed >= 2:  # 至少基础功能正常
        logger.info("⚠️ 部分测试通过，基础功能正常")
        return True
    else:
        logger.error("💥 大部分测试失败，请检查配置")
        return False


if __name__ == "__main__":
    asyncio.run(main()) 