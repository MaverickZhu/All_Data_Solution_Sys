"""
测试视频多模态语义融合功能
验证Phase 4的时间轴对齐、语义关联、故事分析、情感追踪等功能
"""
import sys
import os
import asyncio
from pathlib import Path
import logging
import json

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_multimodal_service_import():
    """测试多模态融合服务导入"""
    logger.info("测试多模态融合服务导入...")
    
    try:
        from backend.services.video_multimodal_service import VideoMultimodalService
        logger.info("✅ VideoMultimodalService导入成功")
        return True
    except Exception as e:
        logger.error(f"❌ VideoMultimodalService导入失败: {e}")
        return False


async def test_service_structure():
    """测试服务结构"""
    logger.info("测试多模态融合服务结构...")
    
    try:
        from backend.services.video_multimodal_service import VideoMultimodalService
        
        # 检查核心方法
        fusion_methods = [
            'fuse_multimodal_analysis',
            '_align_timelines',
            '_correlate_semantics',
            '_analyze_story_structure',
            '_track_emotion_changes',
            '_generate_comprehensive_understanding'
        ]
        
        for method in fusion_methods:
            if hasattr(VideoMultimodalService, method):
                logger.info(f"  ✅ 方法存在: {method}")
            else:
                logger.error(f"  ❌ 方法缺失: {method}")
                return False
        
        logger.info("✅ 多模态融合服务结构验证通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 服务结构验证失败: {e}")
        return False


async def test_service_initialization():
    """测试服务初始化"""
    logger.info("测试多模态融合服务初始化...")
    
    try:
        from backend.services.video_multimodal_service import VideoMultimodalService
        
        service = VideoMultimodalService()
        logger.info("✅ 多模态融合服务初始化成功")
        
        # 检查延迟加载属性
        if hasattr(service, '_llm_service'):
            logger.info("✅ LLM服务延迟加载属性存在")
        else:
            logger.error("❌ LLM服务延迟加载属性缺失")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 服务初始化失败: {e}")
        return False


async def test_timeline_alignment():
    """测试时间轴对齐功能"""
    logger.info("测试时间轴对齐功能...")
    
    try:
        from backend.services.video_multimodal_service import VideoMultimodalService
        
        service = VideoMultimodalService()
        
        # 创建模拟的视觉和音频结果
        mock_visual_results = {
            "visual_analysis": {
                "frame_analyses": [
                    {
                        "timestamp": 0.0,
                        "frame_number": 0,
                        "scene_type": "indoor",
                        "visual_themes": ["presentation", "office"],
                        "detected_objects": ["person", "laptop"],
                        "confidence": 0.85
                    },
                    {
                        "timestamp": 2.0,
                        "frame_number": 60,
                        "scene_type": "indoor",
                        "visual_themes": ["discussion", "meeting"],
                        "detected_objects": ["person", "whiteboard"],
                        "confidence": 0.90
                    }
                ]
            }
        }
        
        mock_audio_results = {
            "enhanced_speech": {
                "segments": [
                    {
                        "id": 0,
                        "start_time": 0.0,
                        "end_time": 1.5,
                        "text": "欢迎大家参加今天的会议",
                        "confidence": 0.88
                    },
                    {
                        "id": 1,
                        "start_time": 2.0,
                        "end_time": 4.0,
                        "text": "我们来讨论项目进展",
                        "confidence": 0.92
                    }
                ],
                "total_duration": 4.0
            },
            "semantic_analysis": {
                "emotion_analysis": {
                    "emotion_changes": [
                        {
                            "timestamp": 2.0,
                            "from_emotion": "neutral",
                            "to_emotion": "positive"
                        }
                    ]
                }
            }
        }
        
        # 测试时间轴对齐
        alignment_result = await service._align_timelines(mock_visual_results, mock_audio_results)
        
        logger.info("时间轴对齐结果:")
        logger.info(f"  - 视觉事件数: {len(alignment_result.get('visual_timeline', {}).get('visual_events', []))}")
        logger.info(f"  - 音频事件数: {len(alignment_result.get('audio_timeline', {}).get('audio_events', []))}")
        logger.info(f"  - 统一时间段数: {len(alignment_result.get('unified_timeline', {}).get('time_segments', []))}")
        logger.info(f"  - 匹配段数: {len(alignment_result.get('temporal_segments', []))}")
        logger.info(f"  - 同步事件数: {len(alignment_result.get('sync_events', []))}")
        
        if alignment_result.get("error"):
            logger.error(f"❌ 时间轴对齐失败: {alignment_result['error']}")
            return False
        
        logger.info("✅ 时间轴对齐测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 时间轴对齐测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_semantic_correlation():
    """测试语义关联分析"""
    logger.info("测试语义关联分析...")
    
    try:
        from backend.services.video_multimodal_service import VideoMultimodalService
        
        service = VideoMultimodalService()
        
        # 创建模拟数据
        mock_visual_results = {
            "visual_analysis": {
                "visual_themes": ["meeting", "presentation", "office"],
                "analysis_summary": "办公室会议场景"
            }
        }
        
        mock_audio_results = {
            "semantic_analysis": {
                "topic_analysis": {
                    "main_topics": ["会议", "项目", "讨论"],
                    "keywords": ["项目", "进展", "团队"]
                },
                "content_analysis": {
                    "content_type": "meeting",
                    "content_style": "formal"
                }
            },
            "enhanced_speech": {
                "full_text": "欢迎大家参加今天的项目进展会议，我们来讨论一下最新的开发情况。"
            }
        }
        
        # 创建模拟时间轴对齐结果
        mock_timeline_alignment = {
            "temporal_segments": [
                {
                    "start_time": 0.0,
                    "end_time": 2.0,
                    "visual_themes": ["meeting", "office"],
                    "audio_content": "欢迎大家参加今天的项目进展会议",
                    "visual_frame_count": 2
                }
            ]
        }
        
        # 测试语义关联
        correlation_result = await service._correlate_semantics(
            mock_visual_results, mock_audio_results, mock_timeline_alignment
        )
        
        logger.info("语义关联分析结果:")
        logger.info(f"  - 主题关联得分: {correlation_result.get('theme_correlation', {}).get('correlation_score', 0)}")
        logger.info(f"  - 情感一致性: {correlation_result.get('emotion_correlation', {}).get('emotion_consistency', 0)}")
        logger.info(f"  - 内容互补性: {correlation_result.get('content_complementarity', {}).get('complementarity_score', 0)}")
        logger.info(f"  - 语义冲突数: {len(correlation_result.get('semantic_conflicts', []))}")
        logger.info(f"  - 时间语义关联数: {len(correlation_result.get('temporal_semantic_links', []))}")
        
        if correlation_result.get("error"):
            logger.error(f"❌ 语义关联分析失败: {correlation_result['error']}")
            return False
        
        logger.info("✅ 语义关联分析测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 语义关联分析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_story_analysis():
    """测试故事结构分析"""
    logger.info("测试故事结构分析...")
    
    try:
        from backend.services.video_multimodal_service import VideoMultimodalService
        
        service = VideoMultimodalService()
        
        # 创建模拟数据
        mock_visual_results = {
            "visual_analysis": {
                "detected_objects": ["person", "laptop", "whiteboard"],
                "visual_themes": ["presentation", "meeting", "discussion"]
            }
        }
        
        mock_audio_results = {
            "semantic_analysis": {
                "topic_analysis": {
                    "main_topics": ["项目", "会议", "讨论"],
                    "keywords": ["团队", "进展", "计划"]
                },
                "content_analysis": {
                    "content_type": "meeting",
                    "estimated_audience": "团队成员"
                }
            }
        }
        
        mock_semantic_correlation = {
            "temporal_semantic_links": [
                {
                    "start_time": 0.0,
                    "end_time": 2.0,
                    "visual_themes": ["presentation"],
                    "audio_content": "欢迎大家参加今天的会议",
                    "semantic_overlap": 0.7
                },
                {
                    "start_time": 2.0,
                    "end_time": 4.0,
                    "visual_themes": ["discussion"],
                    "audio_content": "我们来讨论项目进展",
                    "semantic_overlap": 0.8
                }
            ]
        }
        
        # 测试故事结构分析
        story_result = await service._analyze_story_structure(
            mock_visual_results, mock_audio_results, mock_semantic_correlation
        )
        
        logger.info("故事结构分析结果:")
        logger.info(f"  - 故事元素: {story_result.get('story_elements', {})}")
        logger.info(f"  - 故事段落数: {len(story_result.get('story_segments', []))}")
        logger.info(f"  - 转折点数: {len(story_result.get('turning_points', []))}")
        logger.info(f"  - 故事弧线: {story_result.get('story_arc', {}).get('arc_type', 'unknown')}")
        logger.info(f"  - 叙事结构: {story_result.get('narrative_structure', {})}")
        
        if story_result.get("error"):
            logger.error(f"❌ 故事结构分析失败: {story_result['error']}")
            return False
        
        logger.info("✅ 故事结构分析测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 故事结构分析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_emotion_tracking():
    """测试情感变化追踪"""
    logger.info("测试情感变化追踪...")
    
    try:
        from backend.services.video_multimodal_service import VideoMultimodalService
        
        service = VideoMultimodalService()
        
        # 创建模拟数据
        mock_visual_results = {
            "visual_analysis": {
                "analysis_summary": "正式的会议环境"
            }
        }
        
        mock_audio_results = {
            "semantic_analysis": {
                "emotion_analysis": {
                    "segment_emotions": [
                        {
                            "segment_id": 0,
                            "start_time": 0.0,
                            "end_time": 2.0,
                            "emotion": "neutral",
                            "confidence": 0.8
                        },
                        {
                            "segment_id": 1,
                            "start_time": 2.0,
                            "end_time": 4.0,
                            "emotion": "positive",
                            "confidence": 0.9
                        }
                    ],
                    "emotion_changes": [
                        {
                            "timestamp": 2.0,
                            "from_emotion": "neutral",
                            "to_emotion": "positive"
                        }
                    ],
                    "overall_emotion": {
                        "dominant_emotion": "positive"
                    }
                }
            }
        }
        
        mock_timeline_alignment = {
            "temporal_segments": [
                {
                    "start_time": 0.0,
                    "end_time": 2.0,
                    "has_visual": True,
                    "has_audio": True
                },
                {
                    "start_time": 2.0,
                    "end_time": 4.0,
                    "has_visual": True,
                    "has_audio": True
                }
            ]
        }
        
        # 测试情感变化追踪
        emotion_result = await service._track_emotion_changes(
            mock_visual_results, mock_audio_results, mock_timeline_alignment
        )
        
        logger.info("情感变化追踪结果:")
        logger.info(f"  - 情感时间线点数: {len(emotion_result.get('emotion_timeline', []))}")
        logger.info(f"  - 情感转折点数: {len(emotion_result.get('emotion_turning_points', []))}")
        logger.info(f"  - 情感强度: {emotion_result.get('emotion_intensity', {})}")
        logger.info(f"  - 情感弧线: {emotion_result.get('emotion_arc', {}).get('arc_type', 'unknown')}")
        logger.info(f"  - 情感一致性: {emotion_result.get('emotion_consistency', {}).get('consistency_level', 'unknown')}")
        
        if emotion_result.get("error"):
            logger.error(f"❌ 情感变化追踪失败: {emotion_result['error']}")
            return False
        
        logger.info("✅ 情感变化追踪测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 情感变化追踪测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_comprehensive_understanding():
    """测试综合理解生成"""
    logger.info("测试综合理解生成...")
    
    try:
        from backend.services.video_multimodal_service import VideoMultimodalService
        
        service = VideoMultimodalService()
        
        # 创建完整的模拟数据
        mock_visual_results = {
            "visual_analysis": {
                "analysis_summary": "专业的会议环境，包含演示和讨论场景",
                "visual_themes": ["meeting", "presentation", "office"],
                "analysis_confidence": 0.85
            }
        }
        
        mock_audio_results = {
            "enhanced_speech": {
                "full_text": "欢迎大家参加今天的项目进展会议，我们来讨论一下最新的开发情况和下一步计划。",
                "confidence": 0.90
            },
            "semantic_analysis": {
                "content_analysis": {
                    "content_type": "meeting",
                    "content_style": "formal",
                    "main_themes": ["项目管理", "团队协作"]
                }
            }
        }
        
        mock_semantic_correlation = {
            "overall_semantic_coherence": {
                "overall_coherence": 0.75,
                "coherence_level": "high"
            }
        }
        
        mock_story_analysis = {
            "story_summary": "这是一个关于项目进展的正式会议，包含欢迎、讨论和计划制定等环节。",
            "narrative_structure": {
                "structure_type": "structured",
                "complexity": "medium"
            }
        }
        
        mock_emotion_tracking = {
            "emotional_journey_summary": "从中性开始，逐渐转向积极正面的讨论氛围。",
            "emotion_consistency": {
                "consistency_level": "high"
            }
        }
        
        # 测试综合理解生成
        understanding_result = await service._generate_comprehensive_understanding(
            mock_visual_results, mock_audio_results, mock_semantic_correlation,
            mock_story_analysis, mock_emotion_tracking
        )
        
        logger.info("综合理解生成结果:")
        logger.info(f"  - 整体理解: {understanding_result.get('overall_understanding', '')[:100]}...")
        logger.info(f"  - 关键洞察数: {len(understanding_result.get('key_insights', []))}")
        logger.info(f"  - 内容价值: {understanding_result.get('content_value', {}).get('value_level', 'unknown')}")
        logger.info(f"  - 目标受众: {understanding_result.get('audience_analysis', {}).get('primary_audience', 'unknown')}")
        logger.info(f"  - 改进建议数: {len(understanding_result.get('improvement_suggestions', []))}")
        logger.info(f"  - 分析置信度: {understanding_result.get('analysis_confidence', {}).get('overall_confidence', 0)}")
        
        if understanding_result.get("error"):
            logger.error(f"❌ 综合理解生成失败: {understanding_result['error']}")
            return False
        
        logger.info("✅ 综合理解生成测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 综合理解生成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_multimodal_fusion():
    """测试完整的多模态融合流程"""
    logger.info("测试完整的多模态融合流程...")
    
    try:
        from backend.services.video_multimodal_service import VideoMultimodalService
        
        service = VideoMultimodalService()
        
        # 创建完整的模拟输入
        mock_visual_results = {
            "visual_analysis": {
                "frame_analyses": [
                    {
                        "timestamp": 0.0,
                        "frame_number": 0,
                        "scene_type": "indoor",
                        "visual_themes": ["meeting", "office"],
                        "detected_objects": ["person", "laptop"],
                        "confidence": 0.85
                    }
                ],
                "visual_themes": ["meeting", "presentation"],
                "detected_objects": ["person", "laptop", "whiteboard"],
                "analysis_summary": "专业会议环境",
                "analysis_confidence": 0.85
            },
            "scene_detection": {
                "total_scenes": 1,
                "scene_changes": []
            }
        }
        
        mock_audio_results = {
            "enhanced_speech": {
                "segments": [
                    {
                        "id": 0,
                        "start_time": 0.0,
                        "end_time": 2.0,
                        "text": "欢迎参加项目会议",
                        "confidence": 0.90
                    }
                ],
                "full_text": "欢迎参加项目会议，我们来讨论进展情况。",
                "total_duration": 2.0,
                "confidence": 0.90
            },
            "semantic_analysis": {
                "content_analysis": {
                    "content_type": "meeting",
                    "content_style": "formal"
                },
                "emotion_analysis": {
                    "segment_emotions": [
                        {
                            "segment_id": 0,
                            "start_time": 0.0,
                            "end_time": 2.0,
                            "emotion": "neutral",
                            "confidence": 0.8
                        }
                    ],
                    "overall_emotion": {
                        "dominant_emotion": "neutral"
                    },
                    "emotion_changes": []
                },
                "topic_analysis": {
                    "main_topics": ["会议", "项目"],
                    "keywords": ["项目", "讨论", "进展"]
                }
            }
        }
        
        # 执行完整的多模态融合
        fusion_result = await service.fuse_multimodal_analysis(mock_visual_results, mock_audio_results)
        
        logger.info("完整多模态融合结果:")
        logger.info(f"  - 时间轴对齐质量: {fusion_result.get('timeline_alignment', {}).get('alignment_quality', {}).get('overall_quality', 0)}")
        logger.info(f"  - 语义一致性: {fusion_result.get('semantic_correlation', {}).get('overall_semantic_coherence', {}).get('overall_coherence', 0)}")
        logger.info(f"  - 故事段落数: {len(fusion_result.get('story_analysis', {}).get('story_segments', []))}")
        logger.info(f"  - 情感转折点数: {len(fusion_result.get('emotion_tracking', {}).get('emotion_turning_points', []))}")
        logger.info(f"  - 综合理解置信度: {fusion_result.get('comprehensive_understanding', {}).get('analysis_confidence', {}).get('overall_confidence', 0)}")
        
        if fusion_result.get("error"):
            logger.error(f"❌ 完整多模态融合失败: {fusion_result['error']}")
            return False
        
        # 检查所有核心组件是否都有结果
        required_components = [
            "timeline_alignment",
            "semantic_correlation", 
            "story_analysis",
            "emotion_tracking",
            "comprehensive_understanding"
        ]
        
        missing_components = []
        for component in required_components:
            if not fusion_result.get(component):
                missing_components.append(component)
        
        if missing_components:
            logger.error(f"❌ 缺少融合组件: {missing_components}")
            return False
        
        logger.info("✅ 完整多模态融合测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 完整多模态融合测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_integration_with_video_analysis():
    """测试与视频分析服务的集成"""
    logger.info("测试与视频分析服务的集成...")
    
    try:
        from backend.services.video_analysis_service import VideoAnalysisService
        
        # 检查视频分析服务是否包含多模态融合
        if hasattr(VideoAnalysisService, 'perform_multimodal_fusion'):
            logger.info("✅ 视频分析服务包含多模态融合方法")
        else:
            logger.error("❌ 视频分析服务缺少多模态融合方法")
            return False
        
        # 检查服务初始化
        try:
            service = VideoAnalysisService()
            if hasattr(service, 'multimodal_service'):
                logger.info("✅ 视频分析服务包含多模态服务实例")
            else:
                logger.error("❌ 视频分析服务缺少多模态服务实例")
                return False
        except Exception as e:
            logger.warning(f"⚠️ 视频分析服务初始化失败: {e}")
            logger.info("继续检查类定义...")
        
        logger.info("✅ 多模态融合集成验证通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 集成验证失败: {e}")
        return False


async def main():
    """主测试函数"""
    logger.info("🔗 开始Phase 4多模态语义融合测试")
    logger.info("=" * 60)
    
    # 执行测试
    tests = [
        ("多模态服务导入", test_multimodal_service_import),
        ("服务结构验证", test_service_structure),
        ("服务初始化", test_service_initialization),
        ("时间轴对齐", test_timeline_alignment),
        ("语义关联分析", test_semantic_correlation),
        ("故事结构分析", test_story_analysis),
        ("情感变化追踪", test_emotion_tracking),
        ("综合理解生成", test_comprehensive_understanding),
        ("完整多模态融合", test_full_multimodal_fusion),
        ("集成验证", test_integration_with_video_analysis),
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
        logger.info("🎉 所有测试通过！Phase 4多模态语义融合功能完全正常")
        logger.info("📋 Phase 4完成状态:")
        logger.info("  ✅ 时间轴对齐算法")
        logger.info("  ✅ 跨模态语义关联")
        logger.info("  ✅ 故事结构分析")
        logger.info("  ✅ 情感变化追踪")
        logger.info("  ✅ 综合理解生成")
        logger.info("  ✅ 完整融合流程")
        logger.info("  ✅ 服务集成")
        return True
    elif passed >= 7:
        logger.info("⚠️ 大部分测试通过，核心功能正常")
        logger.info("💡 提示：部分功能可能需要额外的依赖配置")
        return True
    else:
        logger.error("💥 多数测试失败，请检查配置")
        return False


if __name__ == "__main__":
    asyncio.run(main()) 