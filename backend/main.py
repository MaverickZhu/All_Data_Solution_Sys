"""
多模态智能数据分析平台 - 主应用入口
"""
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import time
import uuid

from starlette_prometheus import PrometheusMiddleware, metrics

# 统一使用从 `backend` 开始的绝对路径
from backend.core.exceptions import get_exception_handlers
from backend.core.config import settings
from backend.core.logging import setup_logging, logger, request_id_var
from backend.api.v1.router import api_router

# 设置日志
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 导入所有数据库管理器的正确类名
    from backend.core.database import (
        init_db, 
        close_databases, 
        MongoDB, 
        RedisManager, 
        Neo4jManager
    )
    from backend.core.milvus_manager import MilvusManager

    logger.info("Application startup: Initializing database connections...")
    # 初始化各个数据库连接
    await init_db() # 初始化PostgreSQL表结构
    await MongoDB.connect()
    await RedisManager.connect()
    await Neo4jManager.connect()
    MilvusManager.connect()
    MilvusManager.get_or_create_collection()
    
    # 创建必要的目录
    settings.create_directories()
    
    yield
    
    logger.info("Application shutdown: Closing database connections...")
    # 关闭所有数据库连接
    MilvusManager.disconnect()
    await close_databases() # 这个函数会处理所有数据库的关闭
    logger.info("All database connections closed.")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    exception_handlers=get_exception_handlers()
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加信任主机中间件（安全考虑）
if settings.app_env == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.yourdomain.com", "yourdomain.com"]
    )

# 添加GZip压缩中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 添加Prometheus中间件和/metrics端点
app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", metrics)


# 自定义中间件 - 合并请求日志、计时和大小限制
MAX_REQUEST_BODY_SIZE = 200 * 1024 * 1024  # 200MB

@app.middleware("http")
async def combined_middleware(request: Request, call_next):
    """
    合并了日志、计时和请求体大小限制的中间件
    """
    # 1. 检查请求体大小
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_REQUEST_BODY_SIZE:
        return JSONResponse(
            status_code=413,  # Payload Too Large
            content={
                "error": {
                    "code": "PAYLOAD_TOO_LARGE",
                    "message": f"Request body size exceeds the limit of {MAX_REQUEST_BODY_SIZE / 1024 / 1024:.0f}MB."
                }
            }
        )

    # 2. 设置请求ID和日志
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request_id_var.set(request_id)
    
    start_time = time.time()
    
    logger.info(
        f"Request started",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else "unknown",
            "request_id": request_id
        }
    )
    
    # 3. 执行请求
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        
        logger.info(
            f"Request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": process_time,
                "request_id": request_id
            }
        )
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "process_time": process_time,
                "request_id": request_id,
                "error": str(e)
            },
            exc_info=True
        )
        # 确保即使在异常情况下也返回一个标准的JSON错误响应
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred.",
                    "request_id": request_id
                }
            }
        )


# 根路由
@app.get("/", tags=["Root"])
async def read_root():
    """根端点，返回项目信息"""
    return {
        "project": settings.app_name,
        "version": settings.app_version,
        "description": "多模态智能数据分析平台" # 暂时硬编码
    }


# 健康检查端点
@app.get("/health", tags=["Health"])
async def health_check():
    """健康检查 - 返回服务状态"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env
    }


# 包含v1的API路由
app.include_router(api_router, prefix="/api/v1")


# 404处理器
@app.exception_handler(404)
async def not_found(request: Request, exc):
    """处理404错误"""
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "NOT_FOUND",
                "message": f"Path {request.url.path} not found"
            }
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        app_dir="." # 在直接运行时，当前目录就是backend
    )