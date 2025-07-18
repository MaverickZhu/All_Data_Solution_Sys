"""
视频视觉分析服务
基于现有ImageDescriptionService，扩展到视频帧的智能分析
集成Qwen2.5-VL模型进行场景理解、物体识别、文字提取
"""
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
import base64
import json
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage

from backend.services.video_frame_extractor import FrameInfo
from backend.services.image_description_service import ImageDescriptionService

logger = logging.getLogger("service")


class VideoVisionService:
    """
    视频视觉分析服务
    基于Qwen2.5-VL模型进行视频帧的智能分析
    """
    
    def __init__(self, 
                 model_name: str = "qwen2.5vl:7b", 
                 ollama_url: str = "http://host.docker.internal:11435"):
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.image_service = ImageDescriptionService(model_name, ollama_url)
        logger.info(f"🎬 视频视觉分析服务初始化: {model_name}")
    
    async def analyze_video_frames(self, frames: List[FrameInfo]) -> Dict[str, Any]:
        """
        分析视频帧序列，提取视觉语义信息
        
        Args:
            frames: 视频帧信息列表
            
        Returns:
            视频视觉分析结果
        """
        try:
            logger.info(f"开始分析 {len(frames)} 个视频帧")
            
            # 分析结果容器
            frame_analyses = []
            visual_themes = set()
            detected_objects = set()
            scene_types = set()
            text_contents = []
            
            # 批量分析帧（控制并发数量避免过载）
            batch_size = 3  # 控制并发数量
            for i in range(0, len(frames), batch_size):
                batch = frames[i:i + batch_size]
                logger.info(f"处理帧批次 {i//batch_size + 1}/{(len(frames) + batch_size - 1)//batch_size}")
                
                # 并发分析当前批次
                batch_tasks = []
                for frame in batch:
                    if frame.frame_path:
                        task = self.analyze_single_frame(frame)
                        batch_tasks.append(task)
                
                # 等待批次完成
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # 处理批次结果
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        logger.error(f"帧分析失败: {result}")
                        continue
                    
                    frame_analyses.append(result)
                    
                    # 收集全局信息
                    if result.get('visual_themes'):
                        visual_themes.update(result['visual_themes'])
                    if result.get('detected_objects'):
                        detected_objects.update(result['detected_objects'])
                    if result.get('scene_type'):
                        scene_types.add(result['scene_type'])
                    if result.get('text_content'):
                        text_contents.append(result['text_content'])
            
            # 生成视频级别的分析摘要
            video_summary = await self._generate_video_summary(frame_analyses)
            
            # 检测场景变化
            scene_changes = self._detect_scene_changes(frame_analyses)
            
            analysis_result = {
                "total_frames_analyzed": len(frame_analyses),
                "frame_analyses": frame_analyses,
                "visual_themes": list(visual_themes),
                "detected_objects": list(detected_objects),
                "scene_types": list(scene_types),
                "extracted_text": text_contents,
                "scene_changes": scene_changes,
                "video_summary": video_summary,
                "analysis_metadata": {
                    "model_used": self.model_name,
                    "analysis_type": "video_vision_semantic",
                    "success_rate": len(frame_analyses) / len(frames) if frames else 0
                }
            }
            
            logger.info(f"视频视觉分析完成: {len(frame_analyses)}帧成功分析")
            return analysis_result
            
        except Exception as e:
            logger.error(f"视频视觉分析失败: {e}")
            return {
                "error": str(e),
                "total_frames_analyzed": 0,
                "frame_analyses": [],
                "visual_themes": [],
                "detected_objects": [],
                "scene_types": [],
                "extracted_text": [],
                "scene_changes": [],
                "video_summary": "",
                "analysis_metadata": {
                    "model_used": self.model_name,
                    "analysis_type": "video_vision_semantic",
                    "success_rate": 0,
                    "error": str(e)
                }
            }
    
    async def analyze_single_frame(self, frame: FrameInfo) -> Dict[str, Any]:
        """
        分析单个视频帧
        
        Args:
            frame: 帧信息
            
        Returns:
            单帧分析结果
        """
        try:
            frame_path = Path(frame.frame_path)
            if not frame_path.exists():
                raise FileNotFoundError(f"帧文件不存在: {frame_path}")
            
            logger.debug(f"分析帧: {frame.frame_number} (时间: {frame.timestamp:.2f}s)")
            
            # 使用专门的视频帧分析提示
            analysis_result = await self._analyze_frame_with_video_context(frame_path, frame)
            
            # 解析分析结果
            parsed_result = self._parse_frame_analysis(analysis_result, frame)
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"单帧分析失败 (帧{frame.frame_number}): {e}")
            return {
                "frame_number": frame.frame_number,
                "timestamp": frame.timestamp,
                "error": str(e),
                "visual_themes": [],
                "detected_objects": [],
                "scene_type": "unknown",
                "text_content": "",
                "description": "",
                "confidence": 0.0
            }
    
    async def _analyze_frame_with_video_context(self, frame_path: Path, frame: FrameInfo) -> str:
        """
        使用视频上下文分析帧
        """
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 编码图像
                image_base64 = self.image_service.encode_image_to_base64(frame_path)
                
                # 初始化LLM with timeout
                llm = ChatOllama(
                    base_url=self.ollama_url,
                    model=self.model_name,
                    temperature=0.1,
                    timeout=30  # 30秒超时
                )
                
                # 视频帧专用分析提示
                prompt_template = f"""
                <|system|>
                你是一个专业的视频内容分析专家。你正在分析视频中的一帧画面。
                
                当前帧信息：
                - 帧序号: {frame.frame_number}
                - 时间戳: {frame.timestamp:.2f}秒
                - 关键帧原因: {frame.key_frame_reason}
                - 亮度: {frame.brightness:.1f}
                - 对比度: {frame.contrast:.1f}
                - 清晰度: {frame.sharpness:.3f}
                
                请按照以下JSON格式分析这一帧：
                {{
                    "scene_type": "场景类型(室内/室外/人物/风景/文档等)",
                    "main_objects": ["主要物体1", "主要物体2", "主要物体3"],
                    "visual_themes": ["视觉主题1", "视觉主题2"],
                    "text_content": "提取的文字内容(如果有)",
                    "description": "详细的场景描述(50字以内)",
                    "activity_level": "活动水平(静态/动态/高动态)",
                    "lighting_condition": "光照条件(明亮/昏暗/背光等)",
                    "composition": "构图特点(特写/远景/俯视等)",
                    "color_tone": "色调特点(暖色调/冷色调/单色等)",
                    "confidence": 0.85
                }}
                
                <|user|>
                请分析这一帧的视觉内容，返回标准JSON格式：

                图像内容：[IMAGE]
                """
                
                # 构建消息
                messages = [
                    HumanMessage(
                        content=[
                            {"type": "text", "text": prompt_template.replace("[IMAGE]", "")},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                        ]
                    )
                ]
                
                # 调用LLM with timeout
                response = llm.invoke(messages)
                analysis_text = response.content
                
                return analysis_text
                
            except Exception as e:
                retry_count += 1
                logger.warning(f"帧分析失败 (尝试 {retry_count}/{max_retries}): {e}")
                
                if retry_count >= max_retries:
                    logger.error(f"帧分析最终失败: {e}")
                    # 返回默认分析结果
                    return '{"scene_type": "unknown", "main_objects": [], "visual_themes": [], "text_content": "", "description": "分析失败", "activity_level": "unknown", "lighting_condition": "unknown", "composition": "unknown", "color_tone": "unknown", "confidence": 0.0}'
                
                # 等待后重试
                await asyncio.sleep(2)
        
        return '{"scene_type": "unknown", "main_objects": [], "visual_themes": [], "text_content": "", "description": "分析失败", "activity_level": "unknown", "lighting_condition": "unknown", "composition": "unknown", "color_tone": "unknown", "confidence": 0.0}'
    
    def _parse_frame_analysis(self, analysis_text: str, frame: FrameInfo) -> Dict[str, Any]:
        """
        解析帧分析结果
        """
        try:
            # 尝试解析JSON
            import re
            
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                analysis_data = json.loads(json_str)
            else:
                # 如果没有找到JSON，创建默认结构
                analysis_data = self._create_fallback_analysis(analysis_text)
            
            # 标准化结果格式
            result = {
                "frame_number": frame.frame_number,
                "timestamp": frame.timestamp,
                "scene_type": analysis_data.get("scene_type", "unknown"),
                "detected_objects": analysis_data.get("main_objects", []),
                "visual_themes": analysis_data.get("visual_themes", []),
                "text_content": analysis_data.get("text_content", ""),
                "description": analysis_data.get("description", ""),
                "activity_level": analysis_data.get("activity_level", "unknown"),
                "lighting_condition": analysis_data.get("lighting_condition", "unknown"),
                "composition": analysis_data.get("composition", "unknown"),
                "color_tone": analysis_data.get("color_tone", "unknown"),
                "confidence": float(analysis_data.get("confidence", 0.5)),
                "quality_metrics": {
                    "brightness": frame.brightness,
                    "contrast": frame.contrast,
                    "sharpness": frame.sharpness
                },
                "key_frame_reason": frame.key_frame_reason
            }
            
            return result
            
        except Exception as e:
            logger.warning(f"解析帧分析结果失败: {e}")
            return self._create_fallback_analysis(analysis_text, frame)
    
    def _create_fallback_analysis(self, text: str, frame: FrameInfo = None) -> Dict[str, Any]:
        """
        创建后备分析结果
        """
        return {
            "frame_number": frame.frame_number if frame else 0,
            "timestamp": frame.timestamp if frame else 0.0,
            "scene_type": "unknown",
            "detected_objects": [],
            "visual_themes": [],
            "text_content": "",
            "description": text[:100] if text else "分析失败",
            "activity_level": "unknown",
            "lighting_condition": "unknown", 
            "composition": "unknown",
            "color_tone": "unknown",
            "confidence": 0.3,
            "quality_metrics": {
                "brightness": frame.brightness if frame else 0.0,
                "contrast": frame.contrast if frame else 0.0,
                "sharpness": frame.sharpness if frame else 0.0
            },
            "key_frame_reason": frame.key_frame_reason if frame else ""
        }
    
    def _detect_scene_changes(self, frame_analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        检测场景变化
        """
        scene_changes = []
        
        if len(frame_analyses) < 2:
            return scene_changes
        
        prev_scene = None
        for analysis in frame_analyses:
            current_scene = analysis.get("scene_type", "unknown")
            
            if prev_scene and prev_scene != current_scene:
                scene_changes.append({
                    "timestamp": analysis.get("timestamp", 0.0),
                    "frame_number": analysis.get("frame_number", 0),
                    "from_scene": prev_scene,
                    "to_scene": current_scene,
                    "change_type": "scene_transition"
                })
            
            prev_scene = current_scene
        
        return scene_changes
    
    async def _generate_video_summary(self, frame_analyses: List[Dict[str, Any]]) -> str:
        """
        生成视频级别的分析摘要
        """
        try:
            if not frame_analyses:
                return "无法生成摘要：没有成功分析的帧"
            
            # 收集关键信息
            scene_types = [f.get("scene_type", "unknown") for f in frame_analyses]
            descriptions = [f.get("description", "") for f in frame_analyses if f.get("description")]
            
            # 统计最常见的场景类型
            from collections import Counter
            scene_counter = Counter(scene_types)
            dominant_scene = scene_counter.most_common(1)[0][0] if scene_counter else "unknown"
            
            # 生成简单摘要
            summary = f"视频主要场景类型：{dominant_scene}。"
            
            if len(descriptions) > 0:
                # 选择几个代表性描述
                sample_descriptions = descriptions[:3]
                summary += f"关键场景：{'; '.join(sample_descriptions)}。"
            
            summary += f"共分析 {len(frame_analyses)} 个关键帧。"
            
            return summary
            
        except Exception as e:
            logger.error(f"生成视频摘要失败: {e}")
            return f"摘要生成失败：{str(e)}"
    
    async def analyze_scene_sequence(self, frames: List[FrameInfo]) -> Dict[str, Any]:
        """
        分析场景序列，识别视频的故事结构
        """
        try:
            logger.info("开始场景序列分析...")
            
            # 先进行基础帧分析
            frame_results = await self.analyze_video_frames(frames)
            
            if not frame_results.get("frame_analyses"):
                return {"error": "没有成功分析的帧"}
            
            # 分析场景序列
            sequences = self._identify_scene_sequences(frame_results["frame_analyses"])
            
            # 分析故事结构
            story_structure = self._analyze_story_structure(sequences)
            
            return {
                "scene_sequences": sequences,
                "story_structure": story_structure,
                "total_scenes": len(sequences),
                "analysis_metadata": {
                    "model_used": self.model_name,
                    "analysis_type": "scene_sequence"
                }
            }
            
        except Exception as e:
            logger.error(f"场景序列分析失败: {e}")
            return {"error": str(e)}
    
    def _identify_scene_sequences(self, frame_analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        识别场景序列
        """
        sequences = []
        current_sequence = None
        
        for analysis in frame_analyses:
            scene_type = analysis.get("scene_type", "unknown")
            timestamp = analysis.get("timestamp", 0.0)
            
            if current_sequence is None or current_sequence["scene_type"] != scene_type:
                # 开始新序列
                if current_sequence:
                    current_sequence["end_time"] = prev_timestamp
                    current_sequence["duration"] = current_sequence["end_time"] - current_sequence["start_time"]
                    sequences.append(current_sequence)
                
                current_sequence = {
                    "scene_type": scene_type,
                    "start_time": timestamp,
                    "start_frame": analysis.get("frame_number", 0),
                    "frames": [analysis]
                }
            else:
                # 继续当前序列
                current_sequence["frames"].append(analysis)
            
            prev_timestamp = timestamp
        
        # 添加最后一个序列
        if current_sequence:
            current_sequence["end_time"] = prev_timestamp
            current_sequence["duration"] = current_sequence["end_time"] - current_sequence["start_time"]
            sequences.append(current_sequence)
        
        return sequences
    
    def _analyze_story_structure(self, sequences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析故事结构
        """
        if not sequences:
            return {"structure": "unknown", "phases": []}
        
        total_duration = sum(seq.get("duration", 0) for seq in sequences)
        
        # 简单的三段式结构分析
        structure_phases = []
        cumulative_time = 0
        
        for i, seq in enumerate(sequences):
            duration = seq.get("duration", 0)
            cumulative_time += duration
            progress = cumulative_time / total_duration if total_duration > 0 else 0
            
            if progress <= 0.33:
                phase = "开始"
            elif progress <= 0.66:
                phase = "发展"
            else:
                phase = "结尾"
            
            structure_phases.append({
                "sequence_index": i,
                "scene_type": seq.get("scene_type", "unknown"),
                "phase": phase,
                "start_time": seq.get("start_time", 0),
                "duration": duration,
                "progress": progress
            })
        
        return {
            "structure": "三段式",
            "phases": structure_phases,
            "total_duration": total_duration,
            "scene_count": len(sequences)
        }


# 创建全局实例
video_vision_service = VideoVisionService() 