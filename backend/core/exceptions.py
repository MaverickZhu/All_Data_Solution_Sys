"""
自定义异常和异常处理模块
定义应用特定的异常类和全局异常处理器
"""
from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger("app")


# ==================== 基础异常类 ====================

class AppException(Exception):
    """应用基础异常类"""
    
    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        初始化异常
        
        Args:
            message: 错误消息
            code: 错误代码
            status_code: HTTP状态码
            details: 额外的错误详情
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


# ==================== 业务异常类 ====================

class NotFoundException(AppException):
    """资源未找到异常"""
    
    def __init__(self, resource: str, identifier: Union[str, int]):
        super().__init__(
            message=f"{resource} with identifier {identifier} not found",
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "identifier": str(identifier)}
        )


class DuplicateException(AppException):
    """重复资源异常"""
    
    def __init__(self, resource: str, field: str, value: Any):
        super().__init__(
            message=f"{resource} with {field}='{value}' already exists",
            code="DUPLICATE_RESOURCE",
            status_code=status.HTTP_409_CONFLICT,
            details={"resource": resource, "field": field, "value": str(value)}
        )


class ValidationException(AppException):
    """验证异常"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
            
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class AuthenticationException(AppException):
    """认证异常"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationException(AppException):
    """授权异常"""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN
        )


class RateLimitException(AppException):
    """速率限制异常"""
    
    def __init__(self, retry_after: Optional[int] = None):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
            
        super().__init__(
            message="Rate limit exceeded",
            code="RATE_LIMIT_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details
        )


class ExternalServiceException(AppException):
    """外部服务异常"""
    
    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"External service error: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details={"service": service}
        )


class FileException(AppException):
    """文件操作异常"""
    
    def __init__(self, message: str, filename: Optional[str] = None):
        details = {}
        if filename:
            details["filename"] = filename
            
        super().__init__(
            message=message,
            code="FILE_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class DatabaseException(AppException):
    """数据库异常"""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        details = {}
        if operation:
            details["operation"] = operation
            
        super().__init__(
            message=f"Database error: {message}",
            code="DATABASE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


# ==================== 异常处理器 ====================

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    处理应用自定义异常
    
    Args:
        request: 请求对象
        exc: 异常对象
    
    Returns:
        JSON响应
    """
    logger.error(
        f"Application error: {exc.message}",
        extra={
            "code": exc.code,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    处理HTTP异常
    
    Args:
        request: 请求对象
        exc: 异常对象
    
    Returns:
        JSON响应
    """
    logger.error(
        f"HTTP error: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    处理请求验证异常
    
    Args:
        request: 请求对象
        exc: 异常对象
    
    Returns:
        JSON响应
    """
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        "Validation error",
        extra={
            "errors": errors,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"errors": errors}
            }
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    处理未预期的异常
    
    Args:
        request: 请求对象
        exc: 异常对象
    
    Returns:
        JSON响应
    """
    logger.error(
        f"Unexpected error: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred"
            }
        }
    )


def get_exception_handlers() -> dict:
    """
    获取所有异常处理器的映射字典
    
    Returns:
        一个将异常类型映射到处理函数的字典
    """
    return {
        AppException: app_exception_handler,
        StarletteHTTPException: http_exception_handler,
        RequestValidationError: validation_exception_handler,
        Exception: generic_exception_handler,
    } 