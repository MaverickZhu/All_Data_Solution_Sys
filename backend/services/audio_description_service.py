import logging
import re
from pathlib import Path
from typing import Dict, Optional
import librosa
import numpy as np
import tempfile
import os
import whisper

logger = logging.getLogger(__name__)

class AudioDescriptionService:
    """音频语音识别服务，使用Whisper模型进行语音转文字"""
    
    def __init__(self, whisper_model: str = "base"):
        self.whisper_model_name = whisper_model
        self._whisper_model = None  # Lazy loading
    
    def _get_whisper_model(self):
        """懒加载Whisper模型"""
        if self._whisper_model is None:
            try:
                logger.info(f"Loading Whisper model: {self.whisper_model_name}")
                self._whisper_model = whisper.load_model(self.whisper_model_name)
                logger.info(f"Whisper model loaded successfully. Multilingual: {self._whisper_model.is_multilingual}")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                raise
        return self._whisper_model
        
    def extract_audio_features(self, audio_path: Path) -> Dict:
        """提取音频的基础特征"""
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
    
    def speech_to_text(self, audio_path: Path) -> Dict:
        """使用Whisper进行语音识别，将音频转换为文字"""
        try:
            logger.info(f"Starting Whisper speech recognition for {audio_path}")
            
            # 获取Whisper模型
            model = self._get_whisper_model()
            
            # 使用Whisper进行转录
            # Whisper会自动处理音频格式转换和预处理
            result = model.transcribe(
                str(audio_path),
                language="zh",  # 首先尝试中文
                task="transcribe",  # 转录任务（而非翻译）
                verbose=False
            )
            
            # 提取转录结果
            transcribed_text = result.get("text", "").strip()
            detected_language = result.get("language", "unknown")
            
            # 如果中文识别结果很短或为空，尝试英文识别
            if len(transcribed_text) < 3:
                logger.info("Chinese transcription result is too short, trying English...")
                result_en = model.transcribe(
                    str(audio_path),
                    language="en",
                    task="transcribe",
                    verbose=False
                )
                
                transcribed_text_en = result_en.get("text", "").strip()
                
                # 选择更长的结果
                if len(transcribed_text_en) > len(transcribed_text):
                    transcribed_text = transcribed_text_en
                    detected_language = result_en.get("language", "en")
                    result = result_en
                    logger.info("Selected English transcription result")
            
            # 如果还是没有好的结果，尝试自动语言检测
            if len(transcribed_text) < 3:
                logger.info("Trying automatic language detection...")
                result_auto = model.transcribe(
                    str(audio_path),
                    task="transcribe",
                    verbose=False
                )
                
                transcribed_text_auto = result_auto.get("text", "").strip()
                
                if len(transcribed_text_auto) > len(transcribed_text):
                    transcribed_text = transcribed_text_auto
                    detected_language = result_auto.get("language", "auto")
                    result = result_auto
                    logger.info("Selected automatic detection result")
            
            if transcribed_text:
                # 计算置信度（基于segments中的置信度信息）
                segments = result.get("segments", [])
                total_confidence = 0
                total_duration = 0
                
                for segment in segments:
                    if 'confidence' in segment and 'end' in segment and 'start' in segment:
                        duration = segment['end'] - segment['start']
                        total_confidence += segment.get('confidence', 0) * duration
                        total_duration += duration
                
                avg_confidence = total_confidence / total_duration if total_duration > 0 else 0
                
                return {
                    "success": True,
                    "transcribed_text": transcribed_text,
                    "confidence": round(avg_confidence, 3),
                    "language_detected": detected_language,
                    "segments": segments,
                    "segments_count": len(segments),
                    "model_info": {
                        "model": self.whisper_model_name,
                        "multilingual": model.is_multilingual
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "No speech content detected in audio",
                    "transcribed_text": "",
                    "confidence": 0,
                    "language_detected": "unknown"
                }
                
        except Exception as e:
            logger.error(f"Whisper speech recognition failed for {audio_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "transcribed_text": "",
                "confidence": 0,
                "language_detected": "unknown"
            }
    
    def detect_audio_content_type(self, audio_features: Dict, speech_result: Dict = None) -> str:
        """检测音频内容类型"""
        try:
            # 如果有语音识别结果，说明很可能是语音内容
            if speech_result and speech_result.get("success") and speech_result.get("transcribed_text"):
                return "speech"
            
            # 基于音频特征的启发式判断
            zero_crossing_rate = audio_features.get("avg_zero_crossing_rate", 0)
            spectral_centroid = audio_features.get("avg_spectral_centroid", 0)
            tempo = audio_features.get("tempo", 0)
            duration = audio_features.get("duration", 0)
            
            if zero_crossing_rate > 0.1:  # 高零交叉率可能是语音
                return "speech"
            elif tempo and tempo > 60:  # 有明显节拍可能是音乐
                return "music"
            elif spectral_centroid > 3000:  # 高频内容可能是音乐
                return "music"
            elif duration < 10:  # 短音频可能是音效
                return "sound_effect"
            else:
                return "unknown"
                
        except Exception as e:
            logger.error(f"Audio content type detection failed: {e}")
            return "unknown"

    def analyze_audio(self, audio_path: Path) -> Dict:
        """分析音频文件，包括特征提取和语音识别"""
        try:
            logger.info(f"Starting comprehensive audio analysis for {audio_path}")
            
            # 提取音频特征
            audio_features = self.extract_audio_features(audio_path)
            
            # 尝试语音识别
            speech_result = self.speech_to_text(audio_path)
            
            # 检测音频内容类型
            content_type = self.detect_audio_content_type(audio_features, speech_result)
            
            return {
                "success": True,
                "audio_features": audio_features,
                "speech_recognition": speech_result,
                "content_type": content_type,
                "analysis_summary": {
                    "file_analyzed": str(audio_path),
                    "has_speech": speech_result.get("success", False),
                    "detected_type": content_type,
                    "processing_time": "completed"
                }
            }
                
        except Exception as e:
            logger.error(f"Error in comprehensive audio analysis: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "audio_features": {},
                "speech_recognition": {
                    "success": False,
                    "error": str(e)
                },
                "content_type": "unknown"
            } 