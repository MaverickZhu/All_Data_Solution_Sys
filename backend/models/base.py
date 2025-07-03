"""
数据模型基类
提供通用的模型功能
"""
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Column, DateTime, Integer, String, Boolean, func
from sqlalchemy.ext.declarative import declared_attr
from pydantic import BaseModel, ConfigDict
import pytz
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class TimestampMixin:
    """时间戳混入类"""
    
    @declared_attr
    def created_at(cls):
        return Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    @declared_attr
    def updated_at(cls):
        return Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class SoftDeleteMixin:
    """软删除混入类"""
    
    @declared_attr
    def deleted_at(cls):
        return Column(DateTime(timezone=True), nullable=True)
    
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


class Page(BaseModel):
    items: List
    page: int
    size: int
    total: int
    pages: int
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    @classmethod
    def create(cls, items: List, page: int, size: int, total: int):
        return cls(
            items=items,
            page=page,
            size=size,
            total=total,
            pages=(total + size - 1) // size if size > 0 else 0
        )


class Auditable:
    """
    一个提供审计字段（创建时间、更新时间、软删除）的Mixin类。
    所有时间都以UTC时区存储。
    """
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment="最后更新时间")
    deleted_at = Column(DateTime(timezone=True), nullable=True, comment="删除时间")
    is_deleted = Column(Boolean, default=False, nullable=False, comment="是否被删除") 