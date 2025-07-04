"""
项目数据模型
"""
from __future__ import annotations

import enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, Enum as SQLAlchemyEnum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from backend.core.database import Base
from .base import (Auditable, BaseCreateSchema, BaseResponseSchema,
                   BaseUpdateSchema)

if TYPE_CHECKING:
    from .data_source import DataSource, DataSourceResponse
    from .user import User


class ProjectStatus(str, enum.Enum):
    """项目状态枚举"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    PENDING = "pending"
    DELETED = "deleted"

class Project(Base, Auditable):
    """项目模型"""
    
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(String, nullable=True)
    
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    owner = relationship("User", back_populates="projects")
    
    status = Column(SQLAlchemyEnum(ProjectStatus), default=ProjectStatus.ACTIVE, nullable=False)
    
    data_sources = relationship("DataSource", back_populates="project", cascade="all, delete-orphan")
    
    # 使用JSONB存储项目特定配置
    # from sqlalchemy.dialects.postgresql import JSONB
    # config = Column(JSONB, nullable=True)

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', owner_id={self.owner_id})>"


# Pydantic模型

class ProjectBase(BaseCreateSchema):
    name: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    # config: Optional[Dict[str, Any]] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseUpdateSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    # config: Optional[Dict[str, Any]] = None

class ProjectResponse(ProjectBase, BaseResponseSchema):
    owner_id: int
    data_sources: List["DataSourceResponse"] = []

    class Config:
        from_attributes = True 