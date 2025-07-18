"""
视频音频分析服务
基于现有的音频分析基础设施，为视频分析提供音频语义分析能力
集成Whisper、音频增强、文本优化等服务
"""
import logging
import asyncio
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import librosa
import numpy as np
from datetime import datetime, timezone
import json
import re

# 延迟导入，避免初始化时的依赖问题
# from backend.services.audio_description_service import AudioDescriptionService
# from backend.services.whisper_service import WhisperService
# from backend.services.audio_enhancement import AudioEnhancementService
# from backend.services.text_optimization_service import TextOptimizationService
# from backend.services.llm_service import LLMService

logger = logging.getLogger("service")


class VideoAudioService:
    """
    视频音频分析服务
    专门处理视频中的音频内容分析
    """
    
    def __init__(self):
        # 延迟初始化服务，避免导入时的依赖问题
        self._audio_service = None
        self._whisper_service = None
        self._audio_enhancement = None
        self._text_optimizer = None
        self._llm_service = None
        logger.info("🎵 视频音频分析服务初始化完成")
    
    @property
    def audio_service(self):
        """延迟加载音频服务"""
        if self._audio_service is None:
            from backend.services.audio_description_service import AudioDescriptionService
            self._audio_service = AudioDescriptionService(enable_preprocessing=True)
        return self._audio_service
    
    @property
    def whisper_service(self):
        """延迟加载Whisper服务"""
        if self._whisper_service is None:
            from backend.services.whisper_service import WhisperService
            self._whisper_service = WhisperService.get_instance()
        return self._whisper_service
    
    @property
    def audio_enhancement(self):
        """延迟加载音频增强服务"""
        if self._audio_enhancement is None:
            from backend.services.audio_enhancement import AudioEnhancementService
            self._audio_enhancement = AudioEnhancementService()
        return self._audio_enhancement
    
    @property
    def text_optimizer(self):
        """延迟加载文本优化服务"""
        if self._text_optimizer is None:
            from backend.services.text_optimization_service import TextOptimizationService
            self._text_optimizer = TextOptimizationService()
        return self._text_optimizer
    
    @property
    def llm_service(self):
        """延迟加载LLM服务"""
        if self._llm_service is None:
            from backend.services.llm_service import LLMService
            self._llm_service = LLMService()
        return self._llm_service
    
    async def extract_audio_from_video(self, video_path: Path, output_dir: Path) -> Path:
        """
        从视频中提取音频
        
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
            
        Returns:
            提取的音频文件路径
        """
        try:
            logger.info(f"开始从视频提取音频: {video_path.name}")
            
            # 确保输出目录存在
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成音频文件名
            audio_filename = f"{video_path.stem}_audio.wav"
            audio_path = output_dir / audio_filename
            
            # 使用ffmpeg提取音频
            cmd = [
                "ffmpeg", "-i", str(video_path),
                "-vn",  # 不包含视频
                "-acodec", "pcm_s16le",  # 16位PCM编码
                "-ar", "16000",  # 16kHz采样率（Whisper推荐）
                "-ac", "1",  # 单声道
                "-y",  # 覆盖输出文件
                str(audio_path)
            ]
            
            logger.info(f"执行音频提取命令: {' '.join(cmd)}")
            
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"音频提取失败: {result.stderr}")
            
            if not audio_path.exists():
                raise FileNotFoundError(f"音频文件未生成: {audio_path}")
            
            # 获取音频信息
            audio_info = self._get_audio_info(audio_path)
            
            logger.info(f"音频提取成功: {audio_filename}")
            logger.info(f"音频信息: {audio_info['duration']:.2f}秒, {audio_info['sample_rate']}Hz")
            
            return audio_path
            
        except Exception as e:
            logger.error(f"音频提取失败: {e}")
            raise
    
    def _get_audio_info(self, audio_path: Path) -> Dict[str, Any]:
        """获取音频基本信息"""
        try:
            duration = librosa.get_duration(path=str(audio_path))
            y, sr = librosa.load(str(audio_path), sr=None, duration=1.0)  # 只加载1秒用于获取采样率
            
            return {
                "duration": duration,
                "sample_rate": sr,
                "file_size": audio_path.stat().st_size,
                "format": "wav"
            }
        except Exception as e:
            logger.error(f"获取音频信息失败: {e}")
            return {"duration": 0, "sample_rate": 0, "file_size": 0, "format": "unknown"}
    
    async def analyze_video_audio(self, video_path: Path, output_dir: Path) -> Dict[str, Any]:
        """
        分析视频音频内容
        
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
            
        Returns:
            音频分析结果
        """
        try:
            logger.info(f"开始视频音频分析: {video_path.name}")
            
            # 1. 从视频提取音频
            logger.info("第1步：提取音频")
            audio_path = await self.extract_audio_from_video(video_path, output_dir)
            
            # 2. 基础音频分析
            logger.info("第2步：基础音频分析")
            basic_analysis = self.audio_service.analyze_audio(audio_path)
            
            # 3. 增强语音识别
            logger.info("第3步：增强语音识别")
            enhanced_speech = await self._enhanced_speech_recognition(audio_path)
            
            # 4. 音频内容语义分析
            logger.info("第4步：音频内容语义分析")
            semantic_analysis = await self._analyze_audio_semantics(enhanced_speech)
            
            # 5. 时间轴分析
            logger.info("第5步：时间轴分析")
            timeline_analysis = await self._analyze_audio_timeline(enhanced_speech)
            
            # 6. 构建完整分析结果
            analysis_result = {
                "audio_extraction": {
                    "extracted_audio_path": str(audio_path),
                    "audio_info": self._get_audio_info(audio_path),
                    "extraction_success": True
                },
                "basic_analysis": basic_analysis,
                "enhanced_speech": enhanced_speech,
                "semantic_analysis": semantic_analysis,
                "timeline_analysis": timeline_analysis,
                "analysis_metadata": {
                    "video_file": video_path.name,
                    "processing_timestamp": datetime.now(timezone.utc).isoformat(),
                    "analysis_type": "video_audio_semantic",
                    "services_used": [
                        "audio_extraction",
                        "whisper_recognition", 
                        "semantic_analysis",
                        "timeline_analysis"
                    ]
                }
            }
            
            logger.info(f"视频音频分析完成: {video_path.name}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"视频音频分析失败: {e}")
            return {
                "error": str(e),
                "audio_extraction": {"extraction_success": False},
                "basic_analysis": {},
                "enhanced_speech": {},
                "semantic_analysis": {},
                "timeline_analysis": {},
                "analysis_metadata": {
                    "video_file": video_path.name if video_path else "unknown",
                    "error_timestamp": datetime.now(timezone.utc).isoformat(),
                    "analysis_type": "video_audio_semantic"
                }
            }
    
    async def _enhanced_speech_recognition(self, audio_path: Path) -> Dict[str, Any]:
        """
        增强语音识别，包含分段和详细时间戳
        """
        try:
            logger.info("执行增强语音识别...")
            
            # 使用现有的音频分析服务
            speech_result = self.audio_service.speech_to_text(audio_path)
            
            if not speech_result.get("success"):
                return {
                    "success": False,
                    "error": speech_result.get("error", "语音识别失败"),
                    "segments": [],
                    "full_text": "",
                    "language": "unknown"
                }
            
            # 增强分段信息
            segments = speech_result.get("segments", [])
            enhanced_segments = []
            
            for segment in segments:
                enhanced_segment = {
                    "id": segment.get("id", 0),
                    "start_time": segment.get("start", 0.0),
                    "end_time": segment.get("end", 0.0),
                    "duration": segment.get("end", 0.0) - segment.get("start", 0.0),
                    "text": segment.get("text", "").strip(),
                    "confidence": segment.get("avg_logprob", 0.0),
                    "no_speech_prob": segment.get("no_speech_prob", 0.0),
                    "words": segment.get("words", [])  # 如果有词级时间戳
                }
                enhanced_segments.append(enhanced_segment)
            
            # 生成完整文本
            full_text = speech_result.get("transcribed_text", "")
            
            # 语言检测
            detected_language = speech_result.get("language_detected", "unknown")
            
            enhanced_result = {
                "success": True,
                "segments": enhanced_segments,
                "segments_count": len(enhanced_segments),
                "full_text": full_text,
                "language": detected_language,
                "total_duration": max([s.get("end_time", 0) for s in enhanced_segments], default=0),
                "confidence": speech_result.get("confidence", 0.0),
                "model_info": speech_result.get("model_info", {}),
                "preprocessing_info": speech_result.get("preprocessing_info", {})
            }
            
            logger.info(f"增强语音识别完成: {len(enhanced_segments)}个片段")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"增强语音识别失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "segments": [],
                "full_text": "",
                "language": "unknown"
            }
    
    async def _analyze_audio_semantics(self, speech_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析音频内容的语义信息
        """
        try:
            logger.info("开始音频语义分析...")
            
            if not speech_result.get("success") or not speech_result.get("full_text"):
                return {
                    "success": False,
                    "error": "没有有效的语音识别结果",
                    "content_analysis": {},
                    "emotion_analysis": {},
                    "topic_analysis": {},
                    "speaker_analysis": {}
                }
            
            full_text = speech_result.get("full_text", "")
            segments = speech_result.get("segments", [])
            
            # 1. 内容分类分析
            content_analysis = await self._analyze_content_type(full_text)
            
            # 2. 情感分析
            emotion_analysis = await self._analyze_emotions(full_text, segments)
            
            # 3. 话题分析
            topic_analysis = await self._analyze_topics(full_text)
            
            # 4. 说话人分析（基于音频特征）
            speaker_analysis = await self._analyze_speakers(segments)
            
            semantic_result = {
                "success": True,
                "content_analysis": content_analysis,
                "emotion_analysis": emotion_analysis,
                "topic_analysis": topic_analysis,
                "speaker_analysis": speaker_analysis,
                "text_statistics": {
                    "total_words": len(full_text.split()),
                    "total_characters": len(full_text),
                    "average_segment_length": np.mean([len(s.get("text", "")) for s in segments]) if segments else 0,
                    "speech_rate": len(full_text.split()) / speech_result.get("total_duration", 1) * 60  # 词/分钟
                }
            }
            
            logger.info("音频语义分析完成")
            return semantic_result
            
        except Exception as e:
            logger.error(f"音频语义分析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "content_analysis": {},
                "emotion_analysis": {},
                "topic_analysis": {},
                "speaker_analysis": {}
            }
    
    async def _analyze_content_type(self, text: str) -> Dict[str, Any]:
        """分析音频内容类型"""
        try:
            # 使用LLM分析内容类型
            prompt = f"""
            请分析以下音频转录文本的内容类型和特征：

            文本内容：
            {text[:1000]}...

            请按照以下JSON格式返回分析结果：
            {{
                "content_type": "对话/演讲/教学/娱乐/新闻/其他",
                "content_style": "正式/非正式/学术/口语化",
                "main_themes": ["主题1", "主题2", "主题3"],
                "content_quality": "高/中/低",
                "estimated_audience": "目标受众描述",
                "confidence": 0.85
            }}
            """
            
            response = await self.llm_service.generate_response(prompt)
            
            # 解析JSON响应
            try:
                content_analysis = json.loads(response)
            except json.JSONDecodeError:
                # 如果JSON解析失败，创建基础分析
                content_analysis = {
                    "content_type": "unknown",
                    "content_style": "unknown",
                    "main_themes": [],
                    "content_quality": "unknown",
                    "estimated_audience": "unknown",
                    "confidence": 0.3
                }
            
            return content_analysis
            
        except Exception as e:
            logger.error(f"内容类型分析失败: {e}")
            return {
                "content_type": "unknown",
                "content_style": "unknown",
                "main_themes": [],
                "content_quality": "unknown",
                "estimated_audience": "unknown",
                "confidence": 0.0
            }
    
    async def _analyze_emotions(self, full_text: str, segments: List[Dict]) -> Dict[str, Any]:
        """分析情感变化"""
        try:
            # 整体情感分析
            overall_emotion = await self._analyze_text_emotion(full_text)
            
            # 分段情感分析
            segment_emotions = []
            for segment in segments[:10]:  # 限制分析前10个片段
                if segment.get("text"):
                    emotion = await self._analyze_text_emotion(segment["text"])
                    segment_emotions.append({
                        "segment_id": segment.get("id", 0),
                        "start_time": segment.get("start_time", 0),
                        "end_time": segment.get("end_time", 0),
                        "emotion": emotion.get("dominant_emotion", "neutral"),
                        "confidence": emotion.get("confidence", 0.0)
                    })
            
            # 情感变化分析
            emotion_changes = self._detect_emotion_changes(segment_emotions)
            
            return {
                "overall_emotion": overall_emotion,
                "segment_emotions": segment_emotions,
                "emotion_changes": emotion_changes,
                "emotion_statistics": self._calculate_emotion_statistics(segment_emotions)
            }
            
        except Exception as e:
            logger.error(f"情感分析失败: {e}")
            return {
                "overall_emotion": {"dominant_emotion": "unknown", "confidence": 0.0},
                "segment_emotions": [],
                "emotion_changes": [],
                "emotion_statistics": {}
            }
    
    async def _analyze_text_emotion(self, text: str) -> Dict[str, Any]:
        """分析文本情感"""
        try:
            prompt = f"""
            请分析以下文本的情感倾向：

            文本：{text[:500]}

            请返回JSON格式：
            {{
                "dominant_emotion": "positive/negative/neutral/excited/sad/angry/surprised",
                "confidence": 0.85,
                "emotion_scores": {{
                    "positive": 0.7,
                    "negative": 0.1,
                    "neutral": 0.2
                }}
            }}
            """
            
            response = await self.llm_service.generate_response(prompt)
            
            try:
                emotion_result = json.loads(response)
            except json.JSONDecodeError:
                emotion_result = {
                    "dominant_emotion": "neutral",
                    "confidence": 0.3,
                    "emotion_scores": {"neutral": 1.0}
                }
            
            return emotion_result
            
        except Exception as e:
            logger.error(f"文本情感分析失败: {e}")
            return {
                "dominant_emotion": "unknown",
                "confidence": 0.0,
                "emotion_scores": {}
            }
    
    def _detect_emotion_changes(self, segment_emotions: List[Dict]) -> List[Dict]:
        """检测情感变化点"""
        changes = []
        
        for i in range(1, len(segment_emotions)):
            prev_emotion = segment_emotions[i-1].get("emotion", "neutral")
            curr_emotion = segment_emotions[i].get("emotion", "neutral")
            
            if prev_emotion != curr_emotion:
                changes.append({
                    "timestamp": segment_emotions[i].get("start_time", 0),
                    "from_emotion": prev_emotion,
                    "to_emotion": curr_emotion,
                    "change_type": "emotion_transition"
                })
        
        return changes
    
    def _calculate_emotion_statistics(self, segment_emotions: List[Dict]) -> Dict[str, Any]:
        """计算情感统计"""
        if not segment_emotions:
            return {}
        
        emotions = [s.get("emotion", "neutral") for s in segment_emotions]
        from collections import Counter
        emotion_counts = Counter(emotions)
        
        return {
            "dominant_emotion": emotion_counts.most_common(1)[0][0] if emotion_counts else "neutral",
            "emotion_distribution": dict(emotion_counts),
            "emotion_changes_count": len(self._detect_emotion_changes(segment_emotions)),
            "average_confidence": np.mean([s.get("confidence", 0) for s in segment_emotions])
        }
    
    async def _analyze_topics(self, text: str) -> Dict[str, Any]:
        """分析话题和关键词"""
        try:
            prompt = f"""
            请分析以下文本的主要话题和关键词：

            文本：{text[:1000]}

            请返回JSON格式：
            {{
                "main_topics": ["话题1", "话题2", "话题3"],
                "keywords": ["关键词1", "关键词2", "关键词3"],
                "topic_categories": ["类别1", "类别2"],
                "summary": "简要总结",
                "confidence": 0.85
            }}
            """
            
            response = await self.llm_service.generate_response(prompt)
            
            try:
                topic_result = json.loads(response)
            except json.JSONDecodeError:
                topic_result = {
                    "main_topics": [],
                    "keywords": [],
                    "topic_categories": [],
                    "summary": "话题分析失败",
                    "confidence": 0.3
                }
            
            return topic_result
            
        except Exception as e:
            logger.error(f"话题分析失败: {e}")
            return {
                "main_topics": [],
                "keywords": [],
                "topic_categories": [],
                "summary": "话题分析失败",
                "confidence": 0.0
            }
    
    async def _analyze_speakers(self, segments: List[Dict]) -> Dict[str, Any]:
        """分析说话人特征（基于音频特征推断）"""
        try:
            # 简单的说话人分析（基于片段特征）
            speaker_segments = []
            current_speaker = 1
            
            for segment in segments:
                # 基于音频特征推断说话人（简化版）
                confidence = segment.get("confidence", 0.0)
                duration = segment.get("duration", 0.0)
                
                # 简单的说话人切换检测（基于置信度和时长变化）
                if len(speaker_segments) > 0:
                    prev_confidence = speaker_segments[-1].get("confidence", 0.0)
                    if abs(confidence - prev_confidence) > 0.3:  # 置信度变化较大
                        current_speaker += 1
                
                speaker_segments.append({
                    "segment_id": segment.get("id", 0),
                    "speaker_id": current_speaker,
                    "start_time": segment.get("start_time", 0),
                    "end_time": segment.get("end_time", 0),
                    "confidence": confidence,
                    "text": segment.get("text", "")
                })
            
            # 统计说话人信息
            speaker_stats = {}
            for seg in speaker_segments:
                speaker_id = seg["speaker_id"]
                if speaker_id not in speaker_stats:
                    speaker_stats[speaker_id] = {
                        "total_duration": 0,
                        "segment_count": 0,
                        "total_words": 0
                    }
                
                speaker_stats[speaker_id]["total_duration"] += seg.get("end_time", 0) - seg.get("start_time", 0)
                speaker_stats[speaker_id]["segment_count"] += 1
                speaker_stats[speaker_id]["total_words"] += len(seg.get("text", "").split())
            
            return {
                "speaker_segments": speaker_segments,
                "estimated_speakers": len(speaker_stats),
                "speaker_statistics": speaker_stats,
                "analysis_method": "audio_feature_based"
            }
            
        except Exception as e:
            logger.error(f"说话人分析失败: {e}")
            return {
                "speaker_segments": [],
                "estimated_speakers": 1,
                "speaker_statistics": {},
                "analysis_method": "failed"
            }
    
    async def _analyze_audio_timeline(self, speech_result: Dict[str, Any]) -> Dict[str, Any]:
        """分析音频时间轴特征"""
        try:
            logger.info("开始音频时间轴分析...")
            
            if not speech_result.get("success"):
                return {
                    "success": False,
                    "error": "没有有效的语音识别结果"
                }
            
            segments = speech_result.get("segments", [])
            total_duration = speech_result.get("total_duration", 0)
            
            # 1. 语音活动分析
            speech_activity = self._analyze_speech_activity(segments, total_duration)
            
            # 2. 节奏分析
            rhythm_analysis = self._analyze_speech_rhythm(segments)
            
            # 3. 停顿分析
            pause_analysis = self._analyze_pauses(segments)
            
            # 4. 语速分析
            speech_rate_analysis = self._analyze_speech_rate(segments)
            
            timeline_result = {
                "success": True,
                "speech_activity": speech_activity,
                "rhythm_analysis": rhythm_analysis,
                "pause_analysis": pause_analysis,
                "speech_rate_analysis": speech_rate_analysis,
                "timeline_statistics": {
                    "total_duration": total_duration,
                    "speech_duration": sum([s.get("duration", 0) for s in segments]),
                    "silence_duration": total_duration - sum([s.get("duration", 0) for s in segments]),
                    "segments_count": len(segments)
                }
            }
            
            logger.info("音频时间轴分析完成")
            return timeline_result
            
        except Exception as e:
            logger.error(f"音频时间轴分析失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _analyze_speech_activity(self, segments: List[Dict], total_duration: float) -> Dict[str, Any]:
        """分析语音活动"""
        if not segments:
            return {"activity_ratio": 0.0, "active_periods": []}
        
        # 计算语音活动比例
        speech_duration = sum([s.get("duration", 0) for s in segments])
        activity_ratio = speech_duration / total_duration if total_duration > 0 else 0
        
        # 识别活跃时段
        active_periods = []
        for segment in segments:
            if segment.get("duration", 0) > 2.0:  # 超过2秒的片段认为是活跃时段
                active_periods.append({
                    "start": segment.get("start_time", 0),
                    "end": segment.get("end_time", 0),
                    "duration": segment.get("duration", 0)
                })
        
        return {
            "activity_ratio": round(activity_ratio, 3),
            "active_periods": active_periods,
            "total_active_periods": len(active_periods)
        }
    
    def _analyze_speech_rhythm(self, segments: List[Dict]) -> Dict[str, Any]:
        """分析语音节奏"""
        if not segments:
            return {"rhythm_type": "unknown", "rhythm_stability": 0.0}
        
        # 计算片段长度变化
        durations = [s.get("duration", 0) for s in segments]
        avg_duration = np.mean(durations)
        duration_std = np.std(durations)
        
        # 节奏稳定性（标准差越小越稳定）
        rhythm_stability = 1.0 - min(duration_std / avg_duration, 1.0) if avg_duration > 0 else 0.0
        
        # 节奏类型判断
        if avg_duration > 10.0:
            rhythm_type = "slow"
        elif avg_duration < 3.0:
            rhythm_type = "fast"
        else:
            rhythm_type = "moderate"
        
        return {
            "rhythm_type": rhythm_type,
            "rhythm_stability": round(rhythm_stability, 3),
            "average_segment_duration": round(avg_duration, 2),
            "duration_variance": round(duration_std, 2)
        }
    
    def _analyze_pauses(self, segments: List[Dict]) -> Dict[str, Any]:
        """分析停顿模式"""
        if len(segments) < 2:
            return {"pause_count": 0, "average_pause_duration": 0.0}
        
        # 计算片段间的停顿
        pauses = []
        for i in range(1, len(segments)):
            prev_end = segments[i-1].get("end_time", 0)
            curr_start = segments[i].get("start_time", 0)
            pause_duration = curr_start - prev_end
            
            if pause_duration > 0.1:  # 大于0.1秒认为是停顿
                pauses.append({
                    "start": prev_end,
                    "end": curr_start,
                    "duration": pause_duration
                })
        
        if not pauses:
            return {"pause_count": 0, "average_pause_duration": 0.0}
        
        avg_pause = np.mean([p["duration"] for p in pauses])
        
        return {
            "pause_count": len(pauses),
            "average_pause_duration": round(avg_pause, 2),
            "total_pause_duration": round(sum([p["duration"] for p in pauses]), 2),
            "longest_pause": round(max([p["duration"] for p in pauses]), 2)
        }
    
    def _analyze_speech_rate(self, segments: List[Dict]) -> Dict[str, Any]:
        """分析语速"""
        if not segments:
            return {"words_per_minute": 0.0, "speech_rate_type": "unknown"}
        
        # 计算每个片段的语速
        segment_rates = []
        for segment in segments:
            text = segment.get("text", "")
            duration = segment.get("duration", 0)
            
            if duration > 0:
                word_count = len(text.split())
                rate = (word_count / duration) * 60  # 词/分钟
                segment_rates.append(rate)
        
        if not segment_rates:
            return {"words_per_minute": 0.0, "speech_rate_type": "unknown"}
        
        avg_rate = np.mean(segment_rates)
        
        # 语速类型判断
        if avg_rate > 180:
            rate_type = "fast"
        elif avg_rate < 120:
            rate_type = "slow"
        else:
            rate_type = "normal"
        
        return {
            "words_per_minute": round(avg_rate, 1),
            "speech_rate_type": rate_type,
            "rate_variance": round(np.std(segment_rates), 1),
            "min_rate": round(min(segment_rates), 1),
            "max_rate": round(max(segment_rates), 1)
        }


# 创建全局实例
video_audio_service = VideoAudioService() 