"""
Whisper Speech Recognition Service
优化的语音识别服务，避免重复加载模型，支持GPU加速
"""
import logging
import time
import torch
import whisper
from pathlib import Path
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

class WhisperService:
    """
    全局Whisper模型管理器，避免重复加载，提升性能
    """
    _instance = None
    _model = None
    _device = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @property
    def device(self):
        """获取当前设备"""
        if self._device is None:
            if torch.cuda.is_available():
                self._device = "cuda"
                logger.info(f"🚀 GPU加速可用: {torch.cuda.get_device_name()}")
                logger.info(f"🔧 CUDA版本: {torch.version.cuda}")
                logger.info(f"💾 GPU显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
            else:
                self._device = "cpu"
                logger.warning("⚠️ GPU不可用，回退到CPU模式")
        return self._device
    
    @property
    def model(self):
        """获取模型实例，懒加载"""
        if self._model is None:
            logger.info("🎯 Loading Whisper model...")
            start_time = time.time()
            
            try:
                # 优先使用Large V3模型，提供最佳质量（可通过环境变量配置）
                model_name = os.getenv("WHISPER_MODEL", "large-v3")  # 默认使用large-v3
                
                if self.device == "cuda":
                    # GPU模式：加载模型到GPU，让Whisper自己处理精度
                    logger.info(f"🔥 GPU模式启动中，使用模型: {model_name}")
                    self._model = whisper.load_model(model_name, device=self.device)
                    
                    # 验证GPU使用情况，但不手动转换精度
                    gpu_memory = torch.cuda.memory_allocated() / 1024**3
                    logger.info(f"📊 GPU显存使用: {gpu_memory:.2f}GB")
                    logger.info("✅ 模型已加载到GPU，将在转录时使用FP16")
                    
                else:
                    # CPU模式
                    logger.info(f"💻 CPU模式启动中，使用模型: {model_name}")
                    self._model = whisper.load_model(model_name, device=self.device)
                
                load_time = time.time() - start_time
                logger.info(f"🎉 Whisper模型({model_name})加载成功，耗时 {load_time:.2f}秒，设备: {self.device}")
                
            except Exception as e:
                logger.error(f"❌ 主模型({model_name})加载失败: {e}")
                # 降级策略：large-v3 -> turbo -> base
                fallback_models = ["turbo", "base"] if model_name == "large-v3" else ["base"]
                
                for fallback_model in fallback_models:
                    try:
                        logger.info(f"🔄 降级到{fallback_model}模型...")
                        self._model = whisper.load_model(fallback_model, device=self.device)
                        load_time = time.time() - start_time
                        logger.info(f"✅ {fallback_model}模型加载成功，耗时 {load_time:.2f}秒")
                        break
                    except Exception as fallback_e:
                        logger.error(f"❌ {fallback_model}模型也加载失败: {fallback_e}")
                        continue
                
                if self._model is None:
                    logger.error("💥 所有Whisper模型都加载失败，请检查安装")
                    raise RuntimeError("无法加载任何Whisper模型")
        
        return self._model
    
    def transcribe_audio(self, audio_path: Path, language: str = "zh") -> Dict[str, Any]:
        """
        优化的音频转录功能
        
        Args:
            audio_path: 音频文件路径
            language: 语言代码，默认中文
            
        Returns:
            转录结果字典
        """
        try:
            start_time = time.time()
            
            # 支持字符串路径和Path对象
            audio_name = audio_path.name if hasattr(audio_path, 'name') else str(audio_path).split('/')[-1]
            logger.info(f"🎵 开始转录音频: {audio_name}")
            logger.info(f"🔧 使用设备: {self.device}")
            
            # 获取实际音频时长
            import librosa
            actual_duration = librosa.get_duration(path=str(audio_path))
            logger.info(f"📊 音频时长: {actual_duration:.2f}秒")
            
            # 获取模型并验证GPU状态
            model_to_use = self.model
            gpu_enabled = self.device == "cuda"
            
            if gpu_enabled:
                logger.info("⚡ GPU加速模式已激活")
                # 设置GPU设备
                torch.cuda.set_device(0)
            
            # 转录配置优化（防止重复循环）
            transcribe_options = {
                "language": language,
                "task": "transcribe",
                "fp16": gpu_enabled,  # 仅在GPU时使用FP16
                "verbose": False,
                # 优化参数：防止重复循环
                "beam_size": 1,  # 降低为1，减少重复可能性
                "best_of": 1,  # 降低为1，减少重复可能性
                "temperature": 0.2,  # 增加一点随机性，防止卡住
                "compression_ratio_threshold": 2.0,  # 降低阈值，减少重复
                "logprob_threshold": -0.8,  # 提高阈值，减少低质量重复
                "no_speech_threshold": 0.8,  # 提高阈值，更严格的静音检测
                "condition_on_previous_text": False,  # 禁用上下文依赖，防止重复循环
            }
            
            logger.info(f"🔧 转录配置: {transcribe_options}")
            
            # 执行转录
            transcribe_start = time.time()
            result = model_to_use.transcribe(str(audio_path), **transcribe_options)
            transcribe_time = time.time() - transcribe_start
            
            # 解析结果
            if not result or not result.get("segments"):
                logger.warning("⚠️ 未检测到语音内容")
                return {
                    "text": "",
                    "language": language,
                    "duration": actual_duration,  # 即使没有语音内容，也返回实际时长
                    "confidence": 0.0,
                    "gpu_accelerated": gpu_enabled,
                    "processing_time": time.time() - start_time,
                    "transcription_time": transcribe_time,
                    "error": "No speech content detected"
                }
            
            # 计算置信度
            segments = result.get("segments", [])
            confidences = []
            
            for segment in segments:
                if "avg_logprob" in segment:
                    confidence = min(1.0, max(0.0, (segment["avg_logprob"] + 1.0)))
                    confidences.append(confidence)
                elif "no_speech_prob" in segment:
                    confidence = 1.0 - segment["no_speech_prob"]
                    confidences.append(confidence)
            
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
            
            total_time = time.time() - start_time
            
            result_data = {
                "text": result["text"].strip(),
                "language": result.get("language", language),
                "duration": actual_duration,  # 使用实际音频时长
                "confidence": round(avg_confidence, 3),
                "gpu_accelerated": gpu_enabled,
                "processing_time": round(total_time, 2),
                "transcription_time": round(transcribe_time, 2),
                "segments_count": len(segments),
                "model_used": "large-v3" if hasattr(model_to_use, 'encoder') else "turbo"
            }
            
            logger.info(f"✅ 转录完成: {total_time:.2f}秒 (转录: {transcribe_time:.2f}秒)")
            logger.info(f"📝 识别文本长度: {len(result_data['text'])} 字符")
            logger.info(f"🎯 平均置信度: {avg_confidence:.3f}")
            logger.info(f"⚡ GPU加速: {'是' if gpu_enabled else '否'}")
            
            return result_data
            
        except Exception as e:
            error_time = time.time() - start_time
            logger.error(f"❌ 转录失败 ({error_time:.2f}秒): {e}", exc_info=True)
            
            return {
                "text": "",
                "language": language,
                "duration": 0,  # 错误情况下无法获取时长
                "confidence": 0.0,
                "gpu_accelerated": self.device == "cuda",
                "processing_time": error_time,
                "error": str(e)
            }

# 全局实例
whisper_service = WhisperService.get_instance() 