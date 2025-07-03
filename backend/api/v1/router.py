"""
API v1 主路由器
汇总所有v1版本的API端点
"""
from fastapi import APIRouter

# 导入各个模块的路由器
from backend.api.v1.endpoints import auth, users, projects, processing

# 创建v1 API路由器
api_router = APIRouter()

# 包含各个模块的路由
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(processing.router, prefix="/processing", tags=["Processing"])
# api_router.include_router(analysis.router, prefix="/analysis", tags=["分析"])
# api_router.include_router(search.router, prefix="/search", tags=["搜索"])

# 临时测试路由
@api_router.get("/test")
async def test_endpoint():
    """测试端点"""
    return {"message": "API v1 is working!"} 