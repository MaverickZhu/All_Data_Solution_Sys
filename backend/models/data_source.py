"""
数据源模型
"""
from __future__ import annotations

import enum
from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel
from sqlalchemy import (Column, Enum as DBEnum, Float, ForeignKey, Integer,
                        JSON, String, Text)
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import relationship

from backend.core.database import Base
from .base import (Auditable, BaseCreateSchema, BaseResponseSchema,
                   BaseUpdateSchema)

# 使用TYPE_CHECKING来避免循环导入，这对于类型提示和静态分析器是有效的
# 它只在类型检查时导入模块，在运行时则不会，从而解决了循环依赖问题
if TYPE_CHECKING:
    from .project import Project
    from .task import Task
    from .user import User


class DataSourceType(str, enum.Enum):
    """数据源类型枚举"""
    CSV = "csv"
    JSON = "json"
    TXT = "txt"
    PDF = "pdf"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DATABASE = "database"
    API = "api"
    UNKNOWN = "unknown"


class ProfileStatusEnum(str, enum.Enum):
    """数据分析任务状态枚举"""
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class DataSource(Base, Auditable):
    """数据源模型"""

    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    type = Column(PgEnum(DataSourceType, name="data_source_type_enum"), nullable=False)
    config = Column(JSON, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"))

    # SQLAlchemy通过字符串名称"Project"和"Task"来查找关系，
    # 结合TYPE_CHECKING块中的导入，可以解决循环引用的问题。
    project = relationship("Project", back_populates="data_sources")
    tasks = relationship("Task", back_populates="data_source", cascade="all, delete-orphan")

    # 对于文件类型的数据源
    file_path = Column(String(1024), nullable=True)
    file_size = Column(Float, nullable=True)  # in bytes

    # 数据分析相关字段
    profile_status = Column(PgEnum(ProfileStatusEnum, name="profile_status_enum"), nullable=False, default=ProfileStatusEnum.pending)
    profile_report_path = Column(String, nullable=True)

    def __repr__(self):
        return f"<DataSource(id={self.id}, name='{self.name}', type='{self.type.value}')>"


# Pydantic模型

class DataSourceBase(BaseCreateSchema):
    name: str
    description: Optional[str] = None
    type: DataSourceType


class DataSourceCreate(DataSourceBase):
    project_id: int
    file_path: Optional[str] = None
    file_size: Optional[float] = None


class DataSourceUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    description: Optional[str] = None


class DataSourceResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    project_id: int
    type: DataSourceType
    file_path: Optional[str] = None
    file_size: Optional[float] = None
    profile_status: ProfileStatusEnum
    profile_report_path: Optional[str] = None

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
# from backend.models.project import Project
# Project.data_sources = relationship("DataSource", back_populates="project", cascade="all, delete-orphan") 