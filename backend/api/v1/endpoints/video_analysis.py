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
    添加幂等性检查，防止重复分析
    """
    logger.debug(f"Creating video analysis for data_source_id: {data_source_id}")
    
    try:
        logger.info(
            f"Starting video analysis creation: data_source_id={data_source_id}, type={analysis_type} by user: {current_user.email}",
            extra={"data_source_id": data_source_id, "analysis_type": analysis_type, "user": current_user.email}
        )
        
        # 🔥 强化幂等性检查：基于data_source_id防止重复分析
        existing_analysis = await VideoAnalysisService.get_latest_analysis_by_data_source(
            db, data_source_id, current_user
        )
        
        if existing_analysis:
            # 如果分析状态为进行中，返回现有分析
            if existing_analysis.status in [VideoAnalysisStatus.PENDING, VideoAnalysisStatus.IN_PROGRESS]:
                logger.info(
                    f"Found existing active analysis: ID={existing_analysis.id}, status={existing_analysis.status}",
                    extra={"video_analysis_id": existing_analysis.id, "status": existing_analysis.status}
                )
                return existing_analysis
            
            # 🔥 关键修复：如果分析已完成，也返回现有分析，不要重复创建！
            elif existing_analysis.status == VideoAnalysisStatus.COMPLETED:
                logger.info(
                    f"Found existing completed analysis: ID={existing_analysis.id}, returning existing result",
                    extra={"video_analysis_id": existing_analysis.id, "status": existing_analysis.status}
                )
                return existing_analysis
            
            # 只有在分析失败时才允许重新分析
            elif existing_analysis.status == VideoAnalysisStatus.FAILED:
                logger.info(
                    f"Previous analysis failed (ID={existing_analysis.id}), creating new analysis",
                    extra={"previous_analysis_id": existing_analysis.id, "status": existing_analysis.status}
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
    "/{analysis_id}/status",
    response_model=dict
)
async def get_video_analysis_status(
    analysis_id: int = Path(..., description="The ID of the video analysis"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取视频分析状态（用于前端轮询）
    按analysis_id查询分析状态
    """
    logger.debug(f"Getting video analysis status by analysis_id: {analysis_id}")
    
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
            "data_source_id": video_analysis.data_source_id,
            "status": video_analysis.status,
            "task_id": video_analysis.task_id,
            "processing_time": video_analysis.processing_time,
            "error_message": video_analysis.error_message,
            "current_phase": video_analysis.current_phase,
            "progress_percentage": video_analysis.progress_percentage,
            "progress_message": video_analysis.progress_message,
            "created_at": video_analysis.created_at,
            "updated_at": video_analysis.updated_at,
            
            # 🔥 添加完整的分析结果用于前端展示
            "analysis_result": {
                "scene_count": video_analysis.scene_count,
                "key_frames": video_analysis.key_frames,
                "visual_themes": video_analysis.visual_themes,
                "visual_objects": video_analysis.visual_objects,
                "speech_segments": video_analysis.speech_segments,
                "content_tags": video_analysis.content_tags,
                "comprehensive_summary": video_analysis.comprehensive_summary,
                "story_segments": video_analysis.story_segments,
                "key_moments": video_analysis.key_moments,
                "scene_changes": video_analysis.scene_changes,
                "transcription": video_analysis.transcription,
                "model_versions": video_analysis.model_versions
            } if video_analysis.status == 'COMPLETED' else None
        }
        
        logger.info(
            f"Video analysis status retrieved successfully: ID={analysis_id}, status={video_analysis.status}",
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
    "/data-source/{data_source_id}/status",
    response_model=dict
)
async def get_video_analysis_status_by_data_source(
    data_source_id: int = Path(..., description="The ID of the data source"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    通过数据源ID获取视频分析状态和完整结果
    用于前端轮询检查分析进度并获取完整的分析结果
    """
    logger.debug(f"Getting video analysis status by data_source_id: {data_source_id}")
    
    try:
        # 通过data_source_id查找最新的视频分析记录
        video_analysis = await VideoAnalysisService.get_latest_analysis_by_data_source(
            db, data_source_id, current_user
        )
        
        if not video_analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No video analysis found for this data source"
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
            "data_source_id": data_source_id,
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
        
        # 🔥 关键修复：如果分析已完成，从MongoDB获取完整的分析结果
        if video_analysis.status == VideoAnalysisStatus.COMPLETED:
            from backend.services.mongo_service import mongo_service
            
            # 获取基础视频分析结果（包含基本视频属性）
            basic_analysis_result = mongo_service.get_video_analysis_results(data_source_id)
            
            # 获取深度分析结果（包含高级分析）
            deep_analysis_result = mongo_service.get_video_deep_analysis_results(video_analysis.id)
            
            if basic_analysis_result:
                # 构建合并的分析结果
                merged_result = {
                    "analysis_type": "video_enhanced" if deep_analysis_result else "video",
                    # 基础视频属性
                    "video_properties": basic_analysis_result.get("video_properties", {}),
                    "file_info": basic_analysis_result.get("file_info", {}),
                    "metadata": basic_analysis_result.get("metadata", {}),
                    "quality_info": basic_analysis_result.get("quality_info", {}),
                    "analysis_summary": basic_analysis_result.get("analysis_summary", {}),
                }
                
                # 如果有深度分析结果，添加增强功能
                if deep_analysis_result:
                    # 从基础信息构建enhanced_metadata
                    video_props = basic_analysis_result.get("video_properties", {})
                    file_info = basic_analysis_result.get("file_info", {})
                    
                    merged_result.update({
                        "enhanced_metadata": {
                            "width": video_props.get("width"),
                            "height": video_props.get("height"),
                            "fps": video_props.get("fps"),
                            "duration": video_props.get("duration_seconds"),
                            "nb_frames": video_props.get("frame_count"),
                            "format_name": file_info.get("format"),
                            "has_audio": True,  # 大多数视频都有音频
                            "video_codec": "h264",  # 默认值
                            "audio_codec": "aac",   # 默认值
                        },
                        "visual_analysis": deep_analysis_result.get("visual_analysis", {}),
                        "audio_analysis": deep_analysis_result.get("audio_analysis", {}),
                        "scene_detection": deep_analysis_result.get("scene_detection", {}),
                        "multimodal_fusion": deep_analysis_result.get("multimodal_fusion", {}),
                        "analysis_metadata": deep_analysis_result.get("analysis_metadata", {}),
                    })
                    
                    # 添加缩略图路径
                    thumbnail_path = video_props.get("thumbnail_path")
                    if thumbnail_path:
                        merged_result["primary_thumbnail"] = thumbnail_path
                
                # 添加文件大小
                file_size = file_info.get("file_size_bytes")
                if file_size:
                    merged_result["file_size"] = file_size
                    
                # 添加格式信息
                format_name = file_info.get("format")
                if format_name:
                    merged_result["format"] = format_name
                
                status_info["analysis_result"] = merged_result
                logger.info(f"Successfully merged analysis results for data_source_id: {data_source_id}, video_analysis_id: {video_analysis.id}")
            else:
                logger.warning(f"No basic analysis result found in MongoDB for data_source_id: {data_source_id}")
        
        logger.info(
            f"Video analysis status retrieved by data_source_id: data_source_id={data_source_id}, analysis_id={video_analysis.id}, status={video_analysis.status}",
            extra={"data_source_id": data_source_id, "video_analysis_id": video_analysis.id, "status": video_analysis.status}
        )
        
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get video analysis status for data_source_id {data_source_id}: {str(e)}")
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