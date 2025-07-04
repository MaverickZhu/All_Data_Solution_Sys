"""
数据库连接和会话管理
支持PostgreSQL、MongoDB、Redis、Milvus、Neo4j
"""
from typing import AsyncGenerator, Optional, Generator, ClassVar
from contextlib import asynccontextmanager

# SQLAlchemy for PostgreSQL
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy.pool import NullPool
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker

# MongoDB
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

# Redis
import redis.asyncio as redis
from redis.asyncio import ConnectionPool

# # Milvus - 暂时注释，需要单独安装
# from pymilvus import connections, Collection

# # Neo4j - 暂时注释，需要单独安装
from neo4j import AsyncGraphDatabase

from backend.core.config import settings
import logging

logger = logging.getLogger(__name__)

# ==================== PostgreSQL ====================

# 创建异步引擎
postgres_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_pre_ping=True,  # 检查连接健康状态
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    postgres_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 声明所有模型的基础类
Base = declarative_base()

# 同步数据库引擎和会话工厂 (为Celery任务准备)
sync_engine = create_engine(settings.sync_database_url, echo=False)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI异步依赖，用于获取数据库会话"""
    async with AsyncSessionLocal() as session:
        yield session

def get_sync_db() -> Generator[Session, None, None]:
    """为Celery任务等后台同步进程获取同步数据库会话"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """初始化数据库（创建所有表）"""
    async with postgres_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("PostgreSQL数据库初始化完成")


# ==================== MongoDB ====================

class MongoDB:
    """MongoDB连接管理器"""
    
    client = None
    database = None
    
    @classmethod
    async def connect(cls):
        """连接MongoDB"""
        try:
            cls.client = AsyncIOMotorClient(settings.mongodb_url)
            cls.database = cls.client[settings.mongodb_database]
            # 测试连接
            await cls.client.server_info()
            logger.info("MongoDB连接成功")
        except Exception as e:
            logger.error(f"MongoDB连接失败: {e}")
            raise
    
    @classmethod
    async def disconnect(cls):
        """断开MongoDB连接"""
        if cls.client:
            cls.client.close()
            logger.info("MongoDB连接已关闭")
    
    @classmethod
    def get_database(cls):
        """获取数据库实例"""
        if not cls.database:
            raise RuntimeError("MongoDB未连接，请先调用connect()")
        return cls.database
    
    @classmethod
    def get_collection(cls, name: str):
        """获取集合"""
        return cls.get_database()[name]


# ==================== Redis ====================

class RedisManager:
    """Redis连接管理器"""
    
    pool: Optional[ConnectionPool] = None
    
    @classmethod
    async def connect(cls):
        """创建Redis连接池"""
        try:
            cls.pool = ConnectionPool.from_url(
                settings.redis_url,
                password=settings.redis_password,
                decode_responses=True,
                max_connections=50
            )
            # 测试连接
            async with redis.Redis(connection_pool=cls.pool) as client:
                await client.ping()
            logger.info("Redis连接池创建成功")
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            raise
    
    @classmethod
    async def disconnect(cls):
        """关闭Redis连接池"""
        if cls.pool:
            await cls.pool.disconnect()
            logger.info("Redis连接池已关闭")
    
    @classmethod
    @asynccontextmanager
    async def get_client(cls):
        """获取Redis客户端"""
        if not cls.pool:
            raise RuntimeError("Redis未连接，请先调用connect()")
        async with redis.Redis(connection_pool=cls.pool) as client:
            yield client


# ==================== Milvus ====================
# 暂时注释掉Milvus相关代码

# class MilvusManager:
#     """Milvus向量数据库管理器"""
#     
#     _connected: bool = False
#     
#     @classmethod
#     def connect(cls):
#         """连接Milvus"""
#         try:
#             connections.connect(
#                 alias="default",
#                 host=settings.milvus_host,
#                 port=settings.milvus_port
#             )
#             cls._connected = True
#             logger.info("Milvus连接成功")
#         except Exception as e:
#             logger.error(f"Milvus连接失败: {e}")
#             raise
#     
#     @classmethod
#     def disconnect(cls):
#         """断开Milvus连接"""
#         if cls._connected:
#             connections.disconnect("default")
#             cls._connected = False
#             logger.info("Milvus连接已关闭")
#     
#     @classmethod
#     def get_collection(cls, name: str) -> Collection:
#         """获取集合"""
#         if not cls._connected:
#             raise RuntimeError("Milvus未连接，请先调用connect()")
#         return Collection(name)


# ==================== Neo4j ====================
class Neo4jManager:
    """Neo4j图数据库管理器"""
    
    driver: Optional[AsyncGraphDatabase] = None
    
    @classmethod
    async def connect(cls):
        """连接Neo4j"""
        try:
            cls.driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password)
            )
            # 测试连接
            async with cls.driver.session() as session:
                await session.run("RETURN 1")
            logger.info("Neo4j连接成功")
        except Exception as e:
            logger.error(f"Neo4j连接失败: {e}")
            raise
    
    @classmethod
    async def disconnect(cls):
        """断开Neo4j连接"""
        if cls.driver:
            await cls.driver.close()
            logger.info("Neo4j连接已关闭")
    
    @classmethod
    @asynccontextmanager
    async def get_session(cls):
        """获取Neo4j会话"""
        if not cls.driver:
            raise RuntimeError("Neo4j未连接，请先调用connect()")
        async with cls.driver.session() as session:
            yield session


# ==================== 数据库初始化函数 ====================

async def init_databases():
    """初始化所有数据库连接"""
    # PostgreSQL
    await init_db()
    
    # MongoDB
    await MongoDB.connect()
    
    # Redis
    await RedisManager.connect()
    
    # # Milvus - 暂时注释
    # MilvusManager.connect()
    
    # Neo4j
    await Neo4jManager.connect()
    
    logger.info("所有数据库连接初始化完成")


async def close_databases():
    """关闭所有数据库连接"""
    # PostgreSQL
    await postgres_engine.dispose()
    
    # MongoDB
    await MongoDB.disconnect()
    
    # Redis
    await RedisManager.disconnect()
    
    # # Milvus - 暂时注释
    # MilvusManager.disconnect()
    
    # Neo4j
    await Neo4jManager.disconnect()
    
    logger.info("所有数据库连接已关闭") 