"""
日志配置模块
提供统一的日志记录功能
"""
import logging
import logging.config
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict
from pythonjsonlogger import jsonlogger
from contextvars import ContextVar

from backend.core.config import settings

# 定义一个 ContextVar 来存储 request_id, 可以在应用中的任何地方访问
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """自定义JSON日志格式化器"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        """添加自定义字段"""
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        
        # 添加时间戳
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # 添加应用信息
        log_record['app_name'] = settings.app_name
        log_record['app_version'] = settings.app_version
        log_record['environment'] = settings.app_env
        
        # 添加 request_id
        request_id = request_id_var.get()
        if request_id:
            log_record['request_id'] = request_id
        
        # 添加日志级别名称
        log_record['level'] = record.levelname
        
        # 添加模块和函数信息
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # 添加进程和线程信息
        log_record['process'] = record.process
        log_record['thread'] = record.thread
        
        # 如果有异常信息，添加异常详情
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)


def setup_logging():
    """设置日志配置"""
    
    # 确保日志目录存在
    log_dir = Path(settings.log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 日志配置字典
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            # 控制台格式（彩色输出）
            "console": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            # 文件格式（JSON格式）
            "json": {
                "()": CustomJsonFormatter,
                "format": "%(timestamp)s %(level)s %(name)s %(message)s"
            },
            # 详细格式（用于错误日志）
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            # 控制台处理器
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.log_level,
                "formatter": "console",
                "stream": sys.stdout
            },
            # 文件处理器（所有日志）
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.log_level,
                "formatter": "json",
                "filename": settings.log_file,
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8"
            },
            # 错误文件处理器
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": str(Path(settings.log_file).parent / "error.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8"
            }
        },
        "loggers": {
            # 应用日志器
            "app": {
                "level": settings.log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            # 数据库日志器
            "database": {
                "level": settings.log_level,
                "handlers": ["console", "file"],
                "propagate": False
            },
            # API日志器
            "api": {
                "level": settings.log_level,
                "handlers": ["console", "file"],
                "propagate": False
            },
            # 服务日志器
            "service": {
                "level": settings.log_level,
                "handlers": ["console", "file"],
                "propagate": False
            },
            # AI/ML日志器
            "ml": {
                "level": settings.log_level,
                "handlers": ["console", "file"],
                "propagate": False
            }
        },
        "root": {
            "level": settings.log_level,
            "handlers": ["console", "file"]
        }
    }
    
    # 应用日志配置
    logging.config.dictConfig(logging_config)
    
    # 设置第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    # 创建主日志器
    logger = logging.getLogger("app")
    logger.info("日志系统初始化完成", extra={
        "log_level": settings.log_level,
        "log_file": settings.log_file,
        "environment": settings.app_env
    })
    
    return logger


# 日志装饰器
def log_execution_time(logger_name: str = "app"):
    """
    记录函数执行时间的装饰器
    
    Args:
        logger_name: 日志器名称
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name)
            start_time = datetime.utcnow()
            
            try:
                result = await func(*args, **kwargs)
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                logger.info(
                    f"Function {func.__name__} executed successfully",
                    extra={
                        "function": func.__name__,
                        "execution_time": execution_time,
                        "status": "success"
                    }
                )
                return result
            except Exception as e:
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                logger.error(
                    f"Function {func.__name__} failed",
                    extra={
                        "function": func.__name__,
                        "execution_time": execution_time,
                        "status": "error",
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise
        
        def sync_wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name)
            start_time = datetime.utcnow()
            
            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                logger.info(
                    f"Function {func.__name__} executed successfully",
                    extra={
                        "function": func.__name__,
                        "execution_time": execution_time,
                        "status": "success"
                    }
                )
                return result
            except Exception as e:
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                logger.error(
                    f"Function {func.__name__} failed",
                    extra={
                        "function": func.__name__,
                        "execution_time": execution_time,
                        "status": "error",
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise
        
        # 根据函数类型返回相应的包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 全局日志器实例
logger = setup_logging() 