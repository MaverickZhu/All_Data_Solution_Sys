"""
视频分析服务
提供专业的视频内容分析、缩略图生成、元数据提取等功能
"""
import logging
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import cv2
import numpy as np

logger = logging.getLogger(__name__)

class VideoAnalysisService:
    """
    视频分析服务
    集成多种视频分析技术，提供全面的视频内容分析
    """
    
    def __init__(self):
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp']
        logger.info("🎬 视频分析服务初始化完成")
    
    def is_supported_format(self, file_path: Path) -> bool:
        """检查文件格式是否支持"""
        return file_path.suffix.lower() in self.supported_formats
    
    def extract_metadata_with_ffprobe(self, video_path: Path) -> Dict[str, Any]:
        """
        使用ffprobe提取详细的视频元数据
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            详细的元数据字典
        """
        try:
            # 使用ffprobe获取详细信息
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(video_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                metadata = json.loads(result.stdout)
                
                # 提取有用信息
                format_info = metadata.get('format', {})
                streams = metadata.get('streams', [])
                
                video_stream = None
                audio_stream = None
                
                for stream in streams:
                    if stream.get('codec_type') == 'video' and not video_stream:
                        video_stream = stream
                    elif stream.get('codec_type') == 'audio' and not audio_stream:
                        audio_stream = stream
                
                enhanced_metadata = {
                    'format_name': format_info.get('format_name', ''),
                    'format_long_name': format_info.get('format_long_name', ''),
                    'duration': float(format_info.get('duration', 0)),
                    'size': int(format_info.get('size', 0)),
                    'bit_rate': int(format_info.get('bit_rate', 0)),
                    'nb_streams': int(format_info.get('nb_streams', 0)),
                    'nb_programs': int(format_info.get('nb_programs', 0)),
                    'tags': format_info.get('tags', {})
                }
                
                if video_stream:
                    # 提取帧率
                    fps = 0
                    if video_stream.get('r_frame_rate'):
                        try:
                            fps_str = video_stream.get('r_frame_rate', '0/1')
                            if '/' in fps_str:
                                num, den = fps_str.split('/')
                                fps = float(num) / float(den) if float(den) != 0 else 0
                        except:
                            fps = 0
                    
                    # 提取总帧数
                    nb_frames = 0
                    if 'nb_frames' in video_stream:
                        try:
                            nb_frames = int(video_stream['nb_frames'])
                        except (ValueError, TypeError):
                            # 如果无法从nb_frames获取，尝试通过时长和帧率计算
                            if fps > 0 and enhanced_metadata.get('duration'):
                                nb_frames = int(fps * float(enhanced_metadata['duration']))
                    elif fps > 0 and enhanced_metadata.get('duration'):
                        # 如果没有nb_frames字段，通过时长和帧率计算
                        nb_frames = int(fps * float(enhanced_metadata['duration']))
                    
                    enhanced_metadata.update({
                        'width': int(video_stream.get('width', 0)),
                        'height': int(video_stream.get('height', 0)),
                        'fps': fps,
                        'nb_frames': nb_frames,  # 添加总帧数
                        'video_codec': video_stream.get('codec_name', ''),
                        'video_codec_long': video_stream.get('codec_long_name', ''),
                        'video_profile': video_stream.get('profile', ''),
                        'video_level': video_stream.get('level', ''),
                        'pixel_format': video_stream.get('pix_fmt', ''),
                        'color_space': video_stream.get('color_space', ''),
                        'color_range': video_stream.get('color_range', ''),
                        'field_order': video_stream.get('field_order', ''),
                        'video_bit_rate': int(video_stream.get('bit_rate', 0)) if video_stream.get('bit_rate') else 0,
                        'max_bit_rate': int(video_stream.get('max_bit_rate', 0)) if video_stream.get('max_bit_rate') else 0,
                        'video_tags': video_stream.get('tags', {})
                    })
                
                # 添加是否有音频的标记
                enhanced_metadata['has_audio'] = audio_stream is not None
                
                if audio_stream:
                    enhanced_metadata.update({
                        'audio_codec': audio_stream.get('codec_name', ''),
                        'audio_codec_long': audio_stream.get('codec_long_name', ''),
                        'audio_profile': audio_stream.get('profile', ''),
                        'sample_rate': int(audio_stream.get('sample_rate', 0)),
                        'channels': int(audio_stream.get('channels', 0)),
                        'channel_layout': audio_stream.get('channel_layout', ''),
                        'audio_bit_rate': int(audio_stream.get('bit_rate', 0)) if audio_stream.get('bit_rate') else 0,
                        'audio_tags': audio_stream.get('tags', {})
                    })
                
                logger.info(f"📊 ffprobe元数据提取成功: {video_path.name}")
                return enhanced_metadata
                
            else:
                logger.warning(f"ffprobe failed with return code {result.returncode}: {result.stderr}")
                return {}
                
        except subprocess.TimeoutExpired:
            logger.error(f"ffprobe timeout for {video_path}")
            return {}
        except Exception as e:
            logger.error(f"ffprobe error for {video_path}: {e}")
            return {}
    
    def generate_multiple_thumbnails(self, video_path: Path, count: int = 3) -> List[str]:
        """
        生成多个缩略图（开始、中间、结束）
        
        Args:
            video_path: 视频文件路径
            count: 缩略图数量
            
        Returns:
            缩略图路径列表
        """
        thumbnails = []
        
        try:
            cap = cv2.VideoCapture(str(video_path))
            
            if not cap.isOpened():
                logger.error(f"无法打开视频文件: {video_path}")
                return thumbnails
            
            # 获取视频基本信息
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            if total_frames <= 0 or fps <= 0:
                logger.error(f"无法获取视频帧信息: {video_path}")
                cap.release()
                return thumbnails
            
            # 创建缩略图目录
            thumbnails_dir = video_path.parent / "thumbnails"
            thumbnails_dir.mkdir(exist_ok=True)
            
            # 计算缩略图位置
            positions = []
            if count == 1:
                positions = [total_frames // 2]  # 中间位置
            else:
                step = total_frames // (count + 1)
                positions = [step * (i + 1) for i in range(count)]
            
            for i, frame_pos in enumerate(positions):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
                ret, frame = cap.read()
                
                if ret:
                    # 调整缩略图大小
                    h, w = frame.shape[:2]
                    if w > 400:
                        scale = 400 / w
                        new_w, new_h = int(w * scale), int(h * scale)
                        frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
                    
                    # 保存缩略图
                    thumbnail_filename = f"thumb_{video_path.stem}_{i+1}.jpg"
                    thumbnail_path = thumbnails_dir / thumbnail_filename
                    
                    cv2.imwrite(str(thumbnail_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    thumbnails.append(str(thumbnail_path))
                    
                    logger.info(f"生成缩略图 {i+1}/{count}: {thumbnail_path}")
            
            cap.release()
            
        except Exception as e:
            logger.error(f"生成缩略图失败: {e}")
        
        return thumbnails
    
    def analyze_video_content(self, video_path: Path) -> Dict[str, Any]:
        """
        分析视频内容特征
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            内容分析结果
        """
        try:
            cap = cv2.VideoCapture(str(video_path))
            
            if not cap.isOpened():
                return {"error": "无法打开视频文件"}
            
            # 基本信息
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # 采样分析（每秒1帧）
            sample_interval = max(1, int(fps))
            sample_frames = []
            
            frame_count = 0
            brightness_values = []
            contrast_values = []
            
            while frame_count < total_frames:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                # 转换为灰度图进行分析
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # 计算亮度和对比度
                brightness = np.mean(gray)
                contrast = np.std(gray)
                
                brightness_values.append(brightness)
                contrast_values.append(contrast)
                
                frame_count += sample_interval
                
                # 限制分析帧数（最多100帧）
                if len(brightness_values) >= 100:
                    break
            
            cap.release()
            
            # 计算统计信息
            avg_brightness = np.mean(brightness_values) if brightness_values else 0
            avg_contrast = np.mean(contrast_values) if contrast_values else 0
            brightness_std = np.std(brightness_values) if brightness_values else 0
            contrast_std = np.std(contrast_values) if contrast_values else 0
            
            # 内容特征分析
            content_analysis = {
                "brightness_analysis": {
                    "average": round(avg_brightness, 2),
                    "std_deviation": round(brightness_std, 2),
                    "category": self._categorize_brightness(avg_brightness)
                },
                "contrast_analysis": {
                    "average": round(avg_contrast, 2),
                    "std_deviation": round(contrast_std, 2),
                    "category": self._categorize_contrast(avg_contrast)
                },
                "visual_stability": {
                    "brightness_stability": "稳定" if brightness_std < 20 else "中等" if brightness_std < 40 else "不稳定",
                    "contrast_stability": "稳定" if contrast_std < 15 else "中等" if contrast_std < 30 else "不稳定"
                },
                "analyzed_frames": len(brightness_values),
                "sample_rate": f"每秒{1}帧" if sample_interval == fps else f"每{sample_interval}帧采样1次"
            }
            
            logger.info(f"🎯 视频内容分析完成: {video_path.name}")
            return content_analysis
            
        except Exception as e:
            logger.error(f"视频内容分析失败: {e}")
            return {"error": str(e)}
    
    def _categorize_brightness(self, brightness: float) -> str:
        """分类亮度级别"""
        if brightness < 50:
            return "较暗"
        elif brightness < 100:
            return "中等"
        elif brightness < 150:
            return "较亮"
        else:
            return "很亮"
    
    def _categorize_contrast(self, contrast: float) -> str:
        """分类对比度级别"""
        if contrast < 20:
            return "低对比度"
        elif contrast < 40:
            return "中等对比度"
        elif contrast < 60:
            return "高对比度"
        else:
            return "极高对比度"
    
    def comprehensive_analysis(self, video_path: Path) -> Dict[str, Any]:
        """
        综合视频分析
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            完整的分析结果
        """
        try:
            logger.info(f"🎬 开始综合视频分析: {video_path.name}")
            
            # 检查文件格式
            if not self.is_supported_format(video_path):
                return {"error": f"不支持的视频格式: {video_path.suffix}"}
            
            # 基础分析结果
            analysis_result = {
                "analysis_type": "video_enhanced",
                "file_path": str(video_path),
                "file_size": video_path.stat().st_size,
                "format": video_path.suffix[1:].lower()
            }
            
            # 1. 提取详细元数据
            ffprobe_metadata = self.extract_metadata_with_ffprobe(video_path)
            if ffprobe_metadata:
                analysis_result["enhanced_metadata"] = ffprobe_metadata
            
            # 2. 生成多个缩略图
            thumbnails = self.generate_multiple_thumbnails(video_path, count=3)
            if thumbnails:
                analysis_result["thumbnails"] = thumbnails
                analysis_result["primary_thumbnail"] = thumbnails[0]
            
            # 3. 内容分析
            content_analysis = self.analyze_video_content(video_path)
            if "error" not in content_analysis:
                analysis_result["content_analysis"] = content_analysis
            
            # 4. 生成分析摘要
            analysis_result["analysis_summary"] = self._generate_analysis_summary(analysis_result)
            
            logger.info(f"✅ 综合视频分析完成: {video_path.name}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"综合视频分析失败: {e}")
            return {"error": str(e)}
    
    def _generate_analysis_summary(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成分析摘要"""
        summary = {}
        
        # 基本信息摘要
        enhanced_metadata = analysis_result.get("enhanced_metadata", {})
        if enhanced_metadata:
            duration = enhanced_metadata.get("duration", 0)
            size_mb = analysis_result.get("file_size", 0) / (1024 * 1024)
            
            summary.update({
                "duration_formatted": f"{int(duration // 60)}分{int(duration % 60)}秒",
                "file_size_mb": round(size_mb, 2),
                "video_codec": enhanced_metadata.get("video_codec", "未知"),
                "audio_codec": enhanced_metadata.get("audio_codec", "未知"),
                "has_audio": bool(enhanced_metadata.get("audio_codec")),
                "bit_rate_kbps": round(enhanced_metadata.get("bit_rate", 0) / 1000, 0) if enhanced_metadata.get("bit_rate") else 0
            })
        
        # 内容分析摘要
        content_analysis = analysis_result.get("content_analysis", {})
        if content_analysis:
            brightness = content_analysis.get("brightness_analysis", {})
            contrast = content_analysis.get("contrast_analysis", {})
            
            summary.update({
                "visual_quality": f"{brightness.get('category', '未知')}，{contrast.get('category', '未知')}",
                "content_stability": content_analysis.get("visual_stability", {}).get("brightness_stability", "未知")
            })
        
        # 缩略图信息
        thumbnails = analysis_result.get("thumbnails", [])
        summary["thumbnails_count"] = len(thumbnails)
        
        return summary

# 创建全局实例
video_analysis_service = VideoAnalysisService() 