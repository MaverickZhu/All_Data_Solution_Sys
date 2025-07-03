from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.core.database import Base
from backend.models.base import TimestampMixin

class ProcessingTask(Base, TimestampMixin):
    __tablename__ = "processing_tasks"

    id = Column(Integer, primary_key=True, index=True)
    
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False)
    
    task_type = Column(String, nullable=False, index=True) # e.g., 'profile', 'clean', 'train'
    status = Column(String, default="pending", nullable=False, index=True) # pending, running, success, failed
    progress = Column(Float, default=0.0)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    results = Column(JSON, nullable=True) # To store results, e.g., path to a report file
    logs = Column(String, nullable=True) # To store logs or error messages

    project = relationship("Project")
    data_source = relationship("DataSource") 