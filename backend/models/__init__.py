from .base import Base
from .user import User
from .project import Project
from .data_source import DataSource
from .task import Task

__all__ = ["Base", "User", "Project", "DataSource", "Task"]

# 在所有模型导入后，重建Pydantic模型以解析前向引用
def rebuild_models():
    """重建所有Pydantic模型以解析前向引用"""
    from .project import ProjectResponse
    from .data_source import DataSourceResponse
    from .user import UserResponse
    from .task import TaskResponse
    
    # 重建模型schema
    ProjectResponse.model_rebuild()
    DataSourceResponse.model_rebuild()
    UserResponse.model_rebuild()
    TaskResponse.model_rebuild()

# 自动执行重建
rebuild_models() 