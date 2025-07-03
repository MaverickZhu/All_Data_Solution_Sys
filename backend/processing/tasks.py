import logging
from pathlib import Path

import pandas as pd
from ydata_profiling import ProfileReport

from backend.core.celery_app import celery_app
from backend.core.database import get_db
from backend.models.data_source import DataSource, ProfileStatusEnum
from backend.core.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def run_profiling_task(self, data_source_id: int):
    """
    Celery task to generate a data profile report for a given data source.
    """
    logger.info(f"Celery task started for data source ID: {data_source_id}")
    db_session_gen = get_db()
    db = next(db_session_gen)
    
    try:
        data_source = db.query(DataSource).filter(DataSource.id == data_source_id).first()
        if not data_source:
            logger.error(f"Data source with ID {data_source_id} not found.")
            # We can't easily raise an HTTP exception here, so we log and return.
            # The client can check the task status.
            return {"status": "failed", "error": "Data source not found"}

        # Update status to 'in_progress'
        data_source.profile_status = ProfileStatusEnum.in_progress
        db.commit()
        logger.info(f"Profiling status for data source {data_source_id} set to 'in_progress'.")

        source_file_path = Path(settings.UPLOAD_DIR) / data_source.file_path
        
        if not source_file_path.exists():
            error_msg = f"Data source file not found: {source_file_path}"
            logger.error(error_msg)
            data_source.profile_status = ProfileStatusEnum.failed
            db.commit()
            return {"status": "failed", "error": error_msg}

        if data_source.data_source_type.lower() != 'csv' or source_file_path.suffix.lower() != '.csv':
            error_msg = "Unsupported file type for profiling. Only CSV is supported."
            logger.error(error_msg)
            data_source.profile_status = ProfileStatusEnum.failed
            db.commit()
            return {"status": "failed", "error": error_msg}

        df = pd.read_csv(source_file_path)
        profile = ProfileReport(df, title=f"Profiling Report for {data_source.name}")
        
        report_dir = Path(settings.UPLOAD_DIR) / "reports" / str(data_source.project_id)
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_filename = f"{source_file_path.stem}_profile.html"
        report_path = report_dir / report_filename
        
        profile.to_file(report_path)
        logger.info(f"Successfully generated profiling report at: {report_path}")
        
        relative_report_path = report_path.relative_to(Path(settings.UPLOAD_DIR)).as_posix()
        
        # Update data source with report path and status
        data_source.profile_report_path = relative_report_path
        data_source.profile_status = ProfileStatusEnum.completed
        db.commit()

        logger.info(f"Profiling task completed successfully for data source {data_source_id}.")
        return {
            "status": "completed",
            "report_html_path": relative_report_path
        }

    except Exception as e:
        logger.error(f"An error occurred during profiling task for data source {data_source_id}: {e}", exc_info=True)
        if 'data_source' in locals():
            data_source.profile_status = ProfileStatusEnum.failed
            db.commit()
        # You can use self.update_state to store more details about the failure
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        return {"status": "failed", "error": str(e)}
    finally:
        # Ensure the session is closed
        db.close() 