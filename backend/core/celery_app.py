import os
import sys
from celery import Celery
import multiprocessing

# 设置multiprocessing启动方式为spawn以支持CUDA
if hasattr(multiprocessing, 'set_start_method'):
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        # 如果已经设置过，忽略错误
        pass

# 添加CUDA环境变量
os.environ.setdefault('CUDA_LAUNCH_BLOCKING', '1')

from backend.core.config import settings

# 创建 Celery 应用
celery_app = Celery(
    "tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["backend.processing.tasks"],  # Points to the module where tasks are defined
)

# 配置
celery_app.conf.update(
    task_track_started=True,
    # 添加worker配置以支持CUDA
    worker_pool='solo',  # 使用solo pool避免multiprocessing问题
    worker_concurrency=1,  # 单进程处理
    result_expires=3600,
    timezone='UTC',
    enable_utc=True,
) 