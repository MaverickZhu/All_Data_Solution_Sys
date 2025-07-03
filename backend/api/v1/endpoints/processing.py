from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.security import get_current_active_user
from backend.models.user import User
from backend.processing.profiling_service import ProfilingService

router = APIRouter()

@router.post("/profile/{data_source_id}", response_model=dict)
def start_profiling_task(
    data_source_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Starts a profiling task for a given data source and returns the report.
    """
    # TODO: Add permission check to ensure user has access to the project
    # containing the data source.

    profiling_service = ProfilingService(db)
    try:
        report = profiling_service.generate_profile_report(data_source_id)
        return report
    except (ValueError, TypeError, FileNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Generic error for other unexpected issues
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}") 