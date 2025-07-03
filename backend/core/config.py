"""
应用配置管理
使用Pydantic BaseSettings进行配置验证和管理
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基本信息
    app_name: str = Field(default="多模态智能数据分析平台", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    app_env: str = Field(default="development", env="APP_ENV")
    debug: bool = Field(default=True, env="DEBUG")
    
    # API配置
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    
    # 安全配置
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # 数据库配置
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/multimodal_analysis",
        env="DATABASE_URL"
    )
    db_pool_size: int = Field(default=20, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, env="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")
    
    # MongoDB配置
    mongodb_url: str = Field(default="mongodb://localhost:27017", env="MONGODB_URL")
    mongodb_database: str = Field(default="multimodal_analysis", env="MONGODB_DATABASE")
    
    # Redis配置
    redis_url: str = Field(default="redis://localhost:6380/0", env="REDIS_URL")
    redis_password: Optional[str] = Field(default="multimodal123", env="REDIS_PASSWORD")
    
    # Milvus配置
    milvus_host: str = Field(default="localhost", env="MILVUS_HOST")
    milvus_port: int = Field(default=19530, env="MILVUS_PORT")
    
    # Neo4j配置
    neo4j_uri: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER")
    neo4j_password: str = Field(default="password123", env="NEO4J_PASSWORD")
    
    # CORS配置
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    
    # 日志配置
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/app.log", env="LOG_FILE")
    
    # AI模型配置
    model_cache_dir: str = Field(default="./models", env="MODEL_CACHE_DIR")
    embedding_model: str = Field(default="BAAI/bge-base-zh-v1.5", env="EMBEDDING_MODEL")
    llm_model: str = Field(default="chatglm3-6b", env="LLM_MODEL")
    
    # 文件上传配置
    upload_dir: str = Field(default="./uploads", env="UPLOAD_DIR")
    max_upload_size: int = Field(default=104857600, env="MAX_UPLOAD_SIZE")  # 100MB
    allowed_extensions: List[str] = Field(
        default=["pdf", "docx", "txt", "csv", "xlsx", "json", "jpg", "png", "mp3", "mp4"],
        env="ALLOWED_EXTENSIONS"
    )
    
    # Celery配置
    celery_broker_url: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """解析CORS源"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("allowed_extensions", pre=True)
    def parse_allowed_extensions(cls, v):
        """解析允许的文件扩展名"""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v
    
    def create_directories(self):
        """创建必要的目录"""
        dirs = [
            self.upload_dir,
            self.model_cache_dir,
            os.path.dirname(self.log_file)
        ]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 创建全局配置实例
settings = Settings()

# 创建必要的目录
settings.create_directories() 