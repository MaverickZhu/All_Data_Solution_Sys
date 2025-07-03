"""
数据源模型
"""
from typing import Optional
import enum
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum as SQLAlchemyEnum, Float
from sqlalchemy.orm import relationship

from backend.core.database import Base
from .base import TimestampMixin, SoftDeleteMixin, BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema
from enum import Enum
from ..models.base import Auditable

class DataSourceType(str, Enum):
    """数据源类型枚举"""
    CSV = "csv"
    JSON = "json"
    TXT = "txt"
    PDF = "pdf"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DATABASE = "database"
    UNKNOWN = "unknown"

class DataSource(Base, Auditable):
    """数据源模型"""
    
    __tablename__ = "data_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    project = relationship("Project", back_populates="data_sources")
    
    data_source_type = Column(String, nullable=False, default=DataSourceType.UNKNOWN.value)
    
    # 对于文件类型的数据源
    file_path = Column(String(1024), nullable=True)
    file_size = Column(Float, nullable=True)  # in bytes
    
    # 对于数据库类型的数据源
    connection_params = Column(String, nullable=True)  # For database connections, stored as JSON string

    def __repr__(self):
        return f"<DataSource(id={self.id}, name='{self.name}', project_id={self.project_id})>"

# Pydantic模型

class DataSourceBase(BaseCreateSchema):
    name: str
    description: Optional[str] = None
    type: DataSourceType

class DataSourceCreate(DataSourceBase):
    project_id: int
    file_path: Optional[str] = None
    file_size: Optional[float] = None
    connection_params: Optional[dict] = None

class DataSourceUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    description: Optional[str] = None

class DataSourceResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    project_id: int
    data_source_type: str
    file_path: Optional[str] = None
    file_size: Optional[float] = None

    class Config:
        from_attributes = True

class DataSourceInDB(DataSourceBase, BaseResponseSchema):
    id: int
    project_id: int
    file_path: Optional[str] = None
    file_size: Optional[float] = None

    model_config = {
        "from_attributes": True
    }

# 在Project模型中添加反向关系
from backend.models.project import Project
Project.data_sources = relationship("DataSource", back_populates="project", cascade="all, delete-orphan") 