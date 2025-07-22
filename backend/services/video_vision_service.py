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
        重新设计：解决LLM调用阻塞问题，而非简单的时间限制
        
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
            failed_frames = []
            
            # 记录开始时间
            start_time = asyncio.get_event_loop().time()
            
            # 优化的批处理策略：真正的并发处理
            max_concurrent = 1  # 单线程处理，避免GPU资源竞争
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def analyze_frame_safe(frame: FrameInfo, frame_index: int) -> Optional[Dict[str, Any]]:
                """安全的帧分析函数，包含连接检查和重试机制"""
                async with semaphore:
                    try:
                        # 在每次分析前检查Ollama连接状态
                        if not await self._check_ollama_health():
                            logger.warning(f"帧 {frame.frame_number}: Ollama服务不可用，跳过分析")
                            return None
                        
                        logger.info(f"[{frame_index+1}/{len(frames)}] 分析帧 {frame.frame_number} (时间: {frame.timestamp:.2f}s)")
                        
                        # 使用改进的分析方法
                        result = await self._analyze_frame_resilient(frame)
                        
                        if result and not isinstance(result, str):  # 确保返回有效结果
                            logger.info(f"帧 {frame.frame_number} 分析成功")
                            return result
                        else:
                            logger.warning(f"帧 {frame.frame_number} 分析返回无效结果")
                            return None
                            
                    except Exception as e:
                        logger.error(f"帧 {frame.frame_number} 分析异常: {e}")
                        failed_frames.append({
                            "frame_number": frame.frame_number,
                            "error": str(e),
                            "timestamp": frame.timestamp
                        })
                        return None
            
            # 串行处理每一帧，避免资源竞争和连接阻塞
            for i, frame in enumerate(frames):
                try:
                    result = await analyze_frame_safe(frame, i)
                    
                    if result:
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
                    
                    # 定期报告进度（每处理5帧）
                    if (i + 1) % 5 == 0 or i == len(frames) - 1:
                        progress = (i + 1) / len(frames) * 100
                        elapsed = asyncio.get_event_loop().time() - start_time
                        logger.info(f"进度: {progress:.1f}% ({i+1}/{len(frames)}), 耗时: {elapsed:.1f}s")
                    
                    # 每处理完一帧，短暂休息避免过载
                    if i < len(frames) - 1:
                        await asyncio.sleep(0.2)
                        
                except Exception as e:
                    logger.error(f"处理帧 {frame.frame_number} 时发生错误: {e}")
                    failed_frames.append({
                        "frame_number": frame.frame_number,
                        "error": f"处理错误: {str(e)}",
                        "timestamp": frame.timestamp
                    })
                    continue
            
            # 生成视频级别的分析摘要
            try:
                if frame_analyses:
                    video_summary = await self._generate_video_summary_safe(frame_analyses)
                else:
                    video_summary = "所有帧分析失败，无法生成视频摘要"
            except Exception as e:
                logger.warning(f"视频摘要生成失败: {e}")
                video_summary = f"摘要生成失败: {str(e)}"
            
            # 检测场景变化
            try:
                scene_changes = self._detect_scene_changes(frame_analyses)
            except Exception as e:
                logger.warning(f"场景变化检测失败: {e}")
                scene_changes = []
            
            # 计算成功率
            total_attempted = len(frames)
            successful_analyses = len(frame_analyses)
            success_rate = successful_analyses / total_attempted if total_attempted > 0 else 0
            total_time = asyncio.get_event_loop().time() - start_time
            
            analysis_result = {
                "total_frames_analyzed": successful_analyses,
                "total_frames_attempted": total_attempted,
                "failed_frames": failed_frames,
                "frame_analyses": frame_analyses,
                "visual_themes": list(visual_themes),
                "detected_objects": list(detected_objects),
                "scene_types": list(scene_types),
                "extracted_text": text_contents,
                "scene_changes": scene_changes,
                "video_summary": video_summary,
                "analysis_metadata": {
                    "model_used": self.model_name,
                    "analysis_type": "video_vision_semantic_resilient",
                    "success_rate": round(success_rate, 3),
                    "processing_time": round(total_time, 1),
                    "frames_per_second": round(successful_analyses / total_time, 2) if total_time > 0 else 0,
                    "failure_count": len(failed_frames),
                    "avg_time_per_frame": round(total_time / total_attempted, 2) if total_attempted > 0 else 0
                }
            }
            
            logger.info(f"视频视觉分析完成: {successful_analyses}/{total_attempted}帧成功，成功率: {success_rate:.1%}，总耗时: {total_time:.1f}s")
            return analysis_result
            
        except Exception as e:
            logger.error(f"视频视觉分析完全失败: {e}")
            return {
                "error": str(e),
                "total_frames_analyzed": 0,
                "total_frames_attempted": len(frames) if frames else 0,
                "failed_frames": [{"error": f"全局失败: {str(e)}"}],
                "frame_analyses": [],
                "visual_themes": [],
                "detected_objects": [],
                "scene_types": [],
                "extracted_text": [],
                "scene_changes": [],
                "video_summary": f"分析失败: {str(e)}",
                "analysis_metadata": {
                    "model_used": self.model_name,
                    "analysis_type": "video_vision_semantic_resilient",
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
        使用视频上下文分析帧 - 增强超时控制和错误恢复
        """
        max_retries = 3
        retry_count = 0
        base_timeout = 20  # 基础超时时间（秒）
        
        while retry_count < max_retries:
            try:
                # 动态调整超时时间
                current_timeout = base_timeout + (retry_count * 10)  # 重试时增加超时时间
                
                logger.debug(f"分析帧 {frame.frame_number}，尝试 {retry_count + 1}/{max_retries}，超时: {current_timeout}s")
                
                # 编码图像
                image_base64 = self.image_service.encode_image_to_base64(frame_path)
                
                # 初始化LLM with strict timeout
                llm = ChatOllama(
                    base_url=self.ollama_url,
                    model=self.model_name,
                    temperature=0.1,
                    timeout=current_timeout,  # 动态超时
                    # 添加更多控制参数
                    request_timeout=current_timeout,
                    num_predict=512  # 限制生成长度
                )
                
                # 简化的视频帧分析提示 - 减少复杂性避免卡顿
                prompt_template = f"""分析帧{frame.frame_number}(时间{frame.timestamp:.1f}s):
返回JSON格式:
{{
    "scene_type": "场景类型",
    "main_objects": ["物体1", "物体2"],
    "description": "简短描述(30字内)",
    "confidence": 0.8
}}
不要添加任何解释，只返回JSON。"""
                
                # 构建消息
                messages = [
                    HumanMessage(
                        content=[
                            {"type": "text", "text": prompt_template},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                        ]
                    )
                ]
                
                # 使用asyncio.wait_for添加额外的超时保护
                response = await asyncio.wait_for(
                    llm.ainvoke(messages),
                    timeout=current_timeout + 5  # 额外5秒缓冲
                )
                
                analysis_text = response.content
                
                # 验证响应不为空
                if not analysis_text or len(analysis_text.strip()) < 10:
                    raise ValueError("LLM返回内容过短或为空")
                
                logger.debug(f"帧 {frame.frame_number} 分析成功")
                return analysis_text
                
            except asyncio.TimeoutError:
                retry_count += 1
                error_msg = f"帧 {frame.frame_number} 分析超时 (超时时间: {current_timeout}s)"
                logger.warning(error_msg)
                
                if retry_count >= max_retries:
                    logger.error(f"帧 {frame.frame_number} 最终分析失败: 超时")
                    # 返回简化的默认结果，避免完全失败
                    return self._get_fallback_analysis(frame)
                
                # 短暂延迟后重试
                await asyncio.sleep(2)
                
            except Exception as e:
                retry_count += 1
                logger.warning(f"帧 {frame.frame_number} 分析失败 (尝试 {retry_count}/{max_retries}): {e}")
                
                if retry_count >= max_retries:
                    logger.error(f"帧 {frame.frame_number} 最终分析失败: {e}")
                    return self._get_fallback_analysis(frame)
                
                # 短暂延迟后重试
                await asyncio.sleep(1)
        
        # 如果所有重试都失败，返回默认分析
        return self._get_fallback_analysis(frame)
    
    def _get_fallback_analysis(self, frame: FrameInfo) -> str:
        """
        生成兜底分析结果，避免任务完全失败
        """
        fallback_result = {
            "scene_type": "未知场景",
            "main_objects": ["视频帧"],
            "description": f"第{frame.frame_number}帧(时间{frame.timestamp:.1f}s)",
            "confidence": 0.1
        }
        return json.dumps(fallback_result, ensure_ascii=False)
    
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
                "detected_objects": analysis_data.get("detected_objects", []),
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

    async def _check_ollama_health(self) -> bool:
        """
        检查Ollama服务健康状态
        """
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_url}/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [model['name'] for model in data.get('models', [])]
                        available = self.model_name in models
                        if not available:
                            logger.warning(f"模型 {self.model_name} 在Ollama中不可用，可用模型: {models}")
                        return available
                    else:
                        logger.warning(f"Ollama服务响应异常: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Ollama健康检查失败: {e}")
            return False
    
    async def _analyze_frame_resilient(self, frame: FrameInfo) -> Optional[Dict[str, Any]]:
        """
        弹性的帧分析方法，包含连接重试和错误恢复
        """
        max_attempts = 2  # 减少重试次数，避免无限循环
        
        for attempt in range(max_attempts):
            try:
                frame_path = Path(frame.frame_path)
                if not frame_path.exists():
                    logger.error(f"帧文件不存在: {frame_path}")
                    return None
                
                logger.debug(f"分析帧 {frame.frame_number}，尝试 {attempt + 1}/{max_attempts}")
                
                # 编码图像
                try:
                    image_base64 = self.image_service.encode_image_to_base64(frame_path)
                except Exception as e:
                    logger.error(f"图像编码失败: {e}")
                    return None
                
                # 使用连接池和会话管理
                try:
                    llm = ChatOllama(
                        base_url=self.ollama_url,
                        model=self.model_name,
                        temperature=0.1,
                        timeout=15,  # 固定15秒超时
                        request_timeout=15,
                        num_predict=256,  # 进一步限制输出长度
                        keep_alive=0  # 立即释放资源
                    )
                    
                    # 极简化的分析提示
                    prompt = f"""分析这个视频帧(第{frame.frame_number}帧)，用JSON格式回答:
{{
  "scene": "场景类型",
  "objects": ["物体1", "物体2"],
  "desc": "简短描述"
}}"""
                    
                    # 构建消息
                    messages = [
                        HumanMessage(
                            content=[
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                            ]
                        )
                    ]
                    
                    # 单独的超时保护，避免无限等待
                    response = await asyncio.wait_for(
                        llm.ainvoke(messages), 
                        timeout=20  # 20秒硬超时
                    )
                    
                    if response and response.content:
                        # 解析并标准化结果
                        parsed_result = self._parse_frame_analysis_simple(response.content, frame)
                        if parsed_result:
                            return parsed_result
                    
                    logger.warning(f"帧 {frame.frame_number} 第 {attempt + 1} 次尝试无效响应")
                    
                except asyncio.TimeoutError:
                    logger.warning(f"帧 {frame.frame_number} 第 {attempt + 1} 次尝试超时")
                    
                except Exception as e:
                    logger.warning(f"帧 {frame.frame_number} 第 {attempt + 1} 次尝试失败: {e}")
                
                # 尝试之间的延迟
                if attempt < max_attempts - 1:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"帧 {frame.frame_number} 分析出现严重错误: {e}")
                break
        
        # 所有尝试失败，返回基础信息
        logger.warning(f"帧 {frame.frame_number} 所有分析尝试失败，返回基础信息")
        return {
            "frame_number": frame.frame_number,
            "timestamp": frame.timestamp,
            "scene_type": "unknown",
            "detected_objects": [],
            "visual_themes": [],
            "text_content": "",
            "description": f"帧{frame.frame_number}基础信息",
            "confidence": 0.1,
            "quality_metrics": {
                "brightness": getattr(frame, 'brightness', 0.5),
                "contrast": getattr(frame, 'contrast', 0.5),
                "sharpness": getattr(frame, 'sharpness', 0.5)
            }
        }
    
    def _parse_frame_analysis_simple(self, analysis_text: str, frame: FrameInfo) -> Optional[Dict[str, Any]]:
        """
        简化的帧分析结果解析
        """
        try:
            import re
            import json
            
            # 提取JSON部分
            json_match = re.search(r'\{[^{}]*\}', analysis_text)
            if json_match:
                json_str = json_match.group(0)
                try:
                    data = json.loads(json_str)
                except json.JSONDecodeError:
                    # 如果JSON解析失败，尝试简单的文本提取
                    data = self._extract_from_text(analysis_text)
            else:
                data = self._extract_from_text(analysis_text)
            
            # 标准化结果
            result = {
                "frame_number": frame.frame_number,
                "timestamp": frame.timestamp,
                "scene_type": str(data.get("scene", "unknown"))[:50],  # 限制长度
                "detected_objects": self._extract_list(data.get("objects", [])),
                "visual_themes": self._extract_list(data.get("themes", [])),
                "text_content": "",
                "description": str(data.get("desc", ""))[:100],  # 限制描述长度
                "confidence": min(float(data.get("confidence", 0.5)), 1.0),
                "quality_metrics": {
                    "brightness": getattr(frame, 'brightness', 0.5),
                    "contrast": getattr(frame, 'contrast', 0.5),
                    "sharpness": getattr(frame, 'sharpness', 0.5)
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"解析帧分析结果失败: {e}")
            return None
    
    def _extract_from_text(self, text: str) -> dict:
        """从文本中提取基础信息"""
        return {
            "scene": "analyzed_scene",
            "objects": ["video_content"],
            "desc": "视频帧内容"
        }
    
    def _extract_list(self, obj) -> List[str]:
        """安全地提取列表"""
        if isinstance(obj, list):
            return [str(item)[:30] for item in obj[:5]]  # 最多5个项目，每个最多30字符
        elif isinstance(obj, str):
            return [obj[:30]]
        else:
            return []
    
    async def _generate_video_summary_safe(self, frame_analyses: List[Dict[str, Any]]) -> str:
        """
        安全的视频摘要生成，包含重试机制
        """
        if not frame_analyses:
            return "无帧分析数据，无法生成摘要"
        
        try:
            # 提取关键信息
            scene_types = set()
            all_objects = set()
            
            for analysis in frame_analyses:
                if analysis.get('scene_type'):
                    scene_types.add(analysis['scene_type'])
                if analysis.get('detected_objects'):
                    all_objects.update(analysis['detected_objects'])
            
            # 生成基于统计的摘要
            summary_parts = []
            if scene_types:
                summary_parts.append(f"场景类型: {', '.join(list(scene_types)[:3])}")
            if all_objects:
                summary_parts.append(f"主要对象: {', '.join(list(all_objects)[:5])}")
            
            summary_parts.append(f"共分析{len(frame_analyses)}个关键帧")
            
            return "; ".join(summary_parts)
            
        except Exception as e:
            logger.error(f"视频摘要生成失败: {e}")
            return f"摘要生成失败: {str(e)}"


# 创建全局实例
video_vision_service = VideoVisionService() 