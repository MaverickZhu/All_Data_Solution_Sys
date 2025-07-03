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

# 统一使用从 `backend` 开始的绝对路径
from backend.core.database import init_databases, close_databases
from backend.core.exceptions import get_exception_handlers
from backend.core.config import settings
from backend.core.logging import setup_logging
from backend.api.v1.router import api_router

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理器
    """
    # 应用启动时执行
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    await init_databases()
    logger.info("All databases initialized successfully")
    
    yield
    
    # 应用关闭时执行
    logger.info("Shutting down application...")
    await close_databases()
    logger.info("Application shutdown complete")


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


# 自定义中间件 - 请求日志和计时
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志和响应时间"""
    request_id = request.headers.get("X-Request-ID", "")
    start_time = time.time()
    
    # 记录请求信息
    logger.info(
        f"Request started",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else "unknown",
            "request_id": request_id
        }
    )
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # 添加自定义响应头
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        
        # 记录响应信息
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
        raise


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