from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from backend.core.database import get_db
from backend.core.security import get_current_active_user
from backend.models.user import User
from backend.services.project_service import ProjectService
from backend.services.data_source_service import DataSourceService
from backend.processing.profiling_service import ProfilingService
from backend.core.exceptions import NotFoundException, AuthorizationException
from backend.models.data_source import DataSource

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/profile/{data_source_id}",
    status_code=status.HTTP_200_OK,
    summary="启动并完成数据源分析任务"
)
async def run_and_get_profiling_report(
    data_source_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    为指定的数据源启动数据探查，并同步返回最终报告的路径。

    **注意**: 这是一个同步操作，对于大型文件可能会很慢。
    未来的版本会将其改进为异步后台任务。
    """
    # 1. 获取数据源实体
    result = await db.execute(select(DataSource).where(DataSource.id == data_source_id, DataSource.is_deleted == False))
    data_source = result.scalar_one_or_none()
    if not data_source:
        raise NotFoundException(detail=f"Data source with id {data_source_id} not found.")

    # 2. 验证用户权限
    await ProjectService.verify_project_owner(db, project_id=data_source.project_id, user_id=current_user.id)

    # 3. 调用服务层执行探查
    try:
        # 服务层现在直接处理并返回一个包含状态和路径的字典
        result = await ProfilingService.run_profiling(db, data_source)
        
        # 3. 更新数据库（如果需要）
        # 例如，将报告路径保存到Task模型中
        # ... (此处省略，待任务模型完善后添加) ...

        return result

    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Profiling task failed for data source {data_source_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal error occurred during profiling."
        ) 