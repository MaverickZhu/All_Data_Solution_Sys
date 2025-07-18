"""
智能视频帧提取器
实现场景变化检测和关键帧采样，避免重复分析相似帧
"""
import cv2
import numpy as np
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import hashlib

logger = logging.getLogger("service")


@dataclass
class FrameInfo:
    """帧信息数据类"""
    frame_number: int
    timestamp: float
    frame_path: Optional[str] = None
    scene_change_score: float = 0.0
    is_key_frame: bool = False
    key_frame_reason: str = ""
    brightness: float = 0.0
    contrast: float = 0.0
    sharpness: float = 0.0
    frame_hash: str = ""


class VideoFrameExtractor:
    """
    智能视频帧提取器
    基于场景变化检测和质量评估进行智能帧采样
    """
    
    def __init__(self, 
                 scene_threshold: float = 0.3,
                 min_interval: float = 1.0,
                 max_frames: int = 100,
                 quality_threshold: float = 0.5):
        """
        初始化帧提取器
        
        Args:
            scene_threshold: 场景变化阈值 (0-1)
            min_interval: 最小帧间隔 (秒)
            max_frames: 最大提取帧数
            quality_threshold: 质量阈值 (0-1)
        """
        self.scene_threshold = scene_threshold
        self.min_interval = min_interval
        self.max_frames = max_frames
        self.quality_threshold = quality_threshold
        
        logger.info(f"视频帧提取器初始化: scene_threshold={scene_threshold}, min_interval={min_interval}s")
    
    def calculate_scene_change_score(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """
        公共方法：计算两个图像间的场景变化得分
        
        Args:
            img1: 第一个图像 (BGR或灰度)
            img2: 第二个图像 (BGR或灰度)
            
        Returns:
            场景变化得分 (0-1，值越大变化越大)
        """
        try:
            # 转换为灰度图（如果需要）
            if len(img1.shape) == 3:
                img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            if len(img2.shape) == 3:
                img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            
            return self._calculate_scene_change(img1, img2)
        except Exception as e:
            logger.warning(f"场景变化计算失败: {e}")
            return 0.0
    
    def assess_frame_quality(self, img: np.ndarray) -> Dict[str, float]:
        """
        公共方法：评估图像质量
        
        Args:
            img: 输入图像 (BGR或灰度)
            
        Returns:
            质量评估结果字典，包含brightness, contrast, sharpness, overall_score
        """
        try:
            # 转换为灰度图（如果需要）
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img
            
            # 计算质量指标
            brightness = float(np.mean(gray))
            contrast = float(np.std(gray))
            sharpness = self._calculate_sharpness(gray)
            
            # 计算综合质量得分
            overall_score = (brightness / 255.0) * 0.3 + (contrast / 100.0) * 0.3 + sharpness * 0.4
            overall_score = min(1.0, overall_score)
            
            return {
                "brightness": brightness,
                "contrast": contrast,
                "sharpness": sharpness,
                "overall_score": overall_score
            }
        except Exception as e:
            logger.warning(f"质量评估失败: {e}")
            return {
                "brightness": 0.0,
                "contrast": 0.0,
                "sharpness": 0.0,
                "overall_score": 0.0
            }
    
    def extract_key_frames(self, video_path: Path, output_dir: Path) -> List[FrameInfo]:
        """
        提取视频关键帧
        
        Args:
            video_path: 视频文件路径
            output_dir: 帧输出目录
            
        Returns:
            关键帧信息列表
        """
        try:
            logger.info(f"开始提取关键帧: {video_path.name}")
            
            # 打开视频
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                raise ValueError(f"无法打开视频文件: {video_path}")
            
            # 获取视频基本信息
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            
            logger.info(f"视频信息: {total_frames}帧, {fps:.2f}fps, {duration:.2f}s")
            
            # 创建输出目录
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 提取关键帧
            key_frames = self._extract_frames_with_scene_detection(
                cap, fps, total_frames, video_path.stem, output_dir
            )
            
            cap.release()
            
            logger.info(f"关键帧提取完成: 共{len(key_frames)}帧")
            return key_frames
            
        except Exception as e:
            logger.error(f"关键帧提取失败: {e}")
            if 'cap' in locals():
                cap.release()
            raise
    
    def _extract_frames_with_scene_detection(self, 
                                           cap: cv2.VideoCapture,
                                           fps: float,
                                           total_frames: int,
                                           video_name: str,
                                           output_dir: Path) -> List[FrameInfo]:
        """
        基于场景变化检测提取帧
        """
        key_frames = []
        prev_frame_gray = None
        last_key_frame_time = -self.min_interval
        frame_count = 0
        
        # 计算采样间隔（避免处理每一帧）
        sample_interval = max(1, int(fps / 10))  # 每秒最多采样10帧
        
        while frame_count < total_frames and len(key_frames) < self.max_frames:
            # 设置帧位置
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
            ret, frame = cap.read()
            
            if not ret:
                break
            
            timestamp = frame_count / fps
            
            # 转换为灰度图
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # 计算帧质量指标
            brightness = np.mean(gray)
            contrast = np.std(gray)
            sharpness = self._calculate_sharpness(gray)
            
            # 计算帧哈希
            frame_hash = self._calculate_frame_hash(gray)
            
            # 场景变化检测
            scene_change_score = 0.0
            is_scene_change = False
            
            if prev_frame_gray is not None:
                scene_change_score = self._calculate_scene_change(prev_frame_gray, gray)
                is_scene_change = scene_change_score > self.scene_threshold
            
            # 判断是否为关键帧
            is_key_frame, reason = self._is_key_frame(
                timestamp, last_key_frame_time, is_scene_change, 
                brightness, contrast, sharpness, frame_count, total_frames
            )
            
            if is_key_frame:
                # 保存帧
                frame_filename = f"frame_{video_name}_{frame_count:06d}.jpg"
                frame_path = output_dir / frame_filename
                cv2.imwrite(str(frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                
                # 创建帧信息
                frame_info = FrameInfo(
                    frame_number=frame_count,
                    timestamp=timestamp,
                    frame_path=str(frame_path),
                    scene_change_score=scene_change_score,
                    is_key_frame=True,
                    key_frame_reason=reason,
                    brightness=brightness,
                    contrast=contrast,
                    sharpness=sharpness,
                    frame_hash=frame_hash
                )
                
                key_frames.append(frame_info)
                last_key_frame_time = timestamp
                
                logger.debug(f"提取关键帧: {frame_count}/{total_frames} ({reason})")
            
            prev_frame_gray = gray.copy()
            frame_count += sample_interval
        
        return key_frames
    
    def _calculate_scene_change(self, prev_frame: np.ndarray, curr_frame: np.ndarray) -> float:
        """
        计算场景变化程度
        使用直方图比较和结构相似性
        """
        try:
            # 方法1: 直方图比较
            hist1 = cv2.calcHist([prev_frame], [0], None, [256], [0, 256])
            hist2 = cv2.calcHist([curr_frame], [0], None, [256], [0, 256])
            hist_correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            
            # 方法2: 均值差异
            mean_diff = abs(np.mean(prev_frame) - np.mean(curr_frame)) / 255.0
            
            # 方法3: 结构差异 (简化版SSIM)
            # 计算局部方差
            prev_var = np.var(prev_frame)
            curr_var = np.var(curr_frame)
            var_diff = abs(prev_var - curr_var) / max(prev_var, curr_var, 1.0)
            
            # 综合评分 (值越大表示变化越大)
            scene_change_score = (1 - hist_correlation) * 0.5 + mean_diff * 0.3 + var_diff * 0.2
            
            return min(1.0, scene_change_score)
            
        except Exception as e:
            logger.warning(f"场景变化计算失败: {e}")
            return 0.0
    
    def _calculate_sharpness(self, gray: np.ndarray) -> float:
        """
        计算图像清晰度 (使用Laplacian方差)
        """
        try:
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            sharpness = laplacian.var()
            # 归一化到0-1范围
            return min(1.0, sharpness / 1000.0)
        except Exception:
            return 0.0
    
    def _calculate_frame_hash(self, gray: np.ndarray) -> str:
        """
        计算帧的感知哈希，用于去重
        """
        try:
            # 缩放到8x8
            resized = cv2.resize(gray, (8, 8), interpolation=cv2.INTER_AREA)
            # 计算平均值
            avg = np.mean(resized)
            # 生成二进制哈希
            binary = (resized > avg).astype(int)
            # 转换为字符串
            hash_str = ''.join(binary.flatten().astype(str))
            # MD5哈希
            return hashlib.md5(hash_str.encode()).hexdigest()[:16]
        except Exception:
            return ""
    
    def _is_key_frame(self, 
                     timestamp: float,
                     last_key_frame_time: float,
                     is_scene_change: bool,
                     brightness: float,
                     contrast: float,
                     sharpness: float,
                     frame_number: int,
                     total_frames: int) -> Tuple[bool, str]:
        """
        判断是否为关键帧
        
        Returns:
            (是否为关键帧, 原因)
        """
        # 时间间隔检查
        time_since_last = timestamp - last_key_frame_time
        if time_since_last < self.min_interval:
            return False, ""
        
        # 强制关键帧：开始、结束
        if frame_number == 0:
            return True, "视频开始帧"
        if frame_number >= total_frames - 1:
            return True, "视频结束帧"
        
        # 场景变化
        if is_scene_change:
            return True, "场景变化"
        
        # 质量评估
        quality_score = (brightness / 255.0) * 0.3 + (contrast / 100.0) * 0.3 + sharpness * 0.4
        if quality_score > self.quality_threshold and time_since_last >= self.min_interval * 2:
            return True, "高质量帧"
        
        # 定期采样（确保不会错过重要内容）
        if time_since_last >= self.min_interval * 5:  # 5倍最小间隔
            return True, "定期采样"
        
        return False, ""
    
    def get_uniform_samples(self, video_path: Path, count: int, output_dir: Path) -> List[FrameInfo]:
        """
        均匀采样视频帧（用于对比和备用方案）
        
        Args:
            video_path: 视频文件路径
            count: 采样帧数
            output_dir: 输出目录
            
        Returns:
            帧信息列表
        """
        try:
            logger.info(f"均匀采样视频帧: {count}帧")
            
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                raise ValueError(f"无法打开视频文件: {video_path}")
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # 创建输出目录
            output_dir.mkdir(parents=True, exist_ok=True)
            
            frames = []
            if count == 1:
                # 单帧：选择中间帧
                positions = [total_frames // 2]
            else:
                # 多帧：均匀分布
                step = total_frames // (count + 1)
                positions = [step * (i + 1) for i in range(count)]
            
            for i, frame_pos in enumerate(positions):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
                ret, frame = cap.read()
                
                if ret:
                    timestamp = frame_pos / fps
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    
                    # 保存帧
                    frame_filename = f"uniform_{video_path.stem}_{i+1:03d}.jpg"
                    frame_path = output_dir / frame_filename
                    cv2.imwrite(str(frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                    
                    # 创建帧信息
                    frame_info = FrameInfo(
                        frame_number=frame_pos,
                        timestamp=timestamp,
                        frame_path=str(frame_path),
                        is_key_frame=True,
                        key_frame_reason="均匀采样",
                        brightness=np.mean(gray),
                        contrast=np.std(gray),
                        sharpness=self._calculate_sharpness(gray),
                        frame_hash=self._calculate_frame_hash(gray)
                    )
                    
                    frames.append(frame_info)
            
            cap.release()
            logger.info(f"均匀采样完成: {len(frames)}帧")
            return frames
            
        except Exception as e:
            logger.error(f"均匀采样失败: {e}")
            if 'cap' in locals():
                cap.release()
            raise


# 创建全局实例
video_frame_extractor = VideoFrameExtractor() 