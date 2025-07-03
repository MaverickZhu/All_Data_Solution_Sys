"""
项目数据模型
"""
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from core.database import Base
from .base import TimestampMixin, SoftDeleteMixin, BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema
import enum
from pydantic import BaseModel

class ProjectStatus(str, enum.Enum):
    """项目状态枚举"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    PENDING = "pending"
    DELETED = "deleted"

class Project(Base, TimestampMixin, SoftDeleteMixin):
    """项目模型"""
    
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    owner = relationship("User", back_populates="projects")
    
    status = Column(SQLAlchemyEnum(ProjectStatus), default=ProjectStatus.ACTIVE, nullable=False)
    
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
    # 可以添加owner信息
    # owner: Optional[UserResponse] = None

# 在User模型中添加反向关系
from .user import User
User.projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan") 