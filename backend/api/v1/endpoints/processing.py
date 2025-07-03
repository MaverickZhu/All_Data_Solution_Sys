from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from celery.result import AsyncResult

from backend.core.database import get_db
from backend.services.data_source_service import DataSourceService
from backend.services.user_service import UserService
from backend.models.user import User
from backend.processing.tasks import run_profiling_task
from backend.core.celery_app import celery_app

router = APIRouter()


@router.post(
    "/profile/{data_source_id}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="启动数据源分析任务"
)
async def start_profiling_job(
    data_source_id: int,
    project_id: int = Query(..., description="项目ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(UserService.get_current_active_user),
):
    """
    为指定的数据源启动一个异步的数据探查分析任务。
    """
    # 验证用户有权访问该数据源
    data_source = await DataSourceService.get_data_source_by_id(
        db, data_source_id=data_source_id, project_id=project_id
    )
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data source not found in this project.",
        )

    # 启动后台Celery任务
    task = run_profiling_task.delay(data_source.id)

    return {"task_id": task.id, "message": "Profiling task started successfully."}


@router.get("/profile/status/{task_id}", summary="查询分析任务的状态和结果")
def get_profiling_status(task_id: str):
    """
    根据任务ID查询Celery任务的状态。
    """
    task_result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None
    }
    
    if task_result.failed():
        response['error'] = str(task_result.info)

    return response 