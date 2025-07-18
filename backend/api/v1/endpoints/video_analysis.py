"""
视频分析API端点
基于现有稳定架构设计，遵循data_sources.py的设计模式
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.security import get_current_active_user
from backend.models.user import User
from backend.models.video_analysis import (
    VideoAnalysisResponse, VideoAnalysisCreate, VideoAnalysisUpdate,
    VideoAnalysisType, VideoAnalysisStatus,
    VideoFrameResponse, VideoSegmentResponse
)
from backend.services.video_analysis_service import VideoAnalysisService

router = APIRouter()
logger = logging.getLogger("api")


@router.post(
    "/{data_source_id}/analyze",
    response_model=VideoAnalysisResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_video_analysis(
    data_source_id: int = Path(..., description="The ID of the data source"),
    analysis_type: VideoAnalysisType = Query(VideoAnalysisType.SEMANTIC, description="Type of analysis to perform"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    创建视频分析任务
    遵循现有API端点的设计模式和权限检查
    """
    logger.debug(f"Creating video analysis for data_source_id: {data_source_id}")
    
    try:
        logger.info(
            f"Starting video analysis creation: data_source_id={data_source_id}, type={analysis_type} by user: {current_user.email}",
            extra={"data_source_id": data_source_id, "analysis_type": analysis_type, "user": current_user.email}
        )
        
        # 创建视频分析
        video_analysis = await VideoAnalysisService.create_video_analysis(
            db, data_source_id, analysis_type, current_user
        )
        
        # 启动Celery深度分析任务
        from backend.processing.tasks import run_video_deep_analysis_task
        task = run_video_deep_analysis_task.delay(video_analysis.id)
        
        # 更新任务ID
        video_analysis.task_id = task.id
        await db.commit()
        await db.refresh(video_analysis)
        
        # 转换数据格式以符合API模型要求
        if video_analysis.visual_objects:
            # 如果visual_objects是字符串列表，转换为字典列表
            if isinstance(video_analysis.visual_objects, list) and video_analysis.visual_objects:
                if isinstance(video_analysis.visual_objects[0], str):
                    video_analysis.visual_objects = [
                        {"name": obj, "confidence": 1.0, "category": "detected"} 
                        for obj in video_analysis.visual_objects
                    ]
        
        # 确保scene_changes格式正确
        if video_analysis.scene_changes:
            if isinstance(video_analysis.scene_changes, list) and video_analysis.scene_changes:
                if isinstance(video_analysis.scene_changes[0], (int, float)):
                    video_analysis.scene_changes = [
                        {"timestamp": change, "type": "scene_change"} 
                        for change in video_analysis.scene_changes
                    ]
        
        logger.info(
            f"Video analysis created successfully: ID={video_analysis.id}, Task ID={task.id}",
            extra={"video_analysis_id": video_analysis.id, "task_id": task.id}
        )
        
        return video_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to create video analysis: {str(e)}",
            extra={"data_source_id": data_source_id, "user": current_user.email}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create video analysis"
        )


@router.get(
    "/{analysis_id}",
    response_model=VideoAnalysisResponse
)
async def get_video_analysis(
    analysis_id: int = Path(..., description="The ID of the video analysis"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取视频分析详情
    遵循现有API端点的查询模式
    """
    logger.debug(f"Getting video analysis: {analysis_id}")
    
    try:
        video_analysis = await VideoAnalysisService.get_video_analysis_by_id(
            db, analysis_id, current_user
        )
        
        # 转换数据格式以符合API模型要求
        if video_analysis.visual_objects:
            # 如果visual_objects是字符串列表，转换为字典列表
            if isinstance(video_analysis.visual_objects, list) and video_analysis.visual_objects:
                if isinstance(video_analysis.visual_objects[0], str):
                    video_analysis.visual_objects = [
                        {"name": obj, "confidence": 1.0, "category": "detected"} 
                        for obj in video_analysis.visual_objects
                    ]
        
        # 确保scene_changes格式正确
        if video_analysis.scene_changes:
            if isinstance(video_analysis.scene_changes, list) and video_analysis.scene_changes:
                if isinstance(video_analysis.scene_changes[0], (int, float)):
                    video_analysis.scene_changes = [
                        {"timestamp": change, "type": "scene_change"} 
                        for change in video_analysis.scene_changes
                    ]
        
        logger.info(
            f"Video analysis retrieved successfully: ID={analysis_id}",
            extra={"video_analysis_id": analysis_id}
        )
        
        return video_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get video analysis {analysis_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve video analysis"
        )


@router.get(
    "/data-sources/{data_source_id}",
    response_model=List[VideoAnalysisResponse]
)
async def get_video_analyses_by_data_source(
    data_source_id: int = Path(..., description="The ID of the data source"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取指定数据源的所有视频分析
    """
    logger.debug(f"Getting video analyses for data_source_id: {data_source_id}")
    
    try:
        analyses = await VideoAnalysisService.get_analyses_by_data_source(
            db, data_source_id, current_user
        )
        
        logger.info(
            f"Retrieved {len(analyses)} video analyses for data_source_id: {data_source_id}",
            extra={"data_source_id": data_source_id, "count": len(analyses)}
        )
        
        return analyses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get video analyses for data_source {data_source_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve video analyses"
        )


@router.put(
    "/{analysis_id}",
    response_model=VideoAnalysisResponse
)
async def update_video_analysis(
    analysis_id: int = Path(..., description="The ID of the video analysis"),
    update_data: VideoAnalysisUpdate = ...,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    更新视频分析结果
    遵循现有API端点的更新模式
    """
    logger.debug(f"Updating video analysis: {analysis_id}")
    
    try:
        video_analysis = await VideoAnalysisService.update_video_analysis(
            db, analysis_id, update_data, current_user
        )
        
        logger.info(
            f"Video analysis updated successfully: ID={analysis_id}",
            extra={"video_analysis_id": analysis_id}
        )
        
        return video_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update video analysis {analysis_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update video analysis"
        )


@router.delete(
    "/{analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_video_analysis(
    analysis_id: int = Path(..., description="The ID of the video analysis"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    删除视频分析
    遵循现有API端点的删除模式（软删除）
    """
    logger.debug(f"Deleting video analysis: {analysis_id}")
    
    try:
        await VideoAnalysisService.delete_video_analysis(db, analysis_id, current_user)
        
        logger.info(
            f"Video analysis deleted successfully: ID={analysis_id}",
            extra={"video_analysis_id": analysis_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete video analysis {analysis_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete video analysis"
        )


@router.get(
    "/{analysis_id}/status",
    response_model=dict
)
async def get_video_analysis_status(
    analysis_id: int = Path(..., description="The ID of the video analysis"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取视频分析状态
    用于前端轮询检查分析进度
    """
    logger.debug(f"Getting video analysis status: {analysis_id}")
    
    try:
        video_analysis = await VideoAnalysisService.get_video_analysis_by_id(
            db, analysis_id, current_user
        )
        
        # 转换数据格式以符合API模型要求
        if video_analysis.visual_objects:
            # 如果visual_objects是字符串列表，转换为字典列表
            if isinstance(video_analysis.visual_objects, list) and video_analysis.visual_objects:
                if isinstance(video_analysis.visual_objects[0], str):
                    video_analysis.visual_objects = [
                        {"name": obj, "confidence": 1.0, "category": "detected"} 
                        for obj in video_analysis.visual_objects
                    ]
        
        # 确保scene_changes格式正确
        if video_analysis.scene_changes:
            if isinstance(video_analysis.scene_changes, list) and video_analysis.scene_changes:
                if isinstance(video_analysis.scene_changes[0], (int, float)):
                    video_analysis.scene_changes = [
                        {"timestamp": change, "type": "scene_change"} 
                        for change in video_analysis.scene_changes
                    ]
        
        status_info = {
            "analysis_id": video_analysis.id,
            "status": video_analysis.status,
            "task_id": video_analysis.task_id,
            "processing_time": video_analysis.processing_time,
            "error_message": video_analysis.error_message,
            "current_phase": video_analysis.current_phase,
            "progress_percentage": video_analysis.progress_percentage,
            "progress_message": video_analysis.progress_message,
            "created_at": video_analysis.created_at,
            "updated_at": video_analysis.updated_at
        }
        
        logger.info(
            f"Video analysis status retrieved: ID={analysis_id}, status={video_analysis.status}",
            extra={"video_analysis_id": analysis_id, "status": video_analysis.status}
        )
        
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get video analysis status {analysis_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve video analysis status"
        )


@router.get(
    "/{analysis_id}/frames",
    response_model=List[VideoFrameResponse]
)
async def get_video_frames(
    analysis_id: int = Path(..., description="The ID of the video analysis"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取视频分析的所有帧
    """
    logger.debug(f"Getting video frames for analysis: {analysis_id}")
    
    try:
        # 先验证用户权限
        await VideoAnalysisService.get_video_analysis_by_id(db, analysis_id, current_user)
        
        frames = await VideoFrameService.get_frames_by_analysis(db, analysis_id)
        
        logger.info(
            f"Retrieved {len(frames)} frames for analysis: {analysis_id}",
            extra={"video_analysis_id": analysis_id, "frame_count": len(frames)}
        )
        
        return frames
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get video frames for analysis {analysis_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve video frames"
        )


@router.get(
    "/{analysis_id}/segments",
    response_model=List[VideoSegmentResponse]
)
async def get_video_segments(
    analysis_id: int = Path(..., description="The ID of the video analysis"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取视频分析的所有片段
    """
    logger.debug(f"Getting video segments for analysis: {analysis_id}")
    
    try:
        # 先验证用户权限
        await VideoAnalysisService.get_video_analysis_by_id(db, analysis_id, current_user)
        
        segments = await VideoSegmentService.get_segments_by_analysis(db, analysis_id)
        
        logger.info(
            f"Retrieved {len(segments)} segments for analysis: {analysis_id}",
            extra={"video_analysis_id": analysis_id, "segment_count": len(segments)}
        )
        
        return segments
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get video segments for analysis {analysis_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve video segments"
        ) 