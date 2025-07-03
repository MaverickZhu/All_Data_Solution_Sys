"""
数据库初始化和数据迁移脚本
创建必要的数据库和测试连接
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

# 现在这个导入应该可以工作了
from backend.core.database import postgres_engine, Base
from backend.models import user, project, data_source # 导入所有需要创建表的模型

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_tables(engine: AsyncEngine):
    """根据模型定义创建所有表"""
    async with engine.begin() as conn:
        logger.info("开始删除所有旧表...")
        await conn.run_sync(Base.metadata.drop_all)
        logger.info("所有旧表删除完毕。")
        
        logger.info("开始创建所有新表...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("所有新表创建成功！")

async def main():
    """主函数，执行数据库初始化"""
    logger.info("启动数据库初始化进程...")
    try:
        await create_tables(postgres_engine)
        logger.info("数据库初始化成功完成。")
    except Exception as e:
        logger.error(f"数据库初始化过程中发生错误: {e}")
        # 在这里可以添加更详细的错误处理，例如打印堆栈跟踪
        import traceback
        traceback.print_exc()
    finally:
        await postgres_engine.dispose()
        logger.info("数据库连接池已关闭。")

if __name__ == "__main__":
    asyncio.run(main()) 