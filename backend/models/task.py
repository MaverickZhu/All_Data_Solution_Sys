from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Any, Dict
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from pydantic import BaseModel

from backend.core.database import Base
from .base import Auditable

if TYPE_CHECKING:
    from .project import Project
    from .data_source import DataSource

class Task(Base, Auditable):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String, nullable=False, index=True) # e.g., 'profile', 'clean', 'train'
    status = Column(String, default="pending", nullable=False, index=True) # pending, running, success, failed
    progress = Column(Float, default=0.0)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    results = Column(JSON, nullable=True) # To store results, e.g., path to a report file
    logs = Column(String, nullable=True) # To store logs or error messages
    
    # Foreign Keys
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False)

    # Relationships
    project = relationship("Project")
    data_source = relationship("DataSource", back_populates="tasks")


class TaskResponse(BaseModel):
    id: int
    task_type: str
    status: str
    progress: float
    results: Optional[Dict[str, Any]] = None
    logs: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 