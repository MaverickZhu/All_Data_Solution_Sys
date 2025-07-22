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
    
    # 🔥 添加消息重投递控制配置
    task_acks_late=True,  # 任务完成后才确认消息，避免处理中断导致消息丢失
    worker_prefetch_multiplier=1,  # 限制预取消息数量，避免大量重复任务
    task_reject_on_worker_lost=False,  # worker丢失时不重新投递任务
    
    # 🔥 增强连接稳定性配置
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,  # 增加重试次数
    broker_failover_strategy='round-robin',
    broker_heartbeat=30,  # 心跳检测
    broker_pool_limit=10,  # 连接池大小
    
    # 🔥 解决ConnectionResetError的关键配置
    worker_cancel_long_running_tasks_on_connection_loss=False,  # 连接丢失时不取消长任务
    broker_transport_options={
        'max_retries': 5,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 1,
        'retry_on_timeout': True,
        'confirm_publish': True,  # 确认消息发布
    },
    
    # 任务超时配置
    task_soft_time_limit=1800,  # 30分钟软超时
    task_time_limit=2400,  # 40分钟硬超时
    
    # 避免重复任务的关键配置
    task_ignore_result=False,  # 保留任务结果用于去重检查
    result_persistent=True,  # 持久化结果
) 