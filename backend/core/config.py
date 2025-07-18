"""
应用配置管理
使用Pydantic BaseSettings进行配置验证和管理
"""
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, AliasChoices
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """
    Application settings.
    """
    
    # 测试模式
    testing: bool = Field(False, validation_alias=AliasChoices("testing", "TESTING"))
    
    # 应用基本信息
    app_name: str = Field("多模态智能数据分析平台", validation_alias=AliasChoices("app_name", "APP_NAME"))
    app_version: str = Field("1.0.0", validation_alias=AliasChoices("app_version", "APP_VERSION"))
    app_description: str = Field("一个集成了多种数据源、AI模型和分析工具的智能数据处理与分析平台。", validation_alias=AliasChoices("app_description", "APP_DESCRIPTION"))
    app_env: str = Field("development", validation_alias=AliasChoices("app_env", "APP_ENV"))
    debug: bool = Field(True, validation_alias=AliasChoices("debug", "DEBUG"))
    
    # API配置
    api_host: str = Field("0.0.0.0", validation_alias=AliasChoices("api_host", "API_HOST"))
    api_port: int = Field(8000, validation_alias=AliasChoices("api_port", "API_PORT"))
    api_prefix: str = Field("/api/v1", validation_alias=AliasChoices("api_prefix", "API_PREFIX"))
    
    # 安全配置
    secret_key: str = Field("your-secret-key-change-in-production", validation_alias=AliasChoices("secret_key", "SECRET_KEY"))
    algorithm: str = Field("HS256", validation_alias=AliasChoices("algorithm", "ALGORITHM"))
    access_token_expire_minutes: int = Field(30, validation_alias=AliasChoices("access_token_expire_minutes", "ACCESS_TOKEN_EXPIRE_MINUTES"))
    refresh_token_expire_days: int = Field(7, validation_alias=AliasChoices("refresh_token_expire_days", "REFRESH_TOKEN_EXPIRE_DAYS"))
    
    # 数据库配置
    database_url: str = Field("postgresql+asyncpg://postgres:password@localhost:5432/multimodal_analysis", validation_alias=AliasChoices("database_url", "DATABASE_URL"))
    db_pool_size: int = Field(20, validation_alias=AliasChoices("db_pool_size", "DB_POOL_SIZE"))
    db_max_overflow: int = Field(10, validation_alias=AliasChoices("db_max_overflow", "DB_MAX_OVERFLOW"))
    db_pool_timeout: int = Field(30, validation_alias=AliasChoices("db_pool_timeout", "DB_POOL_TIMEOUT"))
    
    # 为Celery Worker添加的同步数据库URL
    sync_database_url: Optional[str] = Field(None, validation_alias=AliasChoices("sync_database_url", "SYNC_DATABASE_URL"))
    
    # MongoDB配置
    mongodb_url: str = Field("mongodb://localhost:27018", validation_alias=AliasChoices("mongodb_url", "MONGODB_URL"))
    mongodb_database: str = Field("multimodal_analysis", validation_alias=AliasChoices("mongodb_database", "MONGODB_DATABASE"))
    
    # Redis配置
    redis_url: str = Field("redis://multimodal_redis:6379/0", validation_alias=AliasChoices("redis_url", "REDIS_URL"))
    redis_password: Optional[str] = Field("multimodal123", validation_alias=AliasChoices("redis_password", "REDIS_PASSWORD"))
    
    # Milvus配置
    milvus_host: str = Field("localhost", validation_alias=AliasChoices("milvus_host", "MILVUS_HOST"))
    milvus_port: int = Field(19531, validation_alias=AliasChoices("milvus_port", "MILVUS_PORT"))
    
    # Neo4j配置
    neo4j_uri: str = Field("bolt://localhost:7687", validation_alias=AliasChoices("neo4j_uri", "NEO4J_URI"))
    neo4j_user: str = Field("neo4j", validation_alias=AliasChoices("neo4j_user", "NEO4J_USER"))
    neo4j_password: str = Field("password123", validation_alias=AliasChoices("neo4j_password", "NEO4J_PASSWORD"))
    
    # CORS配置
    cors_origins: List[str] = Field(default=["http://localhost:3000", "http://localhost:8000", "http://localhost:3001", "http://localhost:3080", "http://localhost:8088"], validation_alias=AliasChoices("cors_origins", "CORS_ORIGINS"))
    
    # 日志配置
    log_level: str = Field("INFO", validation_alias=AliasChoices("log_level", "LOG_LEVEL"))
    log_file: str = Field("logs/app.log", validation_alias=AliasChoices("log_file", "LOG_FILE"))
    
    # AI模型配置
    model_cache_dir: str = Field("./models", validation_alias=AliasChoices("model_cache_dir", "MODEL_CACHE_DIR"))
    embedding_model: str = Field("BAAI/bge-base-zh-v1.5", validation_alias=AliasChoices("embedding_model", "EMBEDDING_MODEL"))
    llm_model: str = Field("chatglm3-6b", validation_alias=AliasChoices("llm_model", "LLM_MODEL"))
    
    # 文件上传配置
    upload_dir: str = Field("./uploads", validation_alias=AliasChoices("upload_dir", "UPLOAD_DIR"))
    max_upload_size: int = Field(2147483648, validation_alias=AliasChoices("max_upload_size", "MAX_UPLOAD_SIZE"))  # 2GB
    allowed_extensions: List[str] = Field(default=["pdf", "docx", "txt", "csv", "xlsx", "json", "jpg", "jpeg", "png", "gif", "mp3", "wav", "m4a", "flac", "mp4", "avi", "mov", "mkv", "wmv", "flv", "webm", "m4v", "3gp"], validation_alias=AliasChoices("allowed_extensions", "ALLOWED_EXTENSIONS"))
    
    # Celery配置
    celery_broker_url: str = Field("redis://:multimodal123@multimodal_redis:6379/1", validation_alias=AliasChoices("celery_broker_url", "CELERY_BROKER_URL"))
    celery_result_backend: str = Field("redis://:multimodal123@multimodal_redis:6379/2", validation_alias=AliasChoices("celery_result_backend", "CELERY_RESULT_BACKEND"))
    celery_task_always_eager: bool = Field(False, validation_alias=AliasChoices("celery_task_always_eager", "CELERY_TASK_ALWAYS_EAGER"))

    # MongoDB settings
    mongodb_url: str = Field("mongodb://localhost:27018", validation_alias=AliasChoices("mongodb_url", "MONGODB_URL"))
    mongodb_db_name: str = Field("multimodal_analysis", validation_alias=AliasChoices("mongodb_db_name", "MONGODB_DB_NAME"))

    # Milvus settings
    milvus_host: str = Field("localhost", validation_alias=AliasChoices("milvus_host", "MILVUS_HOST"))
    milvus_port: int = Field(19531, validation_alias=AliasChoices("milvus_port", "MILVUS_PORT"))
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra='ignore'  # 忽略.env中多余的变量
    )
    
    @field_validator("celery_task_always_eager", mode='before')
    def set_celery_eager_for_testing(cls, v, values):
        """在测试模式下强制Celery任务同步执行"""
        if values.data.get("testing"):
            return True
        return v
    
    @field_validator("sync_database_url", mode='before')
    def set_sync_database_url(cls, v, values):
        """如果未提供，则根据异步URL自动生成同步URL，以供Celery等同步任务使用"""
        if v:
            return v
        async_url = values.data.get("database_url")
        if async_url:
            return async_url.replace("+asyncpg", "")
        raise ValueError("DATABASE_URL must be set to generate SYNC_DATABASE_URL")
    
    @field_validator("cors_origins", "allowed_extensions", mode='before')
    def parse_str_to_list(cls, v):
        """解析逗号分隔的字符串为列表"""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",")]
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


# 创建全局配置实例
settings = Settings()

# 创建必要的目录
settings.create_directories() 