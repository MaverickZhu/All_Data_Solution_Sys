"""
项目管理服务
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.models.project import Project, ProjectCreate, ProjectUpdate
from backend.models.user import User
from backend.core.exceptions import NotFoundException, AuthorizationException
from datetime import datetime

class ProjectService:
    @staticmethod
    async def create_project(db: AsyncSession, project_data: ProjectCreate, current_user: User) -> Project:
        """创建一个新项目"""
        db_project = Project(**project_data.model_dump(), user_id=current_user.id)
        db.add(db_project)
        await db.commit()
        await db.refresh(db_project)
        return db_project

    @staticmethod
    async def get_project_by_id(db: AsyncSession, project_id: int, current_user: User) -> Project:
        """通过ID获取项目，并检查权限"""
        result = await db.execute(select(Project).where(Project.id == project_id, Project.is_deleted == False))
        project = result.scalar_one_or_none()
        if not project:
            raise NotFoundException("Project", project_id)
        
        # 只有项目所有者或超级用户可以查看
        if project.user_id != current_user.id and not current_user.is_superuser:
            raise AuthorizationException("You don't have permission to access this project.")
            
        return project

    @staticmethod
    async def get_user_projects(db: AsyncSession, user_id: int) -> List[Project]:
        """获取一个用户的所有项目"""
        result = await db.execute(
            select(Project)
            .where(Project.user_id == user_id, Project.is_deleted == False)
            .order_by(Project.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def update_project(db: AsyncSession, project_id: int, project_update: ProjectUpdate, current_user: User) -> Project:
        """更新项目信息"""
        project = await ProjectService.get_project_by_id(db, project_id, current_user) # 权限检查已包含
        
        update_data = project_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)
            
        await db.commit()
        await db.refresh(project)
        return project

    @staticmethod
    async def delete_project(db: AsyncSession, project_id: int, current_user: User) -> None:
        """软删除项目"""
        project = await ProjectService.get_project_by_id(db, project_id, current_user) # 权限检查已包含
        
        project.is_deleted = True
        project.deleted_at = datetime.utcnow()
        project.status = "deleted"
        
        await db.commit() 