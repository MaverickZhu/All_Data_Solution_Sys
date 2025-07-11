import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from celery.result import AsyncResult # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.services.data_source_service import DataSourceService
from backend.processing.tasks import run_profiling_task
from backend.core.celery_app import celery_app
from backend.models.user import User
from backend.core.security import get_current_active_user
from backend.models.data_source import ProfileStatusEnum

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/profile/{data_source_id}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="启动数据源分析任务"
)
async def start_profiling_job(
    data_source_id: int,
    project_id: int = Query(..., description="项目ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    为指定的数据源启动一个异步的数据探查分析任务。
    """
    logger.info(f"[DEBUG] Received request to start profiling for data_source_id={data_source_id} in project_id={project_id} by user {current_user.email}")

    # 验证用户有权访问该数据源
    data_source = await DataSourceService.get_data_source_by_id(
        db, ds_id=data_source_id, project_id=project_id
    )
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found in this project.",
        )

    # 启动后台Celery任务
    logger.info(f"[DEBUG] Found data source, dispatching Celery task for data_source_id: {data_source.id}")
    task = run_profiling_task.delay(data_source.id)
    logger.info(f"[DEBUG] Celery task dispatched with task_id: {task.id}")
    
    # 立即持久化任务ID和状态
    await DataSourceService.update_task_info(
        db,
        ds_id=data_source.id,
        task_id=task.id,
        status=ProfileStatusEnum.pending
    )

    return {"task_id": task.id, "message": "Profiling task started successfully."}


@router.get("/profile/{task_id}", summary="查询分析任务的状态和结果")
async def get_profiling_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    根据任务ID查询Celery任务的状态。
    """
    logger.info(f"[DEBUG] Checking status for task_id: {task_id}")
    task_result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None
    }
    
    if task_result.failed():
        response['error'] = str(task_result.info)
        logger.error(f"[DEBUG] Task {task_id} failed: {task_result.info}")
    else:
        logger.info(f"[DEBUG] Task {task_id} status: {task_result.status}")

    return response 