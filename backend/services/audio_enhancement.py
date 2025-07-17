"""
音频增强与去噪预处理服务
集成多种去噪算法，为语音识别提供高质量的音频输入
"""
import logging
import numpy as np
import librosa
import scipy.signal
import scipy.stats
import torch
import tempfile
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from scipy.io import wavfile
from scipy.signal import butter, filtfilt, medfilt

logger = logging.getLogger(__name__)

class AudioEnhancementService:
    """
    音频增强与去噪服务
    提供多种音频预处理算法，提升语音识别质量
    """
    
    def __init__(self):
        self.target_sr = 16000  # Whisper推荐的采样率
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"🎵 音频增强服务初始化，设备: {self.device}")
    
    def load_audio(self, audio_path: Path) -> Tuple[np.ndarray, int]:
        """
        加载音频文件并标准化
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            (audio_data, sample_rate): 音频数据和采样率
        """
        try:
            # 使用librosa加载音频，自动转换为mono和目标采样率
            audio_data, sr = librosa.load(
                str(audio_path), 
                sr=self.target_sr,
                mono=True,
                res_type='kaiser_best'  # 高质量重采样
            )
            
            # 标准化音频幅度到[-1, 1]
            if np.max(np.abs(audio_data)) > 0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            logger.info(f"📂 音频加载成功: {audio_path.name}")
            logger.info(f"📊 时长: {len(audio_data)/sr:.2f}秒, 采样率: {sr}Hz")
            
            return audio_data, sr
            
        except Exception as e:
            logger.error(f"❌ 音频加载失败 {audio_path}: {e}")
            raise
    
    def spectral_gating_denoise(self, audio_data: np.ndarray, sr: int, 
                               stationary_ratio: float = 0.1,
                               prop_decrease: float = 0.8) -> np.ndarray:
        """
        频谱门控去噪算法
        基于噪声统计特性进行自适应去噪
        
        Args:
            audio_data: 输入音频数据
            sr: 采样率
            stationary_ratio: 用于估计噪声的音频比例
            prop_decrease: 噪声减少比例
            
        Returns:
            去噪后的音频数据
        """
        try:
            # 短时傅里叶变换
            n_fft = 2048
            hop_length = 512
            stft = librosa.stft(audio_data, n_fft=n_fft, hop_length=hop_length)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # 估计噪声谱（使用前10%的音频作为噪声样本）
            noise_sample_count = int(magnitude.shape[1] * stationary_ratio)
            noise_stft = magnitude[:, :noise_sample_count]
            noise_profile = np.mean(noise_stft, axis=1, keepdims=True)
            
            # 计算信噪比掩码
            snr_mask = magnitude / (noise_profile + 1e-10)
            
            # 应用频谱门控
            # 保护语音信号，抑制噪声
            enhanced_mask = np.where(
                snr_mask > 1.5,  # 信号强度阈值
                1.0,  # 保持信号
                prop_decrease  # 减少噪声
            )
            
            # 平滑掩码以避免音频artifact
            enhanced_mask = scipy.signal.medfilt(enhanced_mask, kernel_size=3)
            
            # 应用掩码
            enhanced_magnitude = magnitude * enhanced_mask
            enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
            
            # 逆变换回时域
            enhanced_audio = librosa.istft(
                enhanced_stft, 
                hop_length=hop_length,
                length=len(audio_data)
            )
            
            logger.info("✅ 频谱门控去噪完成")
            return enhanced_audio
            
        except Exception as e:
            logger.error(f"❌ 频谱门控去噪失败: {e}")
            return audio_data  # 返回原始音频作为fallback
    
    def adaptive_wiener_filter(self, audio_data: np.ndarray, sr: int) -> np.ndarray:
        """
        自适应维纳滤波去噪
        
        Args:
            audio_data: 输入音频数据
            sr: 采样率
            
        Returns:
            滤波后的音频数据
        """
        try:
            # 计算功率谱密度
            f, psd = scipy.signal.welch(audio_data, sr, nperseg=1024)
            
            # 估计噪声功率（使用最低20%的频率作为噪声估计）
            noise_floor = np.percentile(psd, 20)
            
            # 设计维纳滤波器
            wiener_gain = psd / (psd + noise_floor)
            
            # 应用到频域
            fft_audio = np.fft.fft(audio_data)
            freqs = np.fft.fftfreq(len(audio_data), 1/sr)
            
            # 插值增益到所有频率
            gain_interp = np.interp(np.abs(freqs), f, wiener_gain)
            
            # 应用滤波
            filtered_fft = fft_audio * gain_interp
            filtered_audio = np.real(np.fft.ifft(filtered_fft))
            
            logger.info("✅ 维纳滤波去噪完成")
            return filtered_audio
            
        except Exception as e:
            logger.error(f"❌ 维纳滤波失败: {e}")
            return audio_data
    
    def bandpass_filter(self, audio_data: np.ndarray, sr: int,
                       low_cutoff: int = 80, high_cutoff: int = 8000) -> np.ndarray:
        """
        带通滤波器，去除语音频率范围外的噪声
        
        Args:
            audio_data: 输入音频数据
            sr: 采样率
            low_cutoff: 低频截止频率 (Hz)
            high_cutoff: 高频截止频率 (Hz)
            
        Returns:
            滤波后的音频数据
        """
        try:
            # 设计Butterworth带通滤波器
            nyquist = sr / 2
            low = low_cutoff / nyquist
            high = high_cutoff / nyquist
            
            b, a = butter(4, [low, high], btype='band')
            
            # 应用零相位滤波
            filtered_audio = filtfilt(b, a, audio_data)
            
            logger.info(f"✅ 带通滤波完成 ({low_cutoff}-{high_cutoff}Hz)")
            return filtered_audio
            
        except Exception as e:
            logger.error(f"❌ 带通滤波失败: {e}")
            return audio_data
    
    def remove_silence(self, audio_data: np.ndarray, sr: int,
                      top_db: int = 20) -> np.ndarray:
        """
        移除静音段，减少无效音频
        
        Args:
            audio_data: 输入音频数据
            sr: 采样率
            top_db: 静音检测阈值
            
        Returns:
            移除静音后的音频数据
        """
        try:
            # 检测非静音段
            intervals = librosa.effects.split(
                audio_data, 
                top_db=top_db,
                frame_length=2048,
                hop_length=512
            )
            
            if len(intervals) == 0:
                logger.warning("⚠️ 未检测到有效音频段")
                return audio_data
            
            # 合并非静音段
            trimmed_audio = np.concatenate([
                audio_data[start:end] for start, end in intervals
            ])
            
            silence_removed = len(audio_data) - len(trimmed_audio)
            logger.info(f"✅ 静音移除完成，移除 {silence_removed/sr:.2f}秒")
            
            return trimmed_audio
            
        except Exception as e:
            logger.error(f"❌ 静音移除失败: {e}")
            return audio_data
    
    def normalize_volume(self, audio_data: np.ndarray, target_rms: float = 0.1) -> np.ndarray:
        """
        音量标准化
        
        Args:
            audio_data: 输入音频数据
            target_rms: 目标RMS值
            
        Returns:
            标准化后的音频数据
        """
        try:
            # 计算当前RMS
            current_rms = np.sqrt(np.mean(audio_data**2))
            
            if current_rms > 0:
                # 计算缩放因子
                scale_factor = target_rms / current_rms
                normalized_audio = audio_data * scale_factor
                
                # 防止剪切
                max_val = np.max(np.abs(normalized_audio))
                if max_val > 0.95:
                    normalized_audio = normalized_audio * (0.95 / max_val)
                
                logger.info(f"✅ 音量标准化完成，缩放因子: {scale_factor:.3f}")
                return normalized_audio
            else:
                logger.warning("⚠️ 音频RMS为0，跳过标准化")
                return audio_data
                
        except Exception as e:
            logger.error(f"❌ 音量标准化失败: {e}")
            return audio_data
    
    def enhance_audio_pipeline(self, audio_path: Path, 
                              enable_denoise: bool = True,
                              enable_bandpass: bool = True,
                              enable_silence_removal: bool = True,
                              enable_normalization: bool = True) -> Path:
        """
        完整的音频增强管道
        
        Args:
            audio_path: 输入音频文件路径
            enable_denoise: 是否启用去噪
            enable_bandpass: 是否启用带通滤波
            enable_silence_removal: 是否移除静音
            enable_normalization: 是否标准化音量
            
        Returns:
            增强后的音频文件路径
        """
        try:
            logger.info(f"🎯 开始音频增强管道: {audio_path.name}")
            start_time = time.time()
            
            # 加载音频
            audio_data, sr = self.load_audio(audio_path)
            original_duration = len(audio_data) / sr
            
            # 保存原始音频信息
            enhancement_log = {
                "original_duration": original_duration,
                "sample_rate": sr,
                "enhancements_applied": []
            }
            
            # 1. 带通滤波（先过滤明显的噪声频率）
            if enable_bandpass:
                audio_data = self.bandpass_filter(audio_data, sr)
                enhancement_log["enhancements_applied"].append("bandpass_filter")
            
            # 2. 频谱去噪（主要去噪步骤）
            if enable_denoise:
                # 使用频谱门控去噪
                audio_data = self.spectral_gating_denoise(audio_data, sr)
                enhancement_log["enhancements_applied"].append("spectral_denoising")
                
                # 可选：维纳滤波进一步优化
                # audio_data = self.adaptive_wiener_filter(audio_data, sr)
                # enhancement_log["enhancements_applied"].append("wiener_filter")
            
            # 3. 移除静音段
            if enable_silence_removal:
                audio_data = self.remove_silence(audio_data, sr)
                enhancement_log["enhancements_applied"].append("silence_removal")
            
            # 4. 音量标准化
            if enable_normalization:
                audio_data = self.normalize_volume(audio_data)
                enhancement_log["enhancements_applied"].append("volume_normalization")
            
            # 保存增强后的音频到临时文件
            enhanced_audio_path = self._save_enhanced_audio(audio_data, sr, audio_path)
            
            # 计算处理时间和效果
            processing_time = time.time() - start_time
            final_duration = len(audio_data) / sr
            
            enhancement_log.update({
                "final_duration": final_duration,
                "processing_time": processing_time,
                "duration_change": final_duration - original_duration,
                "enhanced_file": str(enhanced_audio_path)
            })
            
            logger.info(f"🎉 音频增强完成!")
            logger.info(f"⏱️ 处理时间: {processing_time:.2f}秒")
            logger.info(f"📊 时长变化: {final_duration - original_duration:.2f}秒")
            logger.info(f"🔧 应用的增强: {', '.join(enhancement_log['enhancements_applied'])}")
            
            return enhanced_audio_path
            
        except Exception as e:
            logger.error(f"❌ 音频增强管道失败: {e}", exc_info=True)
            # 失败时返回原始文件
            return audio_path
    
    def _save_enhanced_audio(self, audio_data: np.ndarray, sr: int, 
                           original_path: Path) -> Path:
        """
        保存增强后的音频到临时文件
        
        Args:
            audio_data: 增强后的音频数据
            sr: 采样率
            original_path: 原始文件路径
            
        Returns:
            临时文件路径
        """
        try:
            # 创建临时文件
            temp_dir = Path(tempfile.gettempdir()) / "audio_enhancement"
            temp_dir.mkdir(exist_ok=True)
            
            # 生成临时文件名
            temp_filename = f"enhanced_{original_path.stem}_{int(time.time())}.wav"
            temp_path = temp_dir / temp_filename
            
            # 保存为WAV格式（Whisper友好）
            import soundfile as sf
            sf.write(str(temp_path), audio_data, sr, subtype='PCM_16')
            
            logger.info(f"💾 增强音频已保存: {temp_path}")
            return temp_path
            
        except ImportError:
            # 如果没有soundfile，使用scipy.io.wavfile
            try:
                # 转换为16位整数
                audio_int16 = (audio_data * 32767).astype(np.int16)
                
                temp_dir = Path(tempfile.gettempdir()) / "audio_enhancement"
                temp_dir.mkdir(exist_ok=True)
                temp_filename = f"enhanced_{original_path.stem}_{int(time.time())}.wav"
                temp_path = temp_dir / temp_filename
                
                wavfile.write(str(temp_path), sr, audio_int16)
                logger.info(f"💾 增强音频已保存(fallback): {temp_path}")
                return temp_path
                
            except Exception as e:
                logger.error(f"❌ 保存增强音频失败: {e}")
                return original_path
        
        except Exception as e:
            logger.error(f"❌ 保存增强音频失败: {e}")
            return original_path
    
    def analyze_noise_level(self, audio_path: Path) -> Dict[str, Any]:
        """
        分析音频的噪声水平
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            噪声分析结果
        """
        try:
            audio_data, sr = self.load_audio(audio_path)
            
            # 计算信噪比估计
            # 使用前10%的音频作为噪声样本
            noise_sample_count = int(len(audio_data) * 0.1)
            noise_sample = audio_data[:noise_sample_count]
            signal_sample = audio_data[noise_sample_count:]
            
            noise_power = np.mean(noise_sample**2)
            signal_power = np.mean(signal_sample**2)
            
            if noise_power > 0:
                snr_db = 10 * np.log10(signal_power / noise_power)
            else:
                snr_db = float('inf')
            
            # 分析频谱噪声
            stft = librosa.stft(audio_data)
            magnitude = np.abs(stft)
            spectral_flatness = np.mean(scipy.stats.gmean(magnitude, axis=0) / np.mean(magnitude, axis=0))
            
            # 计算零交叉率（噪声指标）
            zcr = np.mean(librosa.feature.zero_crossing_rate(audio_data))
            
            noise_analysis = {
                "estimated_snr_db": round(snr_db, 2),
                "spectral_flatness": round(spectral_flatness, 4),
                "zero_crossing_rate": round(zcr, 4),
                "noise_level": "low" if snr_db > 20 else "medium" if snr_db > 10 else "high",
                "enhancement_recommended": snr_db < 15 or spectral_flatness > 0.5
            }
            
            logger.info(f"📊 噪声分析完成: SNR={snr_db:.1f}dB, 噪声水平={noise_analysis['noise_level']}")
            
            return noise_analysis
            
        except Exception as e:
            logger.error(f"❌ 噪声分析失败: {e}")
            return {
                "estimated_snr_db": 0,
                "spectral_flatness": 0,
                "zero_crossing_rate": 0,
                "noise_level": "unknown",
                "enhancement_recommended": True,
                "error": str(e)
            }

# 全局实例
audio_enhancement_service = AudioEnhancementService() 