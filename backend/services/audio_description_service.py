import logging
import re
from pathlib import Path
from typing import Dict, Optional
import librosa
import numpy as np
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)

class AudioDescriptionService:
    """音频描述生成服务，使用Qwen2.5模型分析音频内容"""
    
    def __init__(self, model_name: str = "qwen2.5vl:7b", ollama_url: str = "http://host.docker.internal:11435"):
        self.model_name = model_name
        self.ollama_url = ollama_url
        
    def extract_audio_features(self, audio_path: Path) -> Dict:
        """提取音频的基础特征用于AI分析"""
        try:
            # 加载音频文件
            y, sr = librosa.load(str(audio_path), sr=None, duration=30.0)  # 只分析前30秒
            
            # 提取基础特征
            duration = len(y) / sr
            
            # 音频强度特征
            rms = librosa.feature.rms(y=y)[0]
            avg_amplitude = np.mean(rms)
            max_amplitude = np.max(rms)
            
            # 频谱特征
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            avg_spectral_centroid = np.mean(spectral_centroids)
            
            # 零交叉率
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            avg_zcr = np.mean(zcr)
            
            # 频谱滚降
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            avg_spectral_rolloff = np.mean(spectral_rolloff)
            
            # MFCC特征
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            mfcc_means = np.mean(mfccs, axis=1)
            
            # 节拍检测
            try:
                tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            except Exception:
                tempo = 0
                beats = []
            
            return {
                "duration": float(duration),
                "sample_rate": int(sr),
                "avg_amplitude": float(avg_amplitude),
                "max_amplitude": float(max_amplitude),
                "avg_spectral_centroid": float(avg_spectral_centroid),
                "avg_zero_crossing_rate": float(avg_zcr),
                "avg_spectral_rolloff": float(avg_spectral_rolloff),
                "mfcc_features": mfcc_means.tolist(),
                "tempo": float(tempo) if tempo > 0 else None,
                "beat_count": len(beats) if beats is not None else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to extract audio features from {audio_path}: {e}")
            return {}
    
    async def generate_description(self, audio_path: Path, audio_properties: Dict = None) -> Dict:
        """生成音频的智能描述"""
        try:
            logger.info(f"Initializing LLM for audio analysis (model: {self.model_name})...")
            
            # 提取音频特征
            if not audio_properties:
                audio_properties = self.extract_audio_features(audio_path)
            
            # 初始化Ollama LLM
            llm = ChatOllama(
                base_url=self.ollama_url,
                model=self.model_name,
                temperature=0.1
            )
            
            # 创建音频分析提示模板
            prompt_template = ChatPromptTemplate.from_template("""
            <|system|>
            你是一个专业的音频分析专家。你的任务是基于音频的技术特征分析音频内容的特点和可能的类型。
            你必须严格遵守以下规则：
            1. 分析必须基于提供的音频技术特征数据
            2. 提供准确、专业的音频内容判断
            3. 识别音频的可能类型（如音乐、语音、环境音等）
            4. 分析音频的质量和特点
            5. 用中文回答，语言要专业但通俗易懂
            6. 分析长度控制在300字以内

            <|user|>
            请基于以下音频技术特征，详细分析这个音频文件：

            音频基础信息：
            - 时长: {duration:.2f} 秒
            - 采样率: {sample_rate} Hz
            - 平均振幅: {avg_amplitude:.4f}
            - 最大振幅: {max_amplitude:.4f}

            频谱特征：
            - 平均频谱质心: {avg_spectral_centroid:.2f} Hz
            - 平均零交叉率: {avg_zero_crossing_rate:.4f}
            - 平均频谱滚降: {avg_spectral_rolloff:.2f} Hz

            音乐特征：
            - 节拍检测: {tempo} BPM (如果适用)
            - 节拍数量: {beat_count}

            MFCC特征摘要：
            - 前3个MFCC系数: {mfcc_summary}

            请分析：
            1. 音频内容的可能类型（音乐、语音、环境音、混合等）
            2. 音频质量评估
            3. 音频的频率特征和动态特征
            4. 可能的使用场景或来源
            5. 音频的整体特点和建议标签
            """)
            
            # 格式化MFCC特征摘要
            mfcc_features = audio_properties.get('mfcc_features', [])
            mfcc_summary = ", ".join([f"{x:.3f}" for x in mfcc_features[:3]]) if mfcc_features else "无数据"
            
            # 准备提示数据
            prompt_data = {
                "duration": audio_properties.get('duration', 0),
                "sample_rate": audio_properties.get('sample_rate', 0),
                "avg_amplitude": audio_properties.get('avg_amplitude', 0),
                "max_amplitude": audio_properties.get('max_amplitude', 0),
                "avg_spectral_centroid": audio_properties.get('avg_spectral_centroid', 0),
                "avg_zero_crossing_rate": audio_properties.get('avg_zero_crossing_rate', 0),
                "avg_spectral_rolloff": audio_properties.get('avg_spectral_rolloff', 0),
                "tempo": audio_properties.get('tempo', '未检测到') or '未检测到',
                "beat_count": audio_properties.get('beat_count', 0),
                "mfcc_summary": mfcc_summary
            }
            
            # 创建完整提示
            prompt = prompt_template.format(**prompt_data)
            
            logger.info("Invoking LLM for audio analysis...")
            
            # 调用LLM
            response = await llm.ainvoke(prompt)
            
            if hasattr(response, 'content'):
                description = response.content.strip()
            else:
                description = str(response).strip()
            
            logger.info("Successfully generated audio description from LLM.")
            
            # 清理模型输出中可能包含的特殊标签
            cleaned_description = re.sub(r"<think>.*?</think>", "", description, flags=re.DOTALL)
            cleaned_description = cleaned_description.strip()
            
            # 解析描述内容，提取结构化信息
            parsed_result = self._parse_description(cleaned_description, audio_properties)
            
            return {
                "success": True,
                "description": cleaned_description,
                "parsed_analysis": parsed_result,
                "technical_features": audio_properties
            }
                
        except Exception as e:
            logger.error(f"Error generating audio description: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "description": "音频AI分析失败"
            }
    
    def _parse_description(self, description: str, audio_properties: Dict) -> Dict:
        """解析描述文本，提取结构化信息"""
        try:
            # 分析音频类型
            audio_type = self._classify_audio_type(description, audio_properties)
            
            # 提取质量评估
            quality_assessment = self._assess_quality(description, audio_properties)
            
            # 提取特征标签
            feature_tags = self._extract_feature_tags(description)
            
            # 使用场景推测
            usage_scenarios = self._suggest_usage_scenarios(description, audio_type)
            
            return {
                "audio_type": audio_type,
                "quality_assessment": quality_assessment,
                "feature_tags": feature_tags,
                "usage_scenarios": usage_scenarios,
                "analysis_confidence": "基于技术特征分析"
            }
            
        except Exception as e:
            logger.error(f"Error parsing audio description: {e}")
            return {
                "audio_type": "未知",
                "quality_assessment": "无法评估",
                "feature_tags": [],
                "usage_scenarios": [],
                "analysis_confidence": "分析失败"
            }
    
    def _classify_audio_type(self, description: str, properties: Dict) -> str:
        """基于描述和技术特征分类音频类型"""
        desc_lower = description.lower()
        
        # 基于描述内容判断
        if any(word in desc_lower for word in ['音乐', '歌曲', '乐器', '旋律', '节奏', '音乐性']):
            return "音乐"
        elif any(word in desc_lower for word in ['语音', '说话', '讲话', '对话', '演讲', '人声']):
            return "语音/对话"
        elif any(word in desc_lower for word in ['环境', '背景', '自然', '噪声']):
            return "环境音"
        elif any(word in desc_lower for word in ['混合', '复合', '多种']):
            return "混合音频"
        
        # 基于技术特征判断
        zcr = properties.get('avg_zero_crossing_rate', 0)
        spectral_centroid = properties.get('avg_spectral_centroid', 0)
        tempo = properties.get('tempo', 0)
        
        if tempo and tempo > 60:  # 有明显节拍
            return "音乐"
        elif zcr > 0.1:  # 高零交叉率通常表示语音
            return "语音"
        elif spectral_centroid < 2000:  # 低频为主
            return "环境音/低频音"
        else:
            return "未分类音频"
    
    def _assess_quality(self, description: str, properties: Dict) -> str:
        """评估音频质量"""
        desc_lower = description.lower()
        
        # 基于描述判断
        if any(word in desc_lower for word in ['高质量', '清晰', '优质', '良好']):
            return "高质量"
        elif any(word in desc_lower for word in ['低质量', '模糊', '噪声', '失真']):
            return "低质量"
        
        # 基于技术特征判断
        sample_rate = properties.get('sample_rate', 0)
        avg_amplitude = properties.get('avg_amplitude', 0)
        
        if sample_rate >= 44100 and avg_amplitude > 0.01:
            return "良好"
        elif sample_rate >= 22050:
            return "中等"
        else:
            return "一般"
    
    def _extract_feature_tags(self, description: str) -> list:
        """提取特征标签"""
        tags = []
        desc_lower = description.lower()
        
        feature_keywords = {
            "高频": ["高频", "明亮", "清脆"],
            "低频": ["低频", "低沉", "厚重"],
            "动态": ["动态", "变化", "起伏"],
            "稳定": ["稳定", "平稳", "均匀"],
            "节奏性": ["节奏", "节拍", "律动"],
            "连续性": ["连续", "持续", "流畅"]
        }
        
        for tag, keywords in feature_keywords.items():
            if any(keyword in desc_lower for keyword in keywords):
                tags.append(tag)
        
        return tags[:5]  # 限制标签数量
    
    def _suggest_usage_scenarios(self, description: str, audio_type: str) -> list:
        """建议使用场景"""
        scenarios = []
        desc_lower = description.lower()
        
        scenario_mapping = {
            "音乐": ["音乐播放", "背景音乐", "娱乐欣赏", "音乐制作"],
            "语音/对话": ["语音识别", "会议记录", "播客内容", "教育培训"],
            "环境音": ["环境监测", "声学分析", "背景音效", "自然录音"],
            "混合音频": ["多媒体制作", "综合分析", "音频编辑", "内容创作"]
        }
        
        scenarios = scenario_mapping.get(audio_type, ["通用音频处理"])
        
        # 基于描述内容调整
        if "高质量" in desc_lower:
            scenarios.append("专业制作")
        if "清晰" in desc_lower:
            scenarios.append("语音处理")
        
        return scenarios[:4]  # 限制场景数量
    
    async def generate_simple_description(self, audio_path: Path, audio_properties: Dict = None) -> str:
        """生成简单的音频描述"""
        try:
            result = await self.generate_description(audio_path, audio_properties)
            return result.get("description", "无法生成音频描述")
        except Exception as e:
            logger.error(f"Error generating simple audio description: {e}")
            return "音频AI分析失败" 