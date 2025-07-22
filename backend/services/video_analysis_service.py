"""
视频分析服务
基于现有稳定架构设计，遵循DataSourceService的设计模式
"""
import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
import uuid

from backend.models.video_analysis import (
    VideoAnalysis, VideoAnalysisCreate, VideoAnalysisUpdate, 
    VideoAnalysisType, VideoAnalysisStatus,
    VideoFrame, VideoSegment
)
from backend.models.data_source import DataSource, AnalysisCategory
from backend.models.user import User
from backend.core.exceptions import NotFoundException, AuthorizationException
from backend.core.config import settings
from backend.services.video_frame_extractor import VideoFrameExtractor
from backend.services.video_vision_service import VideoVisionService
from backend.services.video_audio_service import VideoAudioService
from backend.services.video_multimodal_service import VideoMultimodalService

logger = logging.getLogger("service")


class VideoAnalysisService:
    """视频分析服务类 - 遵循现有服务的设计模式"""
    
    def __init__(self):
        self.frame_extractor = VideoFrameExtractor()
        self.vision_service = VideoVisionService()
        self.audio_service = VideoAudioService()
        self.multimodal_service = VideoMultimodalService()
        logger.info("视频分析服务初始化完成")

    @classmethod
    async def create_video_analysis(
        cls,
        db: AsyncSession,
        data_source_id: int,
        analysis_type: VideoAnalysisType,
        current_user: User
    ) -> VideoAnalysis:
        """
        创建视频分析任务
        严格遵循现有服务的权限检查和创建模式
        """
        logger.info(f"Creating video analysis for data_source_id: {data_source_id}, type: {analysis_type}")
        
        # 验证数据源存在且用户有权限访问
        data_source = await cls._validate_data_source_access(
            db, data_source_id, current_user
        )
        
        # 验证数据源是视频类型
        if data_source.analysis_category != AnalysisCategory.VIDEO:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data source is not a video file. Category: {data_source.analysis_category}"
            )
        
        # 检查是否已有进行中的分析
        existing_analysis = await cls._get_active_analysis(db, data_source_id)
        if existing_analysis:
            logger.warning(
                f"Active analysis already exists for data_source_id: {data_source_id}. "
                f"Existing analysis ID: {existing_analysis.id}, Status: {existing_analysis.status}, "
                f"Task ID: {existing_analysis.task_id}"
            )
            
            # 检查Celery任务状态
            if existing_analysis.task_id:
                from backend.core.celery_app import celery_app
                try:
                    task_result = celery_app.AsyncResult(existing_analysis.task_id)
                    celery_status = task_result.status
                    logger.info(f"Celery task {existing_analysis.task_id} status: {celery_status}")
                    
                    # 如果Celery任务还在运行，返回现有分析
                    if celery_status in ['PENDING', 'STARTED', 'RETRY']:
                        return existing_analysis
                    # 如果Celery任务已完成或失败，但数据库状态不一致，更新数据库状态
                    elif celery_status == 'SUCCESS' and existing_analysis.status != VideoAnalysisStatus.COMPLETED:
                        existing_analysis.status = VideoAnalysisStatus.COMPLETED
                        await db.commit()
                        return existing_analysis
                    elif celery_status == 'FAILURE' and existing_analysis.status != VideoAnalysisStatus.FAILED:
                        existing_analysis.status = VideoAnalysisStatus.FAILED
                        await db.commit()
                        # 失败的任务允许重新创建
                    else:
                        return existing_analysis
                except Exception as e:
                    logger.warning(f"Failed to check Celery task status: {e}")
                    return existing_analysis
            else:
                return existing_analysis
        
        # 检查是否已有完成的分析（防止重复创建）
        completed_result = await db.execute(
            select(VideoAnalysis).where(
                VideoAnalysis.data_source_id == data_source_id,
                VideoAnalysis.status == VideoAnalysisStatus.COMPLETED,
                VideoAnalysis.is_deleted == False
            ).order_by(VideoAnalysis.created_at.desc())
        )
        completed_analysis = completed_result.scalar_one_or_none()
        
        if completed_analysis:
            logger.warning(
                f"Completed analysis already exists for data_source_id: {data_source_id}. "
                f"Analysis ID: {completed_analysis.id}, Completed at: {completed_analysis.updated_at}"
            )
            return completed_analysis
        
        # 检查最近是否有分析记录（防止频繁创建）
        from datetime import datetime, timedelta
        recent_threshold = datetime.now() - timedelta(minutes=5)  # 5分钟内不允许重复创建
        
        recent_result = await db.execute(
            select(VideoAnalysis).where(
                VideoAnalysis.data_source_id == data_source_id,
                VideoAnalysis.created_at > recent_threshold,
                VideoAnalysis.is_deleted == False
            ).order_by(VideoAnalysis.created_at.desc())
        )
        recent_analysis = recent_result.scalar_one_or_none()
        
        if recent_analysis:
            logger.warning(
                f"Recent analysis found for data_source_id: {data_source_id}. "
                f"Analysis ID: {recent_analysis.id}, Status: {recent_analysis.status}, "
                f"Created: {recent_analysis.created_at}"
            )
            # 如果最近的分析失败了，允许重新创建
            if recent_analysis.status != VideoAnalysisStatus.FAILED:
                return recent_analysis
        
        # 创建新的视频分析记录
        video_analysis = VideoAnalysis(
            data_source_id=data_source_id,
            analysis_type=analysis_type,
            status=VideoAnalysisStatus.PENDING,
            task_id=str(uuid.uuid4()),  # 生成唯一任务ID
            user_id=current_user.id
        )
        
        db.add(video_analysis)
        await db.commit()
        await db.refresh(video_analysis)
        
        logger.info(f"Created new video analysis: {video_analysis.id} for data_source: {data_source_id}")
        return video_analysis
    
    async def perform_visual_analysis(self, data_source: DataSource, video_analysis: VideoAnalysis, progress_callback=None) -> Dict[str, Any]:
        """
        执行视频视觉分析
        
        Args:
            data_source: 数据源对象
            video_analysis: 视频分析对象
            progress_callback: 进度回调函数
            
        Returns:
            视觉分析结果
        """
        try:
            logger.info(f"开始视频视觉分析: {data_source.name}")
            
            # 构建视频文件路径
            video_path = Path(settings.upload_dir) / data_source.file_path
            if not video_path.exists():
                raise FileNotFoundError(f"视频文件不存在: {video_path}")
            
            # 创建帧输出目录
            output_dir = Path(settings.upload_dir) / "video_frames" / str(video_analysis.id)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 1. 提取关键帧
            logger.info("第1步：提取关键帧")
            if progress_callback:
                progress_callback("关键帧提取", 15, "智能提取视频关键帧")
            
            key_frames = self.frame_extractor.extract_key_frames(video_path, output_dir)
            logger.info(f"提取了 {len(key_frames)} 个关键帧")
            
            if not key_frames:
                return {
                    "error": "未能提取到关键帧",
                    "visual_analysis": {},
                    "scene_detection": {},
                    "frame_count": 0
                }
            
            # 2. 视觉语义分析
            logger.info("第2步：视觉语义分析")
            if progress_callback:
                progress_callback("视觉分析", 30, "AI视觉语义理解")
            
            visual_results = await self.vision_service.analyze_video_frames(key_frames)
            
            # 3. 场景序列分析
            logger.info("第3步：场景序列分析")
            if progress_callback:
                progress_callback("场景分析", 45, "场景序列分析")
            
            scene_results = await self.vision_service.analyze_scene_sequence(key_frames)
            
            # 4. 构建完整分析结果
            analysis_result = {
                "visual_analysis": visual_results,
                "scene_detection": scene_results,
                "frame_extraction": {
                    "total_frames_extracted": len(key_frames),
                    "extraction_method": "intelligent_scene_based",
                    "key_frames_info": [
                        {
                            "frame_number": f.frame_number,
                            "timestamp": f.timestamp,
                            "key_frame_reason": f.key_frame_reason,
                            "quality_metrics": {
                                "brightness": f.brightness,
                                "contrast": f.contrast,
                                "sharpness": f.sharpness
                            }
                        } for f in key_frames[:10]  # 只返回前10帧的详细信息
                    ]
                },
                "analysis_metadata": {
                    "video_file": data_source.name,
                    "file_size": data_source.file_size,
                    "analysis_type": video_analysis.analysis_type.value,
                    "processing_timestamp": datetime.now(timezone.utc).isoformat(),
                    "frame_output_dir": str(output_dir)
                }
            }
            
            logger.info(f"视频视觉分析完成: {data_source.name}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"视频视觉分析失败: {e}")
            return {
                "error": str(e),
                "visual_analysis": {},
                "scene_detection": {},
                "frame_extraction": {},
                "analysis_metadata": {
                    "video_file": data_source.name if data_source else "unknown",
                    "error_timestamp": datetime.now(timezone.utc).isoformat(),
                    "analysis_phase": "visual_analysis"
                }
            }
    
    async def perform_enhanced_analysis(self, data_source: DataSource, video_analysis: VideoAnalysis, progress_callback=None) -> Dict[str, Any]:
        """
        执行增强视频分析（包含视觉+音频）
        """
        try:
            logger.info(f"开始增强视频分析: {data_source.name}")
            
            # 更新进度：开始分析
            if progress_callback:
                progress_callback("视觉分析", 10, "开始视频视觉分析")
            
            # 1. 执行视觉分析
            visual_results = await self.perform_visual_analysis(data_source, video_analysis, progress_callback)
            
            # 更新进度：视觉分析完成
            if progress_callback:
                progress_callback("音频分析", 50, "开始音频语义分析")
            
            # 2. 音频分析（Phase 3实现）
            audio_results = await self.perform_audio_analysis(data_source, video_analysis, progress_callback)
            
            # 更新进度：音频分析完成
            if progress_callback:
                progress_callback("多模态融合", 80, "开始多模态语义融合")
            
            # 3. 多模态融合（Phase 4实现）
            multimodal_results = await self.perform_multimodal_fusion(visual_results, audio_results, progress_callback)
            
            # 更新进度：分析完成
            if progress_callback:
                progress_callback("结果整理", 95, "生成综合分析报告")
            
            enhanced_result = {
                "visual_analysis": visual_results.get("visual_analysis", {}),
                "scene_detection": visual_results.get("scene_detection", {}),
                "frame_extraction": visual_results.get("frame_extraction", {}),
                "audio_analysis": audio_results,  # Phase 3 完成
                "multimodal_fusion": multimodal_results,  # Phase 4 完成
                "analysis_metadata": {
                    **visual_results.get("analysis_metadata", {}),
                    "analysis_mode": "enhanced",
                    "phases_completed": ["visual_analysis", "audio_analysis", "multimodal_fusion"],
                    "phases_pending": []
                }
            }
            
            # 处理错误情况
            errors = []
            if visual_results.get("error"):
                errors.append(f"视觉分析错误: {visual_results['error']}")
            if audio_results.get("error"):
                errors.append(f"音频分析错误: {audio_results['error']}")
            if multimodal_results.get("error"):
                errors.append(f"多模态融合错误: {multimodal_results['error']}")
            
            if errors:
                enhanced_result["errors"] = errors
            
            # 最终进度更新
            if progress_callback:
                progress_callback("完成", 100, "视频深度分析完成")
            
            logger.info(f"增强视频分析完成: {data_source.name}")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"增强视频分析失败: {e}")
            if progress_callback:
                progress_callback("失败", 0, f"分析失败: {str(e)}")
            return {
                "error": str(e),
                "visual_analysis": {},
                "scene_detection": {},
                "frame_extraction": {},
                "audio_analysis": {},
                "multimodal_fusion": {},
                "analysis_metadata": {
                    "analysis_mode": "enhanced",
                    "phases_completed": [],
                    "phases_pending": ["visual_analysis", "audio_analysis", "multimodal_fusion"],
                    "error": str(e)
                }
            }
    
    async def perform_audio_analysis(self, data_source: DataSource, video_analysis: VideoAnalysis, progress_callback=None) -> Dict[str, Any]:
        """
        执行视频音频分析
        
        Args:
            data_source: 数据源对象
            video_analysis: 视频分析对象
            progress_callback: 进度回调函数
            
        Returns:
            音频分析结果
        """
        try:
            logger.info(f"开始视频音频分析: {data_source.name}")
            
            # 构建视频文件路径
            video_path = Path(settings.upload_dir) / data_source.file_path
            if not video_path.exists():
                raise FileNotFoundError(f"视频文件不存在: {video_path}")
            
            # 创建音频输出目录
            output_dir = Path(settings.upload_dir) / "video_audio" / str(video_analysis.id)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 更新进度：音频提取
            if progress_callback:
                progress_callback("音频提取", 55, "提取和预处理音频")
            
            # 执行音频分析
            audio_results = await self.audio_service.analyze_video_audio(video_path, output_dir)
            
            # 更新进度：语音识别
            if progress_callback:
                progress_callback("语音识别", 65, "Whisper语音转文字")
            
            # 更新进度：音频语义分析
            if progress_callback:
                progress_callback("音频语义", 75, "音频内容语义分析")
            
            # 添加分析元数据
            audio_results["analysis_metadata"] = {
                **audio_results.get("analysis_metadata", {}),
                "video_analysis_id": video_analysis.id,
                "data_source_id": data_source.id,
                "analysis_phase": "audio_semantic_analysis"
            }
            
            logger.info(f"视频音频分析完成: {data_source.name}")
            return audio_results
            
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
                    "video_file": data_source.name if data_source else "unknown",
                    "error_timestamp": datetime.now(timezone.utc).isoformat(),
                    "analysis_phase": "audio_semantic_analysis"
                }
            }
    
    async def perform_multimodal_fusion(self, visual_results: Dict[str, Any], audio_results: Dict[str, Any], progress_callback=None) -> Dict[str, Any]:
        """
        执行多模态融合分析
        
        Args:
            visual_results: 视觉分析结果
            audio_results: 音频分析结果  
            progress_callback: 进度回调函数
            
        Returns:
            多模态融合结果
        """
        try:
            logger.info("开始多模态语义融合")
            
            # 更新进度：多模态融合
            if progress_callback:
                progress_callback("多模态融合", 85, "视觉+音频语义融合")
            
            # 执行多模态融合
            fusion_results = await self.multimodal_service.fuse_multimodal_analysis(visual_results, audio_results)
            
            # 更新进度：故事分析
            if progress_callback:
                progress_callback("故事分析", 90, "情节和关键时刻识别")
            
            logger.info("多模态语义融合完成")
            return fusion_results
            
        except Exception as e:
            logger.error(f"多模态融合失败: {e}")
            return {
                "error": str(e),
                "timeline_alignment": {},
                "semantic_correlation": {},
                "story_analysis": {},
                "emotion_tracking": {},
                "comprehensive_understanding": {},
                "analysis_metadata": {
                    "error_timestamp": datetime.now(timezone.utc).isoformat(),
                    "analysis_phase": "multimodal_fusion"
                }
            }

    @staticmethod
    async def get_video_analysis_by_id(
        db: AsyncSession,
        analysis_id: int,
        current_user: User
    ) -> VideoAnalysis:
        """
        获取指定的视频分析，严格权限检查
        """
        query = (
            select(VideoAnalysis)
            .options(
                selectinload(VideoAnalysis.frames),
                selectinload(VideoAnalysis.segments)
            )
            .where(VideoAnalysis.id == analysis_id)
            .where(VideoAnalysis.is_deleted == False)
        )
        
        result = await db.execute(query)
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            raise NotFoundException(f"Video analysis with ID {analysis_id} not found")
        
        # 权限检查：只有所有者可以访问
        if analysis.user_id != current_user.id:
            raise AuthorizationException("You don't have permission to access this video analysis")
        
        return analysis

    @staticmethod
    async def get_analyses_by_data_source(
        db: AsyncSession,
        data_source_id: int,
        current_user: User
    ) -> List[VideoAnalysis]:
        """
        获取指定数据源的所有视频分析
        """
        # 先验证数据源访问权限
        await VideoAnalysisService._validate_data_source_access(db, data_source_id, current_user)
        
        query = (
            select(VideoAnalysis)
            .where(VideoAnalysis.data_source_id == data_source_id)
            .where(VideoAnalysis.is_deleted == False)
            .order_by(VideoAnalysis.created_at.desc())
        )
        
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_video_analysis(
        db: AsyncSession,
        analysis_id: int,
        update_data: VideoAnalysisUpdate,
        current_user: User
    ) -> VideoAnalysis:
        """
        更新视频分析，遵循权限检查
        """
        # 先获取并验证权限
        analysis = await VideoAnalysisService.get_video_analysis_by_id(db, analysis_id, current_user)
        
        # 更新字段
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(analysis, field, value)
        
        analysis.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(analysis)
        
        return analysis

    @staticmethod
    async def delete_video_analysis(
        db: AsyncSession,
        analysis_id: int,
        current_user: User
    ) -> None:
        """
        删除视频分析（软删除）
        """
        # 先获取并验证权限
        analysis = await VideoAnalysisService.get_video_analysis_by_id(db, analysis_id, current_user)
        
        # 软删除
        analysis.is_deleted = True
        analysis.deleted_at = datetime.now(timezone.utc)
        
        await db.commit()
        logger.info(f"Video analysis {analysis_id} marked as deleted")

    @staticmethod
    async def _validate_data_source_access(
        db: AsyncSession,
        data_source_id: int,
        current_user: User
    ) -> DataSource:
        """
        验证数据源存在且用户有权限访问
        严格遵循现有的权限检查模式
        """
        # 查询数据源
        result = await db.execute(
            select(DataSource).where(
                DataSource.id == data_source_id,
                DataSource.is_deleted == False
            )
        )
        data_source = result.scalar_one_or_none()
        
        if not data_source:
            raise NotFoundException("Data Source", data_source_id)
        
        # 权限检查：只有所有者可以访问
        if data_source.user_id != current_user.id:
            raise AuthorizationException("You don't have permission to access this data source")
        
        return data_source

    @staticmethod
    async def _get_active_analysis(db: AsyncSession, data_source_id: int) -> Optional[VideoAnalysis]:
        """
        检查是否有进行中的分析任务
        """
        result = await db.execute(
            select(VideoAnalysis).where(
                VideoAnalysis.data_source_id == data_source_id,
                VideoAnalysis.status.in_([
                    VideoAnalysisStatus.PENDING,
                    VideoAnalysisStatus.IN_PROGRESS
                ]),
                VideoAnalysis.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    @classmethod
    async def get_active_analysis_by_data_source(
        cls,
        db: AsyncSession,
        data_source_id: int,
        current_user: User
    ) -> Optional[VideoAnalysis]:
        """
        获取指定数据源的活跃分析任务
        包含用户权限验证，供API端点使用
        """
        # 验证数据源存在且用户有权限访问
        await cls._validate_data_source_access(db, data_source_id, current_user)
        
        # 查找活跃的分析任务
        result = await db.execute(
            select(VideoAnalysis).where(
                VideoAnalysis.data_source_id == data_source_id,
                VideoAnalysis.status.in_([
                    VideoAnalysisStatus.PENDING,
                    VideoAnalysisStatus.IN_PROGRESS
                ]),
                VideoAnalysis.is_deleted == False
            ).order_by(VideoAnalysis.created_at.desc())  # 最新的分析任务优先
        )
        return result.scalar_one_or_none()

    @classmethod
    async def get_latest_analysis_by_data_source(
        cls,
        db: AsyncSession,
        data_source_id: int,
        current_user: User
    ) -> Optional[VideoAnalysis]:
        """
        获取指定数据源的最新视频分析记录
        
        Args:
            db: 数据库会话
            data_source_id: 数据源ID
            current_user: 当前用户
            
        Returns:
            最新的视频分析记录，如果不存在则返回None
        """
        # 验证数据源权限
        data_source = await cls._validate_data_source_access(db, data_source_id, current_user)
        
        # 查找最新的视频分析记录
        result = await db.execute(
            select(VideoAnalysis).where(
                VideoAnalysis.data_source_id == data_source_id,
                VideoAnalysis.is_deleted == False
            ).order_by(VideoAnalysis.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    # VideoFrame相关方法
    @staticmethod
    async def create_video_frame(
        db: AsyncSession,
        video_analysis_id: int,
        frame_data: Dict[str, Any]
    ) -> VideoFrame:
        """创建视频帧记录"""
        video_frame = VideoFrame(
            video_analysis_id=video_analysis_id,
            **frame_data
        )
        
        db.add(video_frame)
        await db.commit()
        await db.refresh(video_frame)
        
        return video_frame

    @staticmethod
    async def get_video_frames(
        db: AsyncSession,
        video_analysis_id: int
    ) -> List[VideoFrame]:
        """获取分析的所有帧"""
        query = (
            select(VideoFrame)
            .where(VideoFrame.video_analysis_id == video_analysis_id)
            .where(VideoFrame.is_deleted == False)
            .order_by(VideoFrame.frame_number)
        )
        
        result = await db.execute(query)
        return result.scalars().all()

    # VideoSegment相关方法
    @staticmethod
    async def create_video_segment(
        db: AsyncSession,
        video_analysis_id: int,
        segment_data: Dict[str, Any]
    ) -> VideoSegment:
        """创建视频片段记录"""
        video_segment = VideoSegment(
            video_analysis_id=video_analysis_id,
            **segment_data
        )
        
        db.add(video_segment)
        await db.commit()
        await db.refresh(video_segment)
        
        return video_segment

    @staticmethod
    async def get_video_segments(
        db: AsyncSession,
        video_analysis_id: int
    ) -> List[VideoSegment]:
        """获取分析的所有片段"""
        query = (
            select(VideoSegment)
            .where(VideoSegment.video_analysis_id == video_analysis_id)
            .where(VideoSegment.is_deleted == False)
            .order_by(VideoSegment.start_time)
        )
        
        result = await db.execute(query)
        return result.scalars().all()


# 创建全局服务实例
video_analysis_service = VideoAnalysisService() 