"""
数据模型基类
提供通用的模型功能
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, DateTime, Integer, String, Boolean
from sqlalchemy.ext.declarative import declared_attr
from pydantic import BaseModel, ConfigDict


class TimestampMixin:
    """时间戳混入类"""
    
    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False)
    
    @declared_attr
    def updated_at(cls):
        return Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class SoftDeleteMixin:
    """软删除混入类"""
    
    @declared_attr
    def deleted_at(cls):
        return Column(DateTime, nullable=True)
    
    @declared_attr
    def is_deleted(cls):
        return Column(Boolean, default=False, nullable=False)


class BaseSchema(BaseModel):
    """Pydantic基础模式"""
    
    model_config = ConfigDict(
        from_attributes=True,  # 允许从SQLAlchemy模型创建
        validate_assignment=True,  # 赋值时验证
        use_enum_values=True,  # 使用枚举值而不是枚举对象
        str_strip_whitespace=True,  # 自动去除字符串首尾空格
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )


class BaseCreateSchema(BaseSchema):
    """创建操作的基础模式"""
    pass


class BaseUpdateSchema(BaseSchema):
    """更新操作的基础模式"""
    pass


class BaseResponseSchema(BaseSchema):
    """响应的基础模式"""
    id: int
    created_at: datetime
    updated_at: datetime


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = 1
    page_size: int = 20
    
    @property
    def skip(self) -> int:
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        return self.page_size


class PaginatedResponse(BaseModel):
    """分页响应"""
    items: list
    total: int
    page: int
    page_size: int
    pages: int
    
    @classmethod
    def create(cls, items: list, total: int, pagination: PaginationParams):
        """创建分页响应"""
        pages = (total + pagination.page_size - 1) // pagination.page_size
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            pages=pages
        ) 