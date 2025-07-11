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

logger = logging.getLogger("service")

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
        if ds.data_source_type in [DataSourceType.TXT, DataSourceType.CSV, DataSourceType.JSON]:
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
        db: AsyncSession, 
        project: Project, 
        upload_file: UploadFile,
        current_user: User
    ) -> DataSource:
        """从上传的文件创建数据源"""
        logger.debug(f"Starting to process file upload: {upload_file.filename} for project ID: {project.id}")
        
        try:
            # 1. 保存文件到磁盘
            project_upload_dir = DataSourceService.BASE_UPLOAD_DIR / str(project.id)
            project_upload_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Upload directory prepared: {project_upload_dir}")
            
            file_path = project_upload_dir / upload_file.filename
            
            try:
                with file_path.open("wb") as buffer:
                    shutil.copyfileobj(upload_file.file, buffer)
                logger.info(f"File saved successfully to {file_path}", extra={"file_path": str(file_path)})
            finally:
                upload_file.file.close()

            # 2. 创建数据库记录
            file_size = file_path.stat().st_size
            file_extension = file_path.suffix.lstrip('.').lower()
            logger.debug(f"File size: {file_size}, extension: {file_extension}")
            
            # 新增：扩展名到枚举的映射
            extension_to_type_map = {
                'csv': DataSourceType.CSV,
                'json': DataSourceType.JSON,
                'txt': DataSourceType.TXT,
                'md': DataSourceType.TXT, # 将Markdown也视为纯文本类型
                'pdf': DataSourceType.PDF,
                'jpg': DataSourceType.IMAGE,
                'jpeg': DataSourceType.IMAGE,
                'png': DataSourceType.IMAGE,
                'docx': DataSourceType.TXT, # Alembic迁移失败，回退到将DOCX视为TXT处理
            }
            
            # 确保使用正确的枚举值（小写）
            ds_type = extension_to_type_map.get(file_extension, DataSourceType.UNKNOWN)
            if ds_type == DataSourceType.UNKNOWN:
                logger.warning(
                    f"Unknown file type: '{file_extension}', defaulting to UNKNOWN.",
                    extra={"file_extension": file_extension}
                )

            db_ds = DataSource(
                name=upload_file.filename,
                project_id=project.id,
                data_source_type=ds_type,
                file_path=str(file_path.relative_to(DataSourceService.BASE_UPLOAD_DIR)),
                file_size=file_size,
                profile_status=ProfileStatusEnum.pending,
                uploaded_at=datetime.now(timezone.utc),
                user_id=current_user.id,
                created_by=current_user.username
            )

            logger.debug(f"DataSource object created, type: {db_ds.data_source_type}")
            
            db.add(db_ds)
            await db.commit()
            await db.refresh(db_ds)
            
            logger.info(f"Data source record created in DB with ID: {db_ds.id}", extra={"data_source_id": db_ds.id})

            # 再次刷新以确保所有字段都已从数据库加载
            await db.refresh(db_ds)
            return db_ds
            
        except Exception as e:
            logger.error(f"Failed to create data source from upload: {e}", exc_info=True)
            # Raise a more specific internal exception or re-raise
            raise

    @staticmethod
    async def delete_data_source(db: AsyncSession, ds: DataSource) -> None:
        """Deletes a data source object and its associated file."""
        # 1. Delete the file from disk
        try:
            file_to_delete = DataSourceService.BASE_UPLOAD_DIR / ds.file_path
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