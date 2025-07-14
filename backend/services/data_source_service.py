"""
数据源管理服务
"""
import os
import shutil
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import imagehash

from backend.models.data_source import DataSource, DataSourceCreate, DataSourceType, ProfileStatusEnum
from backend.models.project import Project
from backend.core.exceptions import NotFoundException, AuthorizationException
from backend.core.config import settings
from backend.models.user import User
from backend.services.mongo_service import mongo_service
from backend.models.data_source import AnalysisCategory
import mimetypes
import uuid

logger = logging.getLogger("service")

def get_file_extension(filename: str) -> str:
    return filename.split(".")[-1] if "." in filename else ""

def get_analysis_category(file_type: str) -> AnalysisCategory:
    # A more robust mapping can be implemented here
    text_based = ["txt", "md", "pdf", "docx", "py", "js", "html", "css", "json", "xml", "csv"]
    image_based = ["jpg", "jpeg", "png", "gif", "bmp", "tiff"]
    tabular_based = ["csv", "xls", "xlsx"] # Note: csv is in both text and tabular

    if file_type in tabular_based:
        return AnalysisCategory.TABULAR
    if file_type in image_based:
        return AnalysisCategory.IMAGE
    if file_type in text_based:
        return AnalysisCategory.TEXTUAL
    
    return AnalysisCategory.UNSTRUCTURED


class DataSourceService:
    
    BASE_UPLOAD_DIR = Path(settings.upload_dir)

    @staticmethod
    async def get_data_source_by_id(db: AsyncSession, ds_id: int, project_id: int) -> DataSource:
        """获取单个数据源并验证其是否属于指定项目"""
        result = await db.execute(select(DataSource).where(DataSource.id == ds_id, DataSource.is_deleted == False))
        ds = result.scalar_one_or_none()
        
        if not ds:
            raise NotFoundException("Data Source", ds_id)
        if ds.project_id != project_id:
            raise AuthorizationException("Data source does not belong to this project.")
        
        # First, refresh the object to ensure all columns from Postgres are loaded
        await db.refresh(ds)
        
        # Then, aggregate data from MongoDB for text-based analysis results
        if ds.analysis_category == AnalysisCategory.TEXTUAL:
            analysis_results = mongo_service.get_text_analysis_results(ds.id)
            if analysis_results:
                # Dynamically add the analysis results to the response object
                # This doesn't change the underlying SQLAlchemy model, just the Pydantic model for the response
                ds.keywords = analysis_results.get("keywords")
                ds.summary = analysis_results.get("summary")
                ds.sentiment = analysis_results.get("sentiment")
            
        return ds

    @staticmethod
    async def get_data_sources_by_project(db: AsyncSession, project_id: int) -> List[DataSource]:
        """获取一个项目的所有数据源"""
        result = await db.execute(
            select(DataSource)
            .where(DataSource.project_id == project_id, DataSource.is_deleted == False)
            .order_by(DataSource.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def create_data_source_from_upload(
        db: AsyncSession, project: Project, upload_file: UploadFile, current_user: User
    ) -> DataSource:
        """
        Creates a new DataSource from an uploaded file and saves it to the database.
        """
        # 恢复原有的按项目分目录存储方式
        project_upload_dir = Path(settings.upload_dir) / str(project.id)
        project_upload_dir.mkdir(parents=True, exist_ok=True)

        sanitized_filename = "".join(
            c for c in upload_file.filename if c.isalnum() or c in (".", "_", "-")
        ).strip()
        unique_filename = f"{uuid.uuid4()}_{sanitized_filename}"
        file_path = project_upload_dir / unique_filename

        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)

            file_size = file_path.stat().st_size
            file_extension = get_file_extension(sanitized_filename)
            analysis_cat = get_analysis_category(file_extension)

            db_ds = DataSource(
                name=sanitized_filename,
                file_path=f"{project.id}/{unique_filename}",  # 使用原有的格式：项目ID/文件名
                file_size=file_size,
                file_type=file_extension,
                analysis_category=analysis_cat,
                profile_status=ProfileStatusEnum.pending,
                project_id=project.id,
                user_id=current_user.id,
                created_by=current_user.username,
                uploaded_at=datetime.now(timezone.utc)
            )
            
            db.add(db_ds)
            await db.commit()
            await db.refresh(db_ds)
            
            logger.info(f"Successfully created data source '{db_ds.name}' (ID: {db_ds.id}) in project {project.id}")
            return db_ds
            
        except Exception as e:
            # Clean up the saved file if an error occurs
            if file_path.exists():
                os.remove(file_path)
            logger.error(
                f"Failed to create data source for file '{upload_file.filename}' in project {project.id}. Error: {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save or process the uploaded file.",
            )
        finally:
            upload_file.file.close()

    @staticmethod
    async def delete_data_source(db: AsyncSession, ds: DataSource) -> None:
        """Deletes a data source object and its associated file."""
        # 1. Delete the file from disk
        try:
            file_to_delete = Path(settings.upload_dir) / ds.file_path
            if file_to_delete.exists():
                os.remove(file_to_delete)
                logger.info(f"Successfully deleted file: {file_to_delete}")
            else:
                logger.warning(f"File to delete not found: {file_to_delete}")
        except Exception as e:
            logger.error(f"Error deleting file {ds.file_path}: {e}", exc_info=True)
            # We continue to delete the DB record even if file deletion fails

        # 2. Delete the database record by marking it as deleted
        ds.is_deleted = True
        ds.deleted_at = datetime.now(timezone.utc)
        # In a real-world scenario, you might want to record who deleted it.
        # ds.deleted_by = current_user.id 
        
        await db.commit()
        logger.info(f"Successfully marked data source {ds.id} as deleted.")

    @staticmethod
    async def update_task_info(db: AsyncSession, ds_id: int, task_id: str, status: ProfileStatusEnum) -> Optional[DataSource]:
        """
        Updates the task ID and profiling status for a data source.
        """
        data_source = await db.get(DataSource, ds_id)
        if data_source:
            data_source.task_id = task_id
            data_source.profile_status = status
            await db.commit()
            await db.refresh(data_source)
        return data_source 

    @staticmethod
    async def find_similar_images(
        db: AsyncSession, ds_id: int, project_id: int, threshold: int = 4
    ) -> List[DataSource]:
        """
        Finds data sources with images similar to the specified one.
        """
        # 1. Get the source data source and its hash
        source_ds = await DataSourceService.get_data_source_by_id(db, ds_id, project_id)
        if not source_ds.image_hash:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source data source is not an image or has not been processed yet."
            )
        
        source_hash = imagehash.hex_to_hash(source_ds.image_hash)

        # 2. Get all other data sources with image hashes in the same project
        result = await db.execute(
            select(DataSource).where(
                DataSource.project_id == project_id,
                DataSource.id != ds_id,
                DataSource.image_hash.isnot(None),
                DataSource.is_deleted == False
            )
        )
        all_other_image_sources = result.scalars().all()

        # 3. Compare hashes and find similar ones
        similar_sources = []
        for candidate_ds in all_other_image_sources:
            try:
                candidate_hash = imagehash.hex_to_hash(candidate_ds.image_hash)
                distance = source_hash - candidate_hash
                if distance <= threshold:
                    similar_sources.append(candidate_ds)
            except Exception as e:
                logger.warning(f"Could not compare hash for data source {candidate_ds.id}: {e}")
        
        return similar_sources 