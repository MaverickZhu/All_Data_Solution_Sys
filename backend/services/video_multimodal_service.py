"""
视频多模态语义融合服务
将视觉分析和音频分析结果进行智能融合，生成综合的视频理解报告
"""
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from datetime import datetime, timezone
import json
import re
from collections import defaultdict, Counter

logger = logging.getLogger("service")


class VideoMultimodalService:
    """
    视频多模态语义融合服务
    专门处理视觉和音频信息的智能融合
    """
    
    def __init__(self):
        # 延迟导入LLM服务
        self._llm_service = None
        logger.info("🔗 多模态语义融合服务初始化完成")
    
    @property
    def llm_service(self):
        """延迟加载LLM服务"""
        if self._llm_service is None:
            from backend.services.llm_service import LLMService
            self._llm_service = LLMService()
        return self._llm_service
    
    async def fuse_multimodal_analysis(
        self, 
        visual_results: Dict[str, Any], 
        audio_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        融合多模态分析结果 - 优化版本
        将原来的16次LLM调用优化为3次高效调用
        
        Args:
            visual_results: 视觉分析结果
            audio_results: 音频分析结果
            
        Returns:
            融合后的多模态分析结果
        """
        try:
            logger.info("开始优化的多模态语义融合...")
            
            # 1. 时间轴对齐（无需LLM，纯算法处理）
            logger.info("第1步：时间轴对齐")
            timeline_alignment = await self._align_timelines(visual_results, audio_results)
            
            # 2. 视觉内容统一分析（1次LLM调用）
            logger.info("第2步：视觉内容综合分析")
            visual_comprehensive = await self._analyze_visual_comprehensive(visual_results)
            
            # 3. 音频内容统一分析（1次LLM调用）
            logger.info("第3步：音频内容综合分析") 
            audio_comprehensive = await self._analyze_audio_comprehensive(audio_results)
            
            # 4. 最终多模态整合（1次LLM调用）
            logger.info("第4步：多模态最终整合")
            final_integration = await self._integrate_multimodal_final(
                visual_comprehensive, audio_comprehensive, timeline_alignment
            )
            
            # 5. 构建融合结果
            fusion_result = {
                "timeline_alignment": timeline_alignment,
                "visual_comprehensive": visual_comprehensive,
                "audio_comprehensive": audio_comprehensive,
                "final_integration": final_integration,
                "fusion_metadata": {
                    "fusion_timestamp": datetime.now(timezone.utc).isoformat(),
                    "fusion_type": "optimized_multimodal_fusion",
                    "modalities_fused": ["visual", "audio"],
                    "llm_calls_count": 3,  # 优化后仅3次LLM调用
                    "optimization_strategy": "consolidated_analysis"
                }
            }
            
            logger.info("优化的多模态语义融合完成（仅3次LLM调用）")
            return fusion_result
            
        except Exception as e:
            logger.error(f"多模态语义融合失败: {e}")
            return {
                "error": str(e),
                "timeline_alignment": {},
                "visual_comprehensive": {},
                "audio_comprehensive": {},
                "final_integration": {}
            }

    async def _analyze_visual_comprehensive(self, visual_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        视觉内容综合分析 - 单次LLM调用处理所有视觉分析
        替代原来的多次分散调用
        """
        try:
            # 提取所有视觉信息
            visual_analysis = visual_results.get("visual_analysis", {})
            scene_detection = visual_results.get("scene_detection", {})
            frame_extraction = visual_analysis.get("frame_extraction", {})
            
            # 构建综合分析提示
            comprehensive_prompt = f"""
            请对以下视频视觉内容进行综合分析，返回JSON格式结果：

            视觉主题: {visual_analysis.get("visual_themes", [])}
            检测对象: {visual_analysis.get("detected_objects", [])}
            场景信息: {scene_detection}
            关键帧信息: {frame_extraction}

            请返回JSON格式的综合分析：
            {{
                "visual_summary": "视觉内容总体描述",
                "main_themes": ["主要视觉主题1", "主要视觉主题2"],
                "scene_types": ["场景类型1", "场景类型2"],
                "visual_emotion": "从视觉推断的整体情感",
                "key_objects": ["重要对象1", "重要对象2"],
                "visual_style": "视觉风格描述",
                "scene_progression": "场景变化描述"
            }}
            """
            
            response = await self.llm_service.generate_response(comprehensive_prompt, timeout=30)
            
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {
                    "visual_summary": "视觉分析失败",
                    "main_themes": visual_analysis.get("visual_themes", [])[:3],
                    "scene_types": ["unknown"],
                    "visual_emotion": "neutral",
                    "key_objects": visual_analysis.get("detected_objects", [])[:5],
                    "visual_style": "unknown",
                    "scene_progression": "无法分析"
                }
                
        except Exception as e:
            logger.error(f"视觉综合分析失败: {e}")
            return {"error": str(e)}

    async def _analyze_audio_comprehensive(self, audio_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        音频内容综合分析 - 单次LLM调用处理所有音频分析
        替代原来的多次分散调用
        """
        try:
            # 提取所有音频信息
            enhanced_speech = audio_results.get("enhanced_speech", {})
            semantic_analysis = audio_results.get("semantic_analysis", {})
            timeline_analysis = audio_results.get("timeline_analysis", {})
            
            # 构建综合分析提示
            comprehensive_prompt = f"""
            请对以下视频音频内容进行综合分析，返回JSON格式结果：

            语音转录: {enhanced_speech.get("full_text", "")[:1000]}
            主要话题: {semantic_analysis.get("topic_analysis", {})}
            情感分析: {semantic_analysis.get("emotion_analysis", {})}
            时间轴分析: {timeline_analysis}

            请返回JSON格式的综合分析：
            {{
                "audio_summary": "音频内容总体描述",
                "main_topics": ["主要话题1", "主要话题2"],
                "overall_emotion": "整体情感倾向",
                "speech_quality": "语音质量评估",
                "key_messages": ["关键信息1", "关键信息2"],
                "audio_atmosphere": "音频氛围描述",
                "content_structure": "内容结构分析"
            }}
            """
            
            response = await self.llm_service.generate_response(comprehensive_prompt, timeout=30)
            
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                topic_analysis = semantic_analysis.get("topic_analysis", {})
                emotion_analysis = semantic_analysis.get("emotion_analysis", {})
                return {
                    "audio_summary": "音频分析失败",
                    "main_topics": topic_analysis.get("main_topics", [])[:3],
                    "overall_emotion": emotion_analysis.get("overall_emotion", {}).get("dominant_emotion", "neutral"),
                    "speech_quality": "unknown",
                    "key_messages": [],
                    "audio_atmosphere": "unknown",
                    "content_structure": "无法分析"
                }
                
        except Exception as e:
            logger.error(f"音频综合分析失败: {e}")
            return {"error": str(e)}

    async def _integrate_multimodal_final(
        self, 
        visual_comprehensive: Dict[str, Any], 
        audio_comprehensive: Dict[str, Any],
        timeline_alignment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        最终多模态整合 - 单次LLM调用整合所有信息
        这是整个分析过程的最终整合步骤
        """
        try:
            # 构建最终整合提示
            final_prompt = f"""
            请基于视觉和音频的综合分析，进行最终的多模态整合，返回JSON格式结果：

            视觉分析结果: {visual_comprehensive}
            音频分析结果: {audio_comprehensive}
            时间轴对齐信息: {timeline_alignment.get("modality_coverage", {})}

            请返回JSON格式的最终整合分析：
            {{
                "story_narrative": "完整的故事叙述",
                "multimodal_coherence": 0.85,
                "key_moments": [
                    {{"timestamp": 0.0, "description": "关键时刻描述", "modalities": ["visual", "audio"]}}
                ],
                "overall_theme": "整体主题",
                "emotional_arc": "情感变化轨迹",
                "content_summary": "内容总结",
                "production_insights": "制作见解",
                "audience_appeal": "受众吸引力分析"
            }}
            """
            
            response = await self.llm_service.generate_response(final_prompt, timeout=40)
            
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {
                    "story_narrative": "多模态整合失败",
                    "multimodal_coherence": 0.5,
                    "key_moments": [],
                    "overall_theme": visual_comprehensive.get("main_themes", ["unknown"])[0] if visual_comprehensive.get("main_themes") else "unknown",
                    "emotional_arc": f"视觉: {visual_comprehensive.get('visual_emotion', 'unknown')}, 音频: {audio_comprehensive.get('overall_emotion', 'unknown')}",
                    "content_summary": f"视觉: {visual_comprehensive.get('visual_summary', 'unknown')[:100]}; 音频: {audio_comprehensive.get('audio_summary', 'unknown')[:100]}",
                    "production_insights": "分析失败",
                    "audience_appeal": "无法评估"
                }
                
        except Exception as e:
            logger.error(f"最终多模态整合失败: {e}")
            return {"error": str(e)}
    
    async def _align_timelines(
        self, 
        visual_results: Dict[str, Any], 
        audio_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        对齐视觉和音频的时间轴
        """
        try:
            logger.info("执行时间轴对齐...")
            
            # 提取视觉时间轴信息
            visual_timeline = self._extract_visual_timeline(visual_results)
            
            # 提取音频时间轴信息
            audio_timeline = self._extract_audio_timeline(audio_results)
            
            # 创建统一时间轴
            unified_timeline = self._create_unified_timeline(visual_timeline, audio_timeline)
            
            # 时间段匹配
            temporal_segments = self._match_temporal_segments(visual_timeline, audio_timeline)
            
            # 同步事件检测
            sync_events = self._detect_sync_events(visual_timeline, audio_timeline)
            
            alignment_result = {
                "visual_timeline": visual_timeline,
                "audio_timeline": audio_timeline,
                "unified_timeline": unified_timeline,
                "temporal_segments": temporal_segments,
                "sync_events": sync_events,
                "alignment_quality": self._calculate_alignment_quality(temporal_segments, sync_events)
            }
            
            logger.info(f"时间轴对齐完成: {len(temporal_segments)}个时间段, {len(sync_events)}个同步事件")
            return alignment_result
            
        except Exception as e:
            logger.error(f"时间轴对齐失败: {e}")
            return {
                "error": str(e),
                "visual_timeline": {},
                "audio_timeline": {},
                "unified_timeline": {},
                "temporal_segments": [],
                "sync_events": []
            }
    
    def _extract_visual_timeline(self, visual_results: Dict[str, Any]) -> Dict[str, Any]:
        """提取视觉时间轴信息"""
        try:
            frame_analyses = visual_results.get("visual_analysis", {}).get("frame_analyses", [])
            
            visual_events = []
            for frame in frame_analyses:
                visual_events.append({
                    "timestamp": frame.get("timestamp", 0),
                    "frame_number": frame.get("frame_number", 0),
                    "scene_type": frame.get("scene_type", "unknown"),
                    "visual_themes": frame.get("visual_themes", []),
                    "detected_objects": frame.get("detected_objects", []),
                    "confidence": frame.get("confidence", 0.0)
                })
            
            # 场景变化检测
            scene_changes = []
            prev_scene = None
            for event in visual_events:
                current_scene = event["scene_type"]
                if prev_scene and current_scene != prev_scene:
                    scene_changes.append({
                        "timestamp": event["timestamp"],
                        "from_scene": prev_scene,
                        "to_scene": current_scene,
                        "change_type": "scene_transition"
                    })
                prev_scene = current_scene
            
            return {
                "visual_events": visual_events,
                "scene_changes": scene_changes,
                "total_duration": max([e["timestamp"] for e in visual_events], default=0),
                "total_frames": len(visual_events)
            }
            
        except Exception as e:
            logger.error(f"视觉时间轴提取失败: {e}")
            return {"visual_events": [], "scene_changes": [], "total_duration": 0, "total_frames": 0}
    
    def _extract_audio_timeline(self, audio_results: Dict[str, Any]) -> Dict[str, Any]:
        """提取音频时间轴信息"""
        try:
            enhanced_speech = audio_results.get("enhanced_speech", {})
            timeline_analysis = audio_results.get("timeline_analysis", {})
            semantic_analysis = audio_results.get("semantic_analysis", {})
            
            # 语音片段
            speech_segments = enhanced_speech.get("segments", [])
            
            # 情感变化
            emotion_changes = semantic_analysis.get("emotion_analysis", {}).get("emotion_changes", [])
            
            # 语音活动
            speech_activity = timeline_analysis.get("speech_activity", {}).get("active_periods", [])
            
            # 停顿分析
            pauses = timeline_analysis.get("pause_analysis", {})
            
            audio_events = []
            
            # 添加语音片段事件
            for segment in speech_segments:
                audio_events.append({
                    "timestamp": segment.get("start_time", 0),
                    "end_time": segment.get("end_time", 0),
                    "event_type": "speech_segment",
                    "content": segment.get("text", ""),
                    "confidence": segment.get("confidence", 0.0)
                })
            
            # 添加情感变化事件
            for emotion_change in emotion_changes:
                audio_events.append({
                    "timestamp": emotion_change.get("timestamp", 0),
                    "event_type": "emotion_change",
                    "from_emotion": emotion_change.get("from_emotion", "unknown"),
                    "to_emotion": emotion_change.get("to_emotion", "unknown")
                })
            
            # 排序事件
            audio_events.sort(key=lambda x: x["timestamp"])
            
            return {
                "audio_events": audio_events,
                "speech_segments": speech_segments,
                "emotion_changes": emotion_changes,
                "speech_activity": speech_activity,
                "pause_info": pauses,
                "total_duration": enhanced_speech.get("total_duration", 0)
            }
            
        except Exception as e:
            logger.error(f"音频时间轴提取失败: {e}")
            return {
                "audio_events": [], "speech_segments": [], "emotion_changes": [],
                "speech_activity": [], "pause_info": {}, "total_duration": 0
            }
    
    def _create_unified_timeline(
        self, 
        visual_timeline: Dict[str, Any], 
        audio_timeline: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建统一时间轴"""
        try:
            # 确定总时长
            visual_duration = visual_timeline.get("total_duration", 0)
            audio_duration = audio_timeline.get("total_duration", 0)
            total_duration = max(visual_duration, audio_duration)
            
            # 创建时间段（每秒一个段）
            time_segments = []
            segment_duration = 1.0  # 1秒一个段
            
            for i in range(int(total_duration) + 1):
                start_time = i * segment_duration
                end_time = min((i + 1) * segment_duration, total_duration)
                
                # 找到这个时间段内的视觉和音频事件
                visual_events_in_segment = self._find_events_in_timerange(
                    visual_timeline.get("visual_events", []), start_time, end_time
                )
                
                audio_events_in_segment = self._find_events_in_timerange(
                    audio_timeline.get("audio_events", []), start_time, end_time
                )
                
                time_segments.append({
                    "segment_id": i,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": end_time - start_time,
                    "visual_events": visual_events_in_segment,
                    "audio_events": audio_events_in_segment,
                    "has_visual": len(visual_events_in_segment) > 0,
                    "has_audio": len(audio_events_in_segment) > 0,
                    "modality_overlap": len(visual_events_in_segment) > 0 and len(audio_events_in_segment) > 0
                })
            
            return {
                "total_duration": total_duration,
                "segment_duration": segment_duration,
                "total_segments": len(time_segments),
                "time_segments": time_segments,
                "modality_coverage": {
                    "visual_coverage": sum(1 for s in time_segments if s["has_visual"]) / len(time_segments) if time_segments else 0,
                    "audio_coverage": sum(1 for s in time_segments if s["has_audio"]) / len(time_segments) if time_segments else 0,
                    "overlap_coverage": sum(1 for s in time_segments if s["modality_overlap"]) / len(time_segments) if time_segments else 0
                }
            }
            
        except Exception as e:
            logger.error(f"统一时间轴创建失败: {e}")
            return {"total_duration": 0, "time_segments": [], "modality_coverage": {}}
    
    def _find_events_in_timerange(
        self, 
        events: List[Dict], 
        start_time: float, 
        end_time: float
    ) -> List[Dict]:
        """查找时间范围内的事件"""
        matching_events = []
        
        for event in events:
            event_time = event.get("timestamp", 0)
            event_end = event.get("end_time", event_time)
            
            # 检查事件是否在时间范围内
            if (event_time >= start_time and event_time < end_time) or \
               (event_end > start_time and event_end <= end_time) or \
               (event_time <= start_time and event_end >= end_time):
                matching_events.append(event)
        
        return matching_events
    
    def _match_temporal_segments(
        self, 
        visual_timeline: Dict[str, Any], 
        audio_timeline: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """匹配时间段"""
        try:
            matched_segments = []
            
            # 基于场景变化和语音片段创建匹配段
            visual_events = visual_timeline.get("visual_events", [])
            audio_segments = audio_timeline.get("speech_segments", [])
            
            # 为每个语音片段找到对应的视觉内容
            for audio_segment in audio_segments:
                start_time = audio_segment.get("start_time", 0)
                end_time = audio_segment.get("end_time", 0)
                
                # 找到时间范围内的视觉帧
                matching_visual = self._find_events_in_timerange(visual_events, start_time, end_time)
                
                if matching_visual:
                    # 提取视觉特征
                    visual_themes = set()
                    detected_objects = set()
                    scene_types = set()
                    
                    for visual_event in matching_visual:
                        visual_themes.update(visual_event.get("visual_themes", []))
                        detected_objects.update(visual_event.get("detected_objects", []))
                        scene_types.add(visual_event.get("scene_type", "unknown"))
                    
                    matched_segments.append({
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration": end_time - start_time,
                        "audio_content": audio_segment.get("text", ""),
                        "audio_confidence": audio_segment.get("confidence", 0.0),
                        "visual_themes": list(visual_themes),
                        "detected_objects": list(detected_objects),
                        "scene_types": list(scene_types),
                        "visual_frame_count": len(matching_visual),
                        "segment_type": "audio_driven"
                    })
            
            logger.info(f"匹配了 {len(matched_segments)} 个时间段")
            return matched_segments
            
        except Exception as e:
            logger.error(f"时间段匹配失败: {e}")
            return []
    
    def _detect_sync_events(
        self, 
        visual_timeline: Dict[str, Any], 
        audio_timeline: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """检测同步事件"""
        try:
            sync_events = []
            
            # 检测场景变化与语音停顿的同步
            scene_changes = visual_timeline.get("scene_changes", [])
            audio_events = audio_timeline.get("audio_events", [])
            
            # 为每个场景变化查找附近的音频事件
            for scene_change in scene_changes:
                scene_time = scene_change.get("timestamp", 0)
                
                # 在场景变化前后2秒内查找音频事件
                nearby_audio = [
                    event for event in audio_events
                    if abs(event.get("timestamp", 0) - scene_time) <= 2.0
                ]
                
                if nearby_audio:
                    sync_events.append({
                        "timestamp": scene_time,
                        "sync_type": "scene_audio_sync",
                        "visual_event": scene_change,
                        "audio_events": nearby_audio,
                        "sync_confidence": self._calculate_sync_confidence(scene_change, nearby_audio)
                    })
            
            # 检测情感变化与视觉变化的同步
            emotion_changes = audio_timeline.get("emotion_changes", [])
            visual_events = visual_timeline.get("visual_events", [])
            
            for emotion_change in emotion_changes:
                emotion_time = emotion_change.get("timestamp", 0)
                
                # 查找附近的视觉事件
                nearby_visual = [
                    event for event in visual_events
                    if abs(event.get("timestamp", 0) - emotion_time) <= 1.5
                ]
                
                if nearby_visual:
                    sync_events.append({
                        "timestamp": emotion_time,
                        "sync_type": "emotion_visual_sync",
                        "audio_event": emotion_change,
                        "visual_events": nearby_visual,
                        "sync_confidence": self._calculate_sync_confidence(emotion_change, nearby_visual)
                    })
            
            logger.info(f"检测到 {len(sync_events)} 个同步事件")
            return sync_events
            
        except Exception as e:
            logger.error(f"同步事件检测失败: {e}")
            return []
    
    def _calculate_sync_confidence(self, primary_event: Dict, secondary_events: List[Dict]) -> float:
        """计算同步置信度"""
        try:
            if not secondary_events:
                return 0.0
            
            # 基于时间距离计算置信度
            primary_time = primary_event.get("timestamp", 0)
            min_time_diff = min([
                abs(event.get("timestamp", 0) - primary_time) 
                for event in secondary_events
            ])
            
            # 时间差越小，置信度越高
            if min_time_diff <= 0.5:
                confidence = 0.9
            elif min_time_diff <= 1.0:
                confidence = 0.7
            elif min_time_diff <= 2.0:
                confidence = 0.5
            else:
                confidence = 0.3
            
            return confidence
            
        except Exception as e:
            logger.error(f"同步置信度计算失败: {e}")
            return 0.0
    
    def _calculate_alignment_quality(
        self, 
        temporal_segments: List[Dict], 
        sync_events: List[Dict]
    ) -> Dict[str, Any]:
        """计算对齐质量"""
        try:
            if not temporal_segments:
                return {"overall_quality": 0.0, "coverage": 0.0, "sync_ratio": 0.0}
            
            # 计算覆盖率
            segments_with_both = sum(1 for s in temporal_segments if s.get("visual_frame_count", 0) > 0)
            coverage = segments_with_both / len(temporal_segments)
            
            # 计算同步比例
            sync_ratio = len(sync_events) / len(temporal_segments) if temporal_segments else 0
            
            # 计算平均同步置信度
            avg_sync_confidence = np.mean([
                event.get("sync_confidence", 0) for event in sync_events
            ]) if sync_events else 0
            
            # 综合质量评分
            overall_quality = (coverage * 0.4 + sync_ratio * 0.3 + avg_sync_confidence * 0.3)
            
            return {
                "overall_quality": round(overall_quality, 3),
                "coverage": round(coverage, 3),
                "sync_ratio": round(sync_ratio, 3),
                "avg_sync_confidence": round(avg_sync_confidence, 3),
                "quality_level": "high" if overall_quality > 0.7 else "medium" if overall_quality > 0.4 else "low"
            }
            
        except Exception as e:
            logger.error(f"对齐质量计算失败: {e}")
            return {"overall_quality": 0.0, "coverage": 0.0, "sync_ratio": 0.0}
    
    async def _correlate_semantics(
        self, 
        visual_results: Dict[str, Any], 
        audio_results: Dict[str, Any], 
        timeline_alignment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        跨模态语义关联分析
        """
        try:
            logger.info("执行跨模态语义关联...")
            
            # 1. 主题一致性分析
            theme_correlation = await self._analyze_theme_correlation(visual_results, audio_results)
            
            # 2. 情感一致性分析
            emotion_correlation = await self._analyze_emotion_correlation(visual_results, audio_results)
            
            # 3. 内容互补性分析
            content_complementarity = await self._analyze_content_complementarity(visual_results, audio_results)
            
            # 4. 语义冲突检测
            semantic_conflicts = await self._detect_semantic_conflicts(visual_results, audio_results)
            
            # 5. 基于时间轴的语义关联
            temporal_semantic_links = self._find_temporal_semantic_links(
                timeline_alignment.get("temporal_segments", [])
            )
            
            correlation_result = {
                "theme_correlation": theme_correlation,
                "emotion_correlation": emotion_correlation,
                "content_complementarity": content_complementarity,
                "semantic_conflicts": semantic_conflicts,
                "temporal_semantic_links": temporal_semantic_links,
                "overall_semantic_coherence": self._calculate_semantic_coherence(
                    theme_correlation, emotion_correlation, content_complementarity, semantic_conflicts
                )
            }
            
            logger.info("跨模态语义关联分析完成")
            return correlation_result
            
        except Exception as e:
            logger.error(f"跨模态语义关联失败: {e}")
            return {
                "error": str(e),
                "theme_correlation": {},
                "emotion_correlation": {},
                "content_complementarity": {},
                "semantic_conflicts": [],
                "temporal_semantic_links": []
            }
    
    async def _analyze_theme_correlation(
        self, 
        visual_results: Dict[str, Any], 
        audio_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析主题关联性"""
        try:
            # 提取视觉主题
            visual_analysis = visual_results.get("visual_analysis", {})
            visual_themes = visual_analysis.get("visual_themes", [])
            
            # 提取音频主题
            semantic_analysis = audio_results.get("semantic_analysis", {})
            audio_topics = semantic_analysis.get("topic_analysis", {}).get("main_topics", [])
            
            # 使用LLM分析主题关联性
            correlation_prompt = f"""
            请分析以下视觉主题和音频主题的关联性：

            视觉主题: {visual_themes}
            音频主题: {audio_topics}

            请返回JSON格式的分析结果：
            {{
                "correlation_score": 0.85,
                "correlation_type": "highly_related/related/weakly_related/unrelated",
                "common_themes": ["共同主题1", "共同主题2"],
                "complementary_themes": ["互补主题1", "互补主题2"],
                "conflicting_themes": ["冲突主题1"],
                "analysis_summary": "主题关联性分析总结"
            }}
            """
            
            # 设置短超时时间，避免卡死
            response = await self.llm_service.generate_response(correlation_prompt, timeout=15)
            
            try:
                theme_correlation = json.loads(response)
            except json.JSONDecodeError:
                theme_correlation = {
                    "correlation_score": 0.5,
                    "correlation_type": "unknown",
                    "common_themes": [],
                    "complementary_themes": [],
                    "conflicting_themes": [],
                    "analysis_summary": "主题关联分析失败"
                }
            
            return theme_correlation
            
        except Exception as e:
            logger.error(f"主题关联分析失败: {e}")
            return {
                "correlation_score": 0.0,
                "correlation_type": "error",
                "common_themes": [],
                "complementary_themes": [],
                "conflicting_themes": [],
                "analysis_summary": f"分析失败: {e}"
            }
    
    async def _analyze_emotion_correlation(
        self, 
        visual_results: Dict[str, Any], 
        audio_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析情感关联性"""
        try:
            # 提取视觉情感（如果有的话，从场景分析中推断）
            visual_analysis = visual_results.get("visual_analysis", {})
            scene_analysis = visual_results.get("scene_detection", {})
            
            # 提取音频情感
            semantic_analysis = audio_results.get("semantic_analysis", {})
            emotion_analysis = semantic_analysis.get("emotion_analysis", {})
            overall_emotion = emotion_analysis.get("overall_emotion", {})
            
            # 使用LLM分析情感一致性
            emotion_prompt = f"""
            请分析视觉场景和音频情感的一致性：

            视觉场景信息: {scene_analysis}
            音频情感分析: {emotion_analysis}

            请返回JSON格式的分析结果：
            {{
                "emotion_consistency": 0.8,
                "consistency_type": "highly_consistent/consistent/inconsistent/conflicting",
                "visual_emotion_inference": "从视觉推断的情感",
                "audio_emotion": "音频检测的情感",
                "emotion_alignment": "情感对齐分析",
                "emotional_journey": "情感变化轨迹描述"
            }}
            """
            
            response = await self.llm_service.generate_response(emotion_prompt, timeout=15)
            
            try:
                emotion_correlation = json.loads(response)
            except json.JSONDecodeError:
                emotion_correlation = {
                    "emotion_consistency": 0.5,
                    "consistency_type": "unknown",
                    "visual_emotion_inference": "unknown",
                    "audio_emotion": overall_emotion.get("dominant_emotion", "unknown"),
                    "emotion_alignment": "分析失败",
                    "emotional_journey": "无法分析"
                }
            
            return emotion_correlation
            
        except Exception as e:
            logger.error(f"情感关联分析失败: {e}")
            return {
                "emotion_consistency": 0.0,
                "consistency_type": "error",
                "visual_emotion_inference": "unknown",
                "audio_emotion": "unknown",
                "emotion_alignment": f"分析失败: {e}",
                "emotional_journey": "无法分析"
            }
    
    async def _analyze_content_complementarity(
        self, 
        visual_results: Dict[str, Any], 
        audio_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析内容互补性"""
        try:
            # 提取视觉内容特征
            visual_analysis = visual_results.get("visual_analysis", {})
            
            # 提取音频内容
            enhanced_speech = audio_results.get("enhanced_speech", {})
            full_text = enhanced_speech.get("full_text", "")
            
            # 使用LLM分析内容互补性
            complementarity_prompt = f"""
            请分析视觉内容和音频内容的互补性：

            视觉分析结果: {visual_analysis}
            音频文本内容: {full_text[:500]}...

            请返回JSON格式的分析结果：
            {{
                "complementarity_score": 0.75,
                "complementarity_type": "highly_complementary/complementary/redundant/conflicting",
                "visual_unique_info": ["视觉独有信息1", "视觉独有信息2"],
                "audio_unique_info": ["音频独有信息1", "音频独有信息2"],
                "overlapping_info": ["重叠信息1", "重叠信息2"],
                "information_gaps": ["信息缺口1", "信息缺口2"],
                "complementarity_analysis": "互补性分析总结"
            }}
            """
            
            response = await self.llm_service.generate_response(complementarity_prompt, timeout=15)
            
            try:
                complementarity = json.loads(response)
            except json.JSONDecodeError:
                complementarity = {
                    "complementarity_score": 0.5,
                    "complementarity_type": "unknown",
                    "visual_unique_info": [],
                    "audio_unique_info": [],
                    "overlapping_info": [],
                    "information_gaps": [],
                    "complementarity_analysis": "互补性分析失败"
                }
            
            return complementarity
            
        except Exception as e:
            logger.error(f"内容互补性分析失败: {e}")
            return {
                "complementarity_score": 0.0,
                "complementarity_type": "error",
                "visual_unique_info": [],
                "audio_unique_info": [],
                "overlapping_info": [],
                "information_gaps": [],
                "complementarity_analysis": f"分析失败: {e}"
            }
    
    async def _detect_semantic_conflicts(
        self, 
        visual_results: Dict[str, Any], 
        audio_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """检测语义冲突"""
        try:
            conflicts = []
            
            # 提取关键信息进行冲突检测
            visual_analysis = visual_results.get("visual_analysis", {})
            audio_analysis = audio_results.get("semantic_analysis", {})
            
            # 使用LLM检测潜在冲突
            conflict_prompt = f"""
            请检测视觉和音频内容之间的语义冲突：

            视觉分析: {visual_analysis}
            音频分析: {audio_analysis}

            请返回JSON格式的冲突检测结果：
            {{
                "conflicts": [
                    {{
                        "conflict_type": "content_mismatch/emotion_conflict/theme_inconsistency",
                        "severity": "high/medium/low",
                        "visual_aspect": "冲突的视觉方面",
                        "audio_aspect": "冲突的音频方面",
                        "description": "冲突描述",
                        "confidence": 0.8
                    }}
                ],
                "overall_consistency": 0.7,
                "conflict_summary": "冲突检测总结"
            }}
            """
            
            response = await self.llm_service.generate_response(conflict_prompt)
            
            try:
                conflict_result = json.loads(response)
                conflicts = conflict_result.get("conflicts", [])
            except json.JSONDecodeError:
                conflicts = []
            
            logger.info(f"检测到 {len(conflicts)} 个语义冲突")
            return conflicts
            
        except Exception as e:
            logger.error(f"语义冲突检测失败: {e}")
            return []
    
    def _find_temporal_semantic_links(self, temporal_segments: List[Dict]) -> List[Dict]:
        """查找时间相关的语义关联"""
        try:
            semantic_links = []
            
            for segment in temporal_segments:
                if segment.get("visual_frame_count", 0) > 0 and segment.get("audio_content"):
                    # 分析这个时间段内的语义关联
                    visual_themes = segment.get("visual_themes", [])
                    audio_content = segment.get("audio_content", "")
                    
                    # 简单的关键词匹配（可以用更复杂的NLP方法）
                    semantic_overlap = self._calculate_semantic_overlap(visual_themes, audio_content)
                    
                    if semantic_overlap > 0.3:  # 阈值可调
                        semantic_links.append({
                            "start_time": segment.get("start_time", 0),
                            "end_time": segment.get("end_time", 0),
                            "visual_themes": visual_themes,
                            "audio_content": audio_content[:100] + "..." if len(audio_content) > 100 else audio_content,
                            "semantic_overlap": semantic_overlap,
                            "link_type": "temporal_semantic_correlation"
                        })
            
            logger.info(f"发现 {len(semantic_links)} 个时间语义关联")
            return semantic_links
            
        except Exception as e:
            logger.error(f"时间语义关联查找失败: {e}")
            return []
    
    def _calculate_semantic_overlap(self, visual_themes: List[str], audio_content: str) -> float:
        """计算语义重叠度（简化版）"""
        try:
            if not visual_themes or not audio_content:
                return 0.0
            
            # 简单的关键词匹配
            audio_words = set(audio_content.lower().split())
            theme_words = set([theme.lower() for theme in visual_themes])
            
            # 计算交集
            common_words = audio_words.intersection(theme_words)
            
            if not theme_words:
                return 0.0
            
            overlap = len(common_words) / len(theme_words)
            return min(overlap, 1.0)
            
        except Exception as e:
            logger.error(f"语义重叠度计算失败: {e}")
            return 0.0
    
    def _calculate_semantic_coherence(
        self, 
        theme_correlation: Dict, 
        emotion_correlation: Dict, 
        content_complementarity: Dict, 
        semantic_conflicts: List
    ) -> Dict[str, Any]:
        """计算整体语义一致性"""
        try:
            # 提取各项得分
            theme_score = theme_correlation.get("correlation_score", 0.5)
            emotion_score = emotion_correlation.get("emotion_consistency", 0.5)
            complementarity_score = content_complementarity.get("complementarity_score", 0.5)
            
            # 冲突惩罚
            conflict_penalty = len(semantic_conflicts) * 0.1
            
            # 综合得分
            overall_coherence = (theme_score * 0.3 + emotion_score * 0.3 + complementarity_score * 0.4) - conflict_penalty
            overall_coherence = max(0.0, min(1.0, overall_coherence))  # 限制在0-1之间
            
            return {
                "overall_coherence": round(overall_coherence, 3),
                "theme_contribution": round(theme_score * 0.3, 3),
                "emotion_contribution": round(emotion_score * 0.3, 3),
                "complementarity_contribution": round(complementarity_score * 0.4, 3),
                "conflict_penalty": round(conflict_penalty, 3),
                "coherence_level": "high" if overall_coherence > 0.7 else "medium" if overall_coherence > 0.4 else "low",
                "analysis_quality": "excellent" if overall_coherence > 0.8 else "good" if overall_coherence > 0.6 else "fair" if overall_coherence > 0.4 else "poor"
            }
            
        except Exception as e:
            logger.error(f"语义一致性计算失败: {e}")
            return {
                "overall_coherence": 0.0,
                "coherence_level": "unknown",
                "analysis_quality": "error"
            }
    
    async def _analyze_story_structure(
        self, 
        visual_results: Dict[str, Any], 
        audio_results: Dict[str, Any], 
        semantic_correlation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析故事结构
        """
        try:
            logger.info("执行故事结构分析...")
            
            # 1. 提取故事元素
            story_elements = self._extract_story_elements(visual_results, audio_results)
            
            # 2. 识别故事段落
            story_segments = await self._identify_story_segments(visual_results, audio_results, semantic_correlation)
            
            # 3. 分析故事弧线
            story_arc = await self._analyze_story_arc(story_segments)
            
            # 4. 识别关键转折点
            turning_points = self._identify_turning_points(story_segments)
            
            # 5. 生成故事摘要
            story_summary = await self._generate_story_summary(story_elements, story_segments, story_arc)
            
            story_analysis = {
                "story_elements": story_elements,
                "story_segments": story_segments,
                "story_arc": story_arc,
                "turning_points": turning_points,
                "story_summary": story_summary,
                "narrative_structure": self._analyze_narrative_structure(story_segments, turning_points)
            }
            
            logger.info("故事结构分析完成")
            return story_analysis
            
        except Exception as e:
            logger.error(f"故事结构分析失败: {e}")
            return {
                "error": str(e),
                "story_elements": {},
                "story_segments": [],
                "story_arc": {},
                "turning_points": [],
                "story_summary": ""
            }
    
    def _extract_story_elements(
        self, 
        visual_results: Dict[str, Any], 
        audio_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """提取故事元素"""
        try:
            # 从视觉分析提取
            visual_analysis = visual_results.get("visual_analysis", {})
            detected_objects = visual_analysis.get("detected_objects", [])
            visual_themes = visual_analysis.get("visual_themes", [])
            
            # 从音频分析提取
            semantic_analysis = audio_results.get("semantic_analysis", {})
            topic_analysis = semantic_analysis.get("topic_analysis", {})
            content_analysis = semantic_analysis.get("content_analysis", {})
            
            story_elements = {
                "characters": self._extract_characters(detected_objects, topic_analysis),
                "setting": self._extract_setting(visual_themes, content_analysis),
                "themes": self._extract_themes(visual_themes, topic_analysis),
                "mood": self._extract_mood(visual_analysis, semantic_analysis),
                "content_type": content_analysis.get("content_type", "unknown")
            }
            
            return story_elements
            
        except Exception as e:
            logger.error(f"故事元素提取失败: {e}")
            return {"characters": [], "setting": [], "themes": [], "mood": "unknown", "content_type": "unknown"}
    
    def _extract_characters(self, detected_objects: List[str], topic_analysis: Dict) -> List[str]:
        """提取角色信息"""
        characters = []
        
        # 从检测到的对象中提取人物
        person_objects = [obj for obj in detected_objects if any(keyword in obj.lower() for keyword in ["person", "人", "man", "woman", "child"])]
        characters.extend(person_objects)
        
        # 从话题分析中提取提到的人物
        keywords = topic_analysis.get("keywords", [])
        person_keywords = [kw for kw in keywords if any(indicator in kw.lower() for indicator in ["先生", "女士", "老师", "同学", "朋友"])]
        characters.extend(person_keywords)
        
        return list(set(characters))  # 去重
    
    def _extract_setting(self, visual_themes: List[str], content_analysis: Dict) -> List[str]:
        """提取场景设置"""
        setting = []
        
        # 从视觉主题中提取场景
        scene_themes = [theme for theme in visual_themes if any(keyword in theme.lower() for keyword in ["indoor", "outdoor", "office", "home", "street", "室内", "室外", "办公室", "家", "街道"])]
        setting.extend(scene_themes)
        
        # 从内容分析中推断设置
        estimated_audience = content_analysis.get("estimated_audience", "")
        if estimated_audience:
            setting.append(f"面向{estimated_audience}")
        
        return list(set(setting))
    
    def _extract_themes(self, visual_themes: List[str], topic_analysis: Dict) -> List[str]:
        """提取主题"""
        themes = []
        themes.extend(visual_themes)
        themes.extend(topic_analysis.get("main_topics", []))
        themes.extend(topic_analysis.get("topic_categories", []))
        
        return list(set(themes))
    
    def _extract_mood(self, visual_analysis: Dict, semantic_analysis: Dict) -> str:
        """提取情绪氛围"""
        # 从音频情感分析中获取主导情感
        emotion_analysis = semantic_analysis.get("emotion_analysis", {})
        overall_emotion = emotion_analysis.get("overall_emotion", {})
        dominant_emotion = overall_emotion.get("dominant_emotion", "neutral")
        
        return dominant_emotion
    
    async def _identify_story_segments(
        self, 
        visual_results: Dict[str, Any], 
        audio_results: Dict[str, Any], 
        semantic_correlation: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """识别故事段落"""
        try:
            # 基于时间语义关联创建故事段落
            temporal_links = semantic_correlation.get("temporal_semantic_links", [])
            
            if not temporal_links:
                return []
            
            story_segments = []
            for i, link in enumerate(temporal_links):
                segment = {
                    "segment_id": i,
                    "start_time": link.get("start_time", 0),
                    "end_time": link.get("end_time", 0),
                    "duration": link.get("end_time", 0) - link.get("start_time", 0),
                    "visual_content": link.get("visual_themes", []),
                    "audio_content": link.get("audio_content", ""),
                    "semantic_overlap": link.get("semantic_overlap", 0),
                    "segment_type": "narrative_unit"
                }
                
                # 使用LLM分析这个段落的叙事功能
                segment_analysis = await self._analyze_segment_narrative_function(segment)
                segment.update(segment_analysis)
                
                story_segments.append(segment)
            
            return story_segments
            
        except Exception as e:
            logger.error(f"故事段落识别失败: {e}")
            return []
    
    async def _analyze_segment_narrative_function(self, segment: Dict[str, Any]) -> Dict[str, Any]:
        """分析段落的叙事功能"""
        try:
            analysis_prompt = f"""
            请分析以下视频段落的叙事功能：

            时间: {segment.get('start_time', 0):.1f}s - {segment.get('end_time', 0):.1f}s
            视觉内容: {segment.get('visual_content', [])}
            音频内容: {segment.get('audio_content', '')}

            请返回JSON格式的分析结果：
            {{
                "narrative_function": "introduction/development/climax/resolution/transition",
                "content_summary": "段落内容摘要",
                "emotional_tone": "情感基调",
                "importance_level": "high/medium/low",
                "narrative_purpose": "叙事目的描述"
            }}
            """
            
            response = await self.llm_service.generate_response(analysis_prompt)
            
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {
                    "narrative_function": "unknown",
                    "content_summary": "分析失败",
                    "emotional_tone": "neutral",
                    "importance_level": "medium",
                    "narrative_purpose": "无法确定"
                }
                
        except Exception as e:
            logger.error(f"段落叙事功能分析失败: {e}")
            return {
                "narrative_function": "unknown",
                "content_summary": f"分析失败: {e}",
                "emotional_tone": "neutral",
                "importance_level": "low",
                "narrative_purpose": "分析失败"
            }
    
    async def _analyze_story_arc(self, story_segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析故事弧线"""
        try:
            if not story_segments:
                return {"arc_type": "unknown", "structure": [], "development": "无法分析"}
            
            # 使用LLM分析整体故事弧线
            arc_prompt = f"""
            请分析以下故事段落的整体弧线结构：

            故事段落:
            {json.dumps([{
                'time': f"{s.get('start_time', 0):.1f}s-{s.get('end_time', 0):.1f}s",
                'function': s.get('narrative_function', 'unknown'),
                'summary': s.get('content_summary', ''),
                'tone': s.get('emotional_tone', 'neutral')
            } for s in story_segments], ensure_ascii=False, indent=2)}

            请返回JSON格式的故事弧线分析：
            {{
                "arc_type": "linear/circular/episodic/experimental",
                "structure": ["introduction", "rising_action", "climax", "falling_action", "resolution"],
                "development": "故事发展描述",
                "pacing": "fast/medium/slow",
                "narrative_coherence": 0.8,
                "story_completeness": "complete/incomplete/fragmented"
            }}
            """
            
            response = await self.llm_service.generate_response(arc_prompt)
            
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {
                    "arc_type": "unknown",
                    "structure": [],
                    "development": "分析失败",
                    "pacing": "unknown",
                    "narrative_coherence": 0.5,
                    "story_completeness": "unknown"
                }
                
        except Exception as e:
            logger.error(f"故事弧线分析失败: {e}")
            return {
                "arc_type": "error",
                "structure": [],
                "development": f"分析失败: {e}",
                "pacing": "unknown",
                "narrative_coherence": 0.0,
                "story_completeness": "error"
            }
    
    def _identify_turning_points(self, story_segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """识别关键转折点"""
        try:
            turning_points = []
            
            for i, segment in enumerate(story_segments):
                # 检查是否是重要的叙事节点
                narrative_function = segment.get("narrative_function", "unknown")
                importance_level = segment.get("importance_level", "medium")
                
                if narrative_function in ["climax", "transition"] or importance_level == "high":
                    turning_points.append({
                        "timestamp": segment.get("start_time", 0),
                        "segment_id": segment.get("segment_id", i),
                        "turning_point_type": narrative_function,
                        "description": segment.get("content_summary", ""),
                        "emotional_impact": segment.get("emotional_tone", "neutral"),
                        "importance": importance_level
                    })
            
            logger.info(f"识别了 {len(turning_points)} 个转折点")
            return turning_points
            
        except Exception as e:
            logger.error(f"转折点识别失败: {e}")
            return []
    
    async def _generate_story_summary(
        self, 
        story_elements: Dict[str, Any], 
        story_segments: List[Dict[str, Any]], 
        story_arc: Dict[str, Any]
    ) -> str:
        """生成故事摘要"""
        try:
            summary_prompt = f"""
            请基于以下信息生成视频的故事摘要：

            故事元素: {story_elements}
            故事弧线: {story_arc}
            段落数量: {len(story_segments)}

            请生成一个简洁但全面的故事摘要（200字以内）：
            """
            
            summary = await self.llm_service.generate_response(summary_prompt)
            return summary.strip()
            
        except Exception as e:
            logger.error(f"故事摘要生成失败: {e}")
            return f"故事摘要生成失败: {e}"
    
    def _analyze_narrative_structure(
        self, 
        story_segments: List[Dict[str, Any]], 
        turning_points: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析叙事结构"""
        try:
            if not story_segments:
                return {"structure_type": "unknown", "complexity": "low", "organization": "unclear"}
            
            # 分析结构复杂度
            narrative_functions = [s.get("narrative_function", "unknown") for s in story_segments]
            unique_functions = set(narrative_functions)
            
            complexity = "high" if len(unique_functions) > 3 else "medium" if len(unique_functions) > 1 else "low"
            
            # 分析组织方式
            if "introduction" in narrative_functions and "resolution" in narrative_functions:
                organization = "well_structured"
            elif len(turning_points) > 0:
                organization = "structured"
            else:
                organization = "loose"
            
            return {
                "structure_type": "narrative" if len(unique_functions) > 2 else "simple",
                "complexity": complexity,
                "organization": organization,
                "segment_count": len(story_segments),
                "turning_point_count": len(turning_points),
                "narrative_functions": list(unique_functions)
            }
            
        except Exception as e:
            logger.error(f"叙事结构分析失败: {e}")
            return {"structure_type": "error", "complexity": "unknown", "organization": "error"}
    
    async def _track_emotion_changes(
        self, 
        visual_results: Dict[str, Any], 
        audio_results: Dict[str, Any], 
        timeline_alignment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        追踪情感变化
        """
        try:
            logger.info("执行情感变化追踪...")
            
            # 1. 提取情感时间线
            emotion_timeline = self._extract_emotion_timeline(audio_results, timeline_alignment)
            
            # 2. 检测情感转折点
            emotion_turning_points = self._detect_emotion_turning_points(emotion_timeline)
            
            # 3. 分析情感强度变化
            emotion_intensity = self._analyze_emotion_intensity(emotion_timeline)
            
            # 4. 情感弧线分析
            emotion_arc = await self._analyze_emotion_arc(emotion_timeline, emotion_turning_points)
            
            # 5. 情感一致性检查
            emotion_consistency = self._check_emotion_consistency(visual_results, audio_results, emotion_timeline)
            
            emotion_tracking = {
                "emotion_timeline": emotion_timeline,
                "emotion_turning_points": emotion_turning_points,
                "emotion_intensity": emotion_intensity,
                "emotion_arc": emotion_arc,
                "emotion_consistency": emotion_consistency,
                "emotional_journey_summary": await self._summarize_emotional_journey(emotion_timeline, emotion_turning_points)
            }
            
            logger.info("情感变化追踪完成")
            return emotion_tracking
            
        except Exception as e:
            logger.error(f"情感变化追踪失败: {e}")
            return {
                "error": str(e),
                "emotion_timeline": [],
                "emotion_turning_points": [],
                "emotion_intensity": {},
                "emotion_arc": {},
                "emotion_consistency": {}
            }
    
    def _extract_emotion_timeline(
        self, 
        audio_results: Dict[str, Any], 
        timeline_alignment: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """提取情感时间线"""
        try:
            emotion_timeline = []
            
            # 从音频分析中提取情感信息
            semantic_analysis = audio_results.get("semantic_analysis", {})
            emotion_analysis = semantic_analysis.get("emotion_analysis", {})
            segment_emotions = emotion_analysis.get("segment_emotions", [])
            
            # 转换为时间线格式
            for emotion_segment in segment_emotions:
                emotion_timeline.append({
                    "timestamp": emotion_segment.get("start_time", 0),
                    "end_time": emotion_segment.get("end_time", 0),
                    "emotion": emotion_segment.get("emotion", "neutral"),
                    "confidence": emotion_segment.get("confidence", 0.0),
                    "segment_id": emotion_segment.get("segment_id", 0),
                    "source": "audio_analysis"
                })
            
            # 按时间排序
            emotion_timeline.sort(key=lambda x: x["timestamp"])
            
            logger.info(f"提取了 {len(emotion_timeline)} 个情感时间点")
            return emotion_timeline
            
        except Exception as e:
            logger.error(f"情感时间线提取失败: {e}")
            return []
    
    def _detect_emotion_turning_points(self, emotion_timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """检测情感转折点"""
        try:
            turning_points = []
            
            for i in range(1, len(emotion_timeline)):
                prev_emotion = emotion_timeline[i-1].get("emotion", "neutral")
                curr_emotion = emotion_timeline[i].get("emotion", "neutral")
                
                # 检测情感变化
                if prev_emotion != curr_emotion:
                    # 计算情感变化强度
                    intensity = self._calculate_emotion_change_intensity(prev_emotion, curr_emotion)
                    
                    turning_points.append({
                        "timestamp": emotion_timeline[i].get("timestamp", 0),
                        "from_emotion": prev_emotion,
                        "to_emotion": curr_emotion,
                        "change_intensity": intensity,
                        "change_type": self._classify_emotion_change(prev_emotion, curr_emotion),
                        "confidence": min(
                            emotion_timeline[i-1].get("confidence", 0),
                            emotion_timeline[i].get("confidence", 0)
                        )
                    })
            
            logger.info(f"检测到 {len(turning_points)} 个情感转折点")
            return turning_points
            
        except Exception as e:
            logger.error(f"情感转折点检测失败: {e}")
            return []
    
    def _calculate_emotion_change_intensity(self, from_emotion: str, to_emotion: str) -> float:
        """计算情感变化强度"""
        # 简化的情感强度映射
        emotion_intensity_map = {
            "positive": 1.0,
            "excited": 1.2,
            "happy": 0.8,
            "neutral": 0.0,
            "negative": -1.0,
            "sad": -0.8,
            "angry": -1.2,
            "surprised": 0.5
        }
        
        from_intensity = emotion_intensity_map.get(from_emotion, 0.0)
        to_intensity = emotion_intensity_map.get(to_emotion, 0.0)
        
        return abs(to_intensity - from_intensity)
    
    def _classify_emotion_change(self, from_emotion: str, to_emotion: str) -> str:
        """分类情感变化类型"""
        positive_emotions = {"positive", "excited", "happy"}
        negative_emotions = {"negative", "sad", "angry"}
        neutral_emotions = {"neutral", "surprised"}
        
        if from_emotion in positive_emotions and to_emotion in negative_emotions:
            return "positive_to_negative"
        elif from_emotion in negative_emotions and to_emotion in positive_emotions:
            return "negative_to_positive"
        elif from_emotion in neutral_emotions:
            return "neutral_to_emotional"
        elif to_emotion in neutral_emotions:
            return "emotional_to_neutral"
        else:
            return "emotional_shift"
    
    def _analyze_emotion_intensity(self, emotion_timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析情感强度"""
        try:
            if not emotion_timeline:
                return {"average_intensity": 0.0, "peak_intensity": 0.0, "intensity_variance": 0.0}
            
            confidences = [point.get("confidence", 0.0) for point in emotion_timeline]
            
            return {
                "average_intensity": np.mean(confidences),
                "peak_intensity": np.max(confidences),
                "min_intensity": np.min(confidences),
                "intensity_variance": np.var(confidences),
                "intensity_stability": 1.0 - np.std(confidences) if confidences else 0.0
            }
            
        except Exception as e:
            logger.error(f"情感强度分析失败: {e}")
            return {"average_intensity": 0.0, "peak_intensity": 0.0, "intensity_variance": 0.0}
    
    async def _analyze_emotion_arc(
        self, 
        emotion_timeline: List[Dict[str, Any]], 
        emotion_turning_points: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析情感弧线"""
        try:
            if not emotion_timeline:
                return {"arc_type": "unknown", "emotional_journey": "无情感数据"}
            
            # 使用LLM分析情感弧线
            arc_prompt = f"""
            请分析以下情感时间线的弧线特征：

            情感时间线: {emotion_timeline[:10]}  # 限制长度
            情感转折点: {emotion_turning_points}

            请返回JSON格式的分析结果：
            {{
                "arc_type": "rising/falling/stable/fluctuating/u_shaped/inverted_u",
                "emotional_journey": "情感旅程描述",
                "dominant_emotion_phase": "主导情感阶段",
                "emotional_complexity": "high/medium/low",
                "emotional_resolution": "resolved/unresolved/ambiguous"
            }}
            """
            
            response = await self.llm_service.generate_response(arc_prompt)
            
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {
                    "arc_type": "unknown",
                    "emotional_journey": "分析失败",
                    "dominant_emotion_phase": "unknown",
                    "emotional_complexity": "medium",
                    "emotional_resolution": "unknown"
                }
                
        except Exception as e:
            logger.error(f"情感弧线分析失败: {e}")
            return {
                "arc_type": "error",
                "emotional_journey": f"分析失败: {e}",
                "dominant_emotion_phase": "error",
                "emotional_complexity": "unknown",
                "emotional_resolution": "error"
            }
    
    def _check_emotion_consistency(
        self, 
        visual_results: Dict[str, Any], 
        audio_results: Dict[str, Any], 
        emotion_timeline: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """检查情感一致性"""
        try:
            # 提取整体情感倾向
            semantic_analysis = audio_results.get("semantic_analysis", {})
            overall_emotion = semantic_analysis.get("emotion_analysis", {}).get("overall_emotion", {})
            dominant_emotion = overall_emotion.get("dominant_emotion", "neutral")
            
            # 计算时间线中各情感的分布
            emotions = [point.get("emotion", "neutral") for point in emotion_timeline]
            emotion_counts = Counter(emotions)
            
            # 检查一致性
            timeline_dominant = emotion_counts.most_common(1)[0][0] if emotion_counts else "neutral"
            consistency_score = 1.0 if timeline_dominant == dominant_emotion else 0.5
            
            return {
                "overall_emotion": dominant_emotion,
                "timeline_dominant_emotion": timeline_dominant,
                "consistency_score": consistency_score,
                "emotion_distribution": dict(emotion_counts),
                "consistency_level": "high" if consistency_score > 0.8 else "medium" if consistency_score > 0.5 else "low"
            }
            
        except Exception as e:
            logger.error(f"情感一致性检查失败: {e}")
            return {
                "consistency_score": 0.0,
                "consistency_level": "unknown",
                "emotion_distribution": {}
            }
    
    async def _summarize_emotional_journey(
        self, 
        emotion_timeline: List[Dict[str, Any]], 
        emotion_turning_points: List[Dict[str, Any]]
    ) -> str:
        """总结情感旅程"""
        try:
            if not emotion_timeline:
                return "无情感数据可分析"
            
            summary_prompt = f"""
            请总结以下情感旅程：

            情感时间线点数: {len(emotion_timeline)}
            主要情感转折: {len(emotion_turning_points)}
            情感变化: {[f"{tp.get('from_emotion', 'unknown')}→{tp.get('to_emotion', 'unknown')}" for tp in emotion_turning_points[:3]]}

            请用50字以内总结这个情感旅程：
            """
            
            summary = await self.llm_service.generate_response(summary_prompt)
            return summary.strip()
            
        except Exception as e:
            logger.error(f"情感旅程总结失败: {e}")
            return f"情感旅程总结失败: {e}"
    
    async def _generate_comprehensive_understanding(
        self, 
        visual_results: Dict[str, Any], 
        audio_results: Dict[str, Any], 
        semantic_correlation: Dict[str, Any], 
        story_analysis: Dict[str, Any], 
        emotion_tracking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成综合理解报告
        """
        try:
            logger.info("生成综合理解报告...")
            
            # 1. 视频整体理解
            overall_understanding = await self._generate_overall_understanding(
                visual_results, audio_results, semantic_correlation
            )
            
            # 2. 关键洞察提取
            key_insights = await self._extract_key_insights(
                story_analysis, emotion_tracking, semantic_correlation
            )
            
            # 3. 内容价值评估
            content_value = self._assess_content_value(
                visual_results, audio_results, story_analysis, emotion_tracking
            )
            
            # 4. 受众分析
            audience_analysis = await self._analyze_target_audience(
                visual_results, audio_results, story_analysis
            )
            
            # 5. 改进建议
            improvement_suggestions = await self._generate_improvement_suggestions(
                semantic_correlation, story_analysis, emotion_tracking
            )
            
            comprehensive_understanding = {
                "overall_understanding": overall_understanding,
                "key_insights": key_insights,
                "content_value": content_value,
                "audience_analysis": audience_analysis,
                "improvement_suggestions": improvement_suggestions,
                "analysis_confidence": self._calculate_analysis_confidence(
                    visual_results, audio_results, semantic_correlation
                )
            }
            
            logger.info("综合理解报告生成完成")
            return comprehensive_understanding
            
        except Exception as e:
            logger.error(f"综合理解报告生成失败: {e}")
            return {
                "error": str(e),
                "overall_understanding": "",
                "key_insights": [],
                "content_value": {},
                "audience_analysis": {},
                "improvement_suggestions": []
            }
    
    async def _generate_overall_understanding(
        self, 
        visual_results: Dict[str, Any], 
        audio_results: Dict[str, Any], 
        semantic_correlation: Dict[str, Any]
    ) -> str:
        """生成整体理解"""
        try:
            understanding_prompt = f"""
            请基于以下多模态分析结果，生成视频的整体理解报告：

            视觉分析摘要: {visual_results.get('visual_analysis', {}).get('analysis_summary', '')}
            音频分析摘要: {audio_results.get('semantic_analysis', {}).get('content_analysis', {})}
            语义一致性: {semantic_correlation.get('overall_semantic_coherence', {})}

            请生成一个300字以内的综合理解报告，包括：
            1. 视频的主要内容和目的
            2. 视觉和音频的配合效果
            3. 整体传达的信息和价值
            """
            
            understanding = await self.llm_service.generate_response(understanding_prompt)
            return understanding.strip()
            
        except Exception as e:
            logger.error(f"整体理解生成失败: {e}")
            return f"整体理解生成失败: {e}"
    
    async def _extract_key_insights(
        self, 
        story_analysis: Dict[str, Any], 
        emotion_tracking: Dict[str, Any], 
        semantic_correlation: Dict[str, Any]
    ) -> List[str]:
        """提取关键洞察"""
        try:
            insights_prompt = f"""
            请从以下分析结果中提取3-5个关键洞察：

            故事分析: {story_analysis.get('story_summary', '')}
            情感追踪: {emotion_tracking.get('emotional_journey_summary', '')}
            语义关联: {semantic_correlation.get('overall_semantic_coherence', {})}

            请返回JSON格式的洞察列表：
            {{
                "insights": [
                    "洞察1：具体的观察和发现",
                    "洞察2：重要的模式或趋势",
                    "洞察3：有价值的结论"
                ]
            }}
            """
            
            response = await self.llm_service.generate_response(insights_prompt)
            
            try:
                insights_data = json.loads(response)
                return insights_data.get("insights", [])
            except json.JSONDecodeError:
                return ["关键洞察提取失败"]
                
        except Exception as e:
            logger.error(f"关键洞察提取失败: {e}")
            return [f"关键洞察提取失败: {e}"]
    
    def _assess_content_value(
        self, 
        visual_results: Dict[str, Any], 
        audio_results: Dict[str, Any], 
        story_analysis: Dict[str, Any], 
        emotion_tracking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """评估内容价值"""
        try:
            # 基于各项指标计算内容价值
            visual_quality = visual_results.get("visual_analysis", {}).get("analysis_quality", 0.5)
            audio_quality = audio_results.get("enhanced_speech", {}).get("confidence", 0.5)
            story_coherence = story_analysis.get("story_arc", {}).get("narrative_coherence", 0.5)
            emotion_stability = emotion_tracking.get("emotion_intensity", {}).get("intensity_stability", 0.5)
            
            # 综合评分
            overall_value = (visual_quality * 0.25 + audio_quality * 0.25 + 
                           story_coherence * 0.25 + emotion_stability * 0.25)
            
            return {
                "overall_value_score": round(overall_value, 3),
                "visual_quality_score": round(visual_quality, 3),
                "audio_quality_score": round(audio_quality, 3),
                "story_coherence_score": round(story_coherence, 3),
                "emotion_stability_score": round(emotion_stability, 3),
                "value_level": "high" if overall_value > 0.7 else "medium" if overall_value > 0.4 else "low",
                "content_strengths": self._identify_content_strengths(visual_quality, audio_quality, story_coherence, emotion_stability),
                "content_weaknesses": self._identify_content_weaknesses(visual_quality, audio_quality, story_coherence, emotion_stability)
            }
            
        except Exception as e:
            logger.error(f"内容价值评估失败: {e}")
            return {
                "overall_value_score": 0.0,
                "value_level": "unknown",
                "content_strengths": [],
                "content_weaknesses": []
            }
    
    def _identify_content_strengths(self, visual_q: float, audio_q: float, story_q: float, emotion_q: float) -> List[str]:
        """识别内容优势"""
        strengths = []
        
        if visual_q > 0.7:
            strengths.append("视觉内容质量高")
        if audio_q > 0.7:
            strengths.append("音频识别准确度高")
        if story_q > 0.7:
            strengths.append("故事结构清晰连贯")
        if emotion_q > 0.7:
            strengths.append("情感表达稳定一致")
        
        return strengths
    
    def _identify_content_weaknesses(self, visual_q: float, audio_q: float, story_q: float, emotion_q: float) -> List[str]:
        """识别内容弱点"""
        weaknesses = []
        
        if visual_q < 0.4:
            weaknesses.append("视觉内容需要改进")
        if audio_q < 0.4:
            weaknesses.append("音频质量有待提升")
        if story_q < 0.4:
            weaknesses.append("故事结构不够清晰")
        if emotion_q < 0.4:
            weaknesses.append("情感表达不够稳定")
        
        return weaknesses
    
    async def _analyze_target_audience(
        self, 
        visual_results: Dict[str, Any], 
        audio_results: Dict[str, Any], 
        story_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析目标受众"""
        try:
            audience_prompt = f"""
            请基于以下信息分析视频的目标受众：

            内容类型: {audio_results.get('semantic_analysis', {}).get('content_analysis', {}).get('content_type', 'unknown')}
            故事元素: {story_analysis.get('story_elements', {})}
            视觉主题: {visual_results.get('visual_analysis', {}).get('visual_themes', [])}

            请返回JSON格式的受众分析：
            {{
                "primary_audience": "主要目标受众",
                "secondary_audience": "次要目标受众",
                "age_group": "年龄群体",
                "interests": ["兴趣1", "兴趣2"],
                "viewing_context": "观看场景",
                "audience_engagement_potential": "high/medium/low"
            }}
            """
            
            response = await self.llm_service.generate_response(audience_prompt)
            
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {
                    "primary_audience": "未知",
                    "secondary_audience": "未知",
                    "age_group": "未知",
                    "interests": [],
                    "viewing_context": "未知",
                    "audience_engagement_potential": "medium"
                }
                
        except Exception as e:
            logger.error(f"目标受众分析失败: {e}")
            return {
                "primary_audience": f"分析失败: {e}",
                "audience_engagement_potential": "unknown"
            }
    
    async def _generate_improvement_suggestions(
        self, 
        semantic_correlation: Dict[str, Any], 
        story_analysis: Dict[str, Any], 
        emotion_tracking: Dict[str, Any]
    ) -> List[str]:
        """生成改进建议"""
        try:
            suggestions_prompt = f"""
            请基于以下分析结果提供3-5个具体的改进建议：

            语义一致性: {semantic_correlation.get('overall_semantic_coherence', {})}
            故事结构: {story_analysis.get('narrative_structure', {})}
            情感表达: {emotion_tracking.get('emotion_consistency', {})}

            请返回JSON格式的建议列表：
            {{
                "suggestions": [
                    "建议1：具体可行的改进方案",
                    "建议2：针对性的优化建议",
                    "建议3：提升效果的方法"
                ]
            }}
            """
            
            response = await self.llm_service.generate_response(suggestions_prompt)
            
            try:
                suggestions_data = json.loads(response)
                return suggestions_data.get("suggestions", [])
            except json.JSONDecodeError:
                return ["改进建议生成失败"]
                
        except Exception as e:
            logger.error(f"改进建议生成失败: {e}")
            return [f"改进建议生成失败: {e}"]
    
    def _calculate_analysis_confidence(
        self, 
        visual_results: Dict[str, Any], 
        audio_results: Dict[str, Any], 
        semantic_correlation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """计算分析置信度"""
        try:
            # 提取各项置信度指标
            visual_confidence = visual_results.get("visual_analysis", {}).get("analysis_confidence", 0.5)
            audio_confidence = audio_results.get("enhanced_speech", {}).get("confidence", 0.5)
            semantic_confidence = semantic_correlation.get("overall_semantic_coherence", {}).get("overall_coherence", 0.5)
            
            # 计算综合置信度
            overall_confidence = (visual_confidence * 0.4 + audio_confidence * 0.3 + semantic_confidence * 0.3)
            
            return {
                "overall_confidence": round(overall_confidence, 3),
                "visual_confidence": round(visual_confidence, 3),
                "audio_confidence": round(audio_confidence, 3),
                "semantic_confidence": round(semantic_confidence, 3),
                "confidence_level": "high" if overall_confidence > 0.7 else "medium" if overall_confidence > 0.4 else "low",
                "reliability": "reliable" if overall_confidence > 0.6 else "moderate" if overall_confidence > 0.4 else "limited"
            }
            
        except Exception as e:
            logger.error(f"分析置信度计算失败: {e}")
            return {
                "overall_confidence": 0.0,
                "confidence_level": "unknown",
                "reliability": "error"
            }


# 创建全局实例
video_multimodal_service = VideoMultimodalService() 