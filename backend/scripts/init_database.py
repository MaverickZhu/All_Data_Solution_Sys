"""
数据库初始化脚本
创建必要的数据库和测试连接
"""
import asyncio
import sys
import os
import logging

# --- 路径设置 ---
# 将项目根目录（All_Data_Solution_Sys）添加到Python路径
# 这样所有backend下的模块都能被正确导入
backend_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)
# --- 路径设置结束 ---

from sqlalchemy.ext.asyncio import AsyncEngine
from core.database import postgres_engine, Base
from models import user, project # Now this should work
from models.user import User
from models.project import Project
from models.data_source import DataSource

# 设置日志
logging.basicConfig(level=logging.INFO)

async def create_all_tables(db_engine: AsyncEngine):
    """
    连接到数据库并创建所有定义的表
    """
    print("Connecting to the database and preparing to create tables...")
    async with db_engine.begin() as conn:
        print("Dropping all existing tables (if any)...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Creating new tables based on models...")
        await conn.run_sync(Base.metadata.create_all)
    print("✅ All tables created successfully!")

async def main():
    """
    脚本主入口
    """
    await create_all_tables(postgres_engine)

if __name__ == "__main__":
    print("🚀 Starting database schema initialization...")
    asyncio.run(main())
    print("🏁 Database schema initialization complete.") 