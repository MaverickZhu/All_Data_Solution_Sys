"""
数据源管理服务
"""
import os
import shutil
from pathlib import Path
from typing import List
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from backend.models.data_source import DataSource, DataSourceCreate, DataSourceType
from backend.models.project import Project
from backend.core.exceptions import NotFoundException, AuthorizationException
from backend.core.config import settings

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
        upload_file: UploadFile
    ) -> DataSource:
        """从上传的文件创建数据源"""
        
        # 1. 保存文件到磁盘
        project_upload_dir = DataSourceService.BASE_UPLOAD_DIR / str(project.id)
        project_upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = project_upload_dir / upload_file.filename
        try:
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)
        finally:
            upload_file.file.close()

        # 2. 创建数据库记录
        file_size = file_path.stat().st_size
        file_extension = file_path.suffix.lstrip('.').lower()
        
        try:
            ds_type = DataSourceType(file_extension)
        except ValueError:
            ds_type = DataSourceType.UNKNOWN

        ds_create_data = DataSourceCreate(
            name=upload_file.filename,
            project_id=project.id,
            type=ds_type,
            file_path=str(file_path.relative_to(DataSourceService.BASE_UPLOAD_DIR)),
            file_size=file_size
        )
        
        db_ds = DataSource(**ds_create_data.model_dump())
        db.add(db_ds)
        await db.commit()
        await db.refresh(db_ds)
        
        return db_ds

    @staticmethod
    async def delete_data_source(db: AsyncSession, ds: DataSource) -> None:
        """删除数据源（软删除数据库记录并删除物理文件）"""
        
        # 1. 删除物理文件
        if ds.file_path:
            full_file_path = DataSourceService.BASE_UPLOAD_DIR / ds.file_path
            if full_file_path.exists() and full_file_path.is_file():
                os.remove(full_file_path)

        # 2. 软删除数据库记录
        await db.delete(ds)
        await db.commit()
        
        return None 