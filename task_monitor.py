#!/usr/bin/env python3
"""
Celery任务监控工具 - 检测和处理僵尸任务
解决Worker重启后任务重新执行的问题

用法:
python task_monitor.py --check-stuck    # 检查卡住的任务
python task_monitor.py --clean-zombie   # 清理僵尸任务  
python task_monitor.py --monitor        # 持续监控模式
"""

import argparse
import time
import sys
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import redis
import json
import subprocess

# 添加项目路径
sys.path.insert(0, os.path.abspath('.'))

from backend.core.config import settings
from backend.core.celery_app import celery_app, check_stuck_tasks
from backend.core.database import get_sync_db
from backend.models.video_analysis import VideoAnalysis, VideoAnalysisStatus
from backend.models.data_source import DataSource, ProfileStatusEnum
from celery import Celery
from celery.result import AsyncResult
import sqlalchemy
from sqlalchemy.exc import OperationalError

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('task_monitor')

class TaskMonitor:
    """Celery任务监控器"""
    
    def __init__(self):
        self.celery_app = celery_app
        self.redis_client = None
        self._init_redis()
    
    def _init_redis(self):
        """初始化Redis连接"""
        try:
            # 从Celery配置中解析Redis URL
            redis_url = settings.celery_result_backend
            if redis_url.startswith('redis://'):
                # 解析格式: redis://:password@host:port/db
                parts = redis_url.replace('redis://', '').split('@')
                if len(parts) == 2:
                    auth_part, host_port_db = parts
                    password = auth_part.lstrip(':') if auth_part.startswith(':') else None
                    host_port, db = host_port_db.split('/')
                    host, port = host_port.split(':')
                    
                    self.redis_client = redis.Redis(
                        host=host, 
                        port=int(port), 
                        db=int(db), 
                        password=password,
                        decode_responses=True
                    )
                else:
                    # 简单格式解析
                    self.redis_client = redis.from_url(redis_url, decode_responses=True)
                    
            logger.info("Redis连接初始化成功")
            
        except Exception as e:
            logger.error(f"Redis连接初始化失败: {e}")
            self.redis_client = None
    
    def get_active_tasks(self) -> List[Dict]:
        """获取所有活跃任务"""
        active_tasks = []
        
        try:
            # 获取Celery监控信息
            inspect = self.celery_app.control.inspect()
            
            # 获取活跃任务
            active = inspect.active()
            if active:
                for worker, tasks in active.items():
                    for task in tasks:
                        active_tasks.append({
                            'task_id': task['id'],
                            'name': task['name'],
                            'worker': worker,
                            'args': task.get('args', []),
                            'kwargs': task.get('kwargs', {}),
                            'time_start': task.get('time_start'),
                            'status': 'ACTIVE'
                        })
            
            # 获取预留任务
            reserved = inspect.reserved()
            if reserved:
                for worker, tasks in reserved.items():
                    for task in tasks:
                        active_tasks.append({
                            'task_id': task['id'],
                            'name': task['name'],
                            'worker': worker,
                            'args': task.get('args', []),
                            'kwargs': task.get('kwargs', {}),
                            'time_start': None,
                            'status': 'RESERVED'
                        })
            
            logger.info(f"发现 {len(active_tasks)} 个活跃任务")
            return active_tasks
            
        except Exception as e:
            logger.error(f"获取活跃任务失败: {e}")
            return []
    
    def _find_docker_executable(self) -> str:
        """查找Docker可执行文件"""
        docker_paths = [
            "docker",  # 先尝试PATH中的docker
            "C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker.exe",  # Docker Desktop路径
            os.path.expandvars("%ProgramFiles%\\Docker\\Docker\\resources\\bin\\docker.exe")  # 动态路径
        ]
        
        for path in docker_paths:
            try:
                test_result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=5)
                if test_result.returncode == 0:
                    logger.debug(f"找到Docker可执行文件: {path}")
                    return path
            except Exception:
                continue
        
        logger.error("无法找到Docker可执行文件")
        return None
    
    def get_stuck_tasks_from_heartbeat(self) -> List[Dict]:
        """从心跳机制检查卡住的任务"""
        try:
            stuck_tasks = check_stuck_tasks()
            logger.info(f"从心跳检查发现 {len(stuck_tasks)} 个可能卡住的任务")
            return stuck_tasks
        except Exception as e:
            logger.error(f"心跳检查失败: {e}")
            return []
    
    def get_database_stuck_tasks(self) -> List[Dict]:
        """从数据库检查长时间运行的任务"""
        stuck_tasks = []
        db = next(get_sync_db())
        
        try:
            # 检查视频分析任务
            cutoff_time = datetime.utcnow() - timedelta(hours=2)  # 2小时前
            
            video_analyses = db.query(VideoAnalysis).filter(
                VideoAnalysis.status == VideoAnalysisStatus.IN_PROGRESS,
                VideoAnalysis.updated_at < cutoff_time
            ).all()
            
            for analysis in video_analyses:
                stuck_tasks.append({
                    'type': 'video_analysis',
                    'id': analysis.id,
                    'data_source_id': analysis.data_source_id,
                    'status': analysis.status.value,
                    'updated_at': analysis.updated_at,
                    'current_phase': analysis.current_phase,
                    'progress': analysis.progress_percentage
                })
            
            # 检查profiling任务
            data_sources = db.query(DataSource).filter(
                DataSource.profile_status == ProfileStatusEnum.in_progress,
                DataSource.updated_at < cutoff_time
            ).all()
            
            for ds in data_sources:
                stuck_tasks.append({
                    'type': 'profiling',
                    'id': ds.id,
                    'task_id': ds.task_id,
                    'status': ds.profile_status.value,
                    'updated_at': ds.updated_at,
                    'file_path': ds.file_path
                })
            
            logger.info(f"从数据库发现 {len(stuck_tasks)} 个长时间运行的任务")
            return stuck_tasks
            
        except Exception as e:
            logger.error(f"数据库检查失败: {e}")
            return []
        finally:
            db.close()
    
    def revoke_task(self, task_id: str, terminate: bool = False) -> bool:
        """撤销任务"""
        try:
            self.celery_app.control.revoke(task_id, terminate=terminate)
            logger.info(f"任务已撤销: {task_id} (terminate: {terminate})")
            return True
        except Exception as e:
            logger.error(f"撤销任务失败 {task_id}: {e}")
            return False
    
    def cleanup_stuck_database_tasks(self, dry_run: bool = True) -> int:
        """清理数据库中卡住的任务状态"""
        cleaned_count = 0
        db = next(get_sync_db())
        
        try:
            # 清理视频分析任务
            cutoff_time = datetime.utcnow() - timedelta(hours=3)  # 3小时前
            
            if dry_run:
                # 仅查询，不更新
                video_count = db.query(VideoAnalysis).filter(
                    VideoAnalysis.status == VideoAnalysisStatus.IN_PROGRESS,
                    VideoAnalysis.updated_at < cutoff_time
                ).count()
                
                profiling_count = db.query(DataSource).filter(
                    DataSource.profile_status == ProfileStatusEnum.in_progress,
                    DataSource.updated_at < cutoff_time
                ).count()
                
                logger.info(f"DRY RUN: 将清理 {video_count} 个视频分析任务, {profiling_count} 个profiling任务")
                return video_count + profiling_count
            
            else:
                # 实际更新
                video_analyses = db.query(VideoAnalysis).filter(
                    VideoAnalysis.status == VideoAnalysisStatus.IN_PROGRESS,
                    VideoAnalysis.updated_at < cutoff_time
                ).all()
                
                for analysis in video_analyses:
                    analysis.status = VideoAnalysisStatus.FAILED
                    analysis.error_message = "任务超时被监控器清理"
                    analysis.current_phase = "超时清理"
                    cleaned_count += 1
                
                data_sources = db.query(DataSource).filter(
                    DataSource.profile_status == ProfileStatusEnum.in_progress,
                    DataSource.updated_at < cutoff_time
                ).all()
                
                for ds in data_sources:
                    ds.profile_status = ProfileStatusEnum.failed
                    cleaned_count += 1
                
                db.commit()
                logger.info(f"已清理 {cleaned_count} 个卡住的任务")
                
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理数据库任务失败: {e}")
            db.rollback()
            return 0
        finally:
            db.close()
    
    def check_celery_connection(self) -> bool:
        """检查Celery连接状态"""
        try:
            # 检查broker连接
            stats = self.celery_app.control.inspect().stats()
            if stats:
                logger.info(f"Celery连接正常，发现 {len(stats)} 个worker")
                return True
            else:
                logger.warning("Celery连接异常，未发现worker")
                return False
        except Exception as e:
            logger.error(f"Celery连接检查失败: {e}")
            return False
    
    def generate_report(self) -> Dict[str, Any]:
        """生成监控报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'celery_connection': self.check_celery_connection(),
            'active_tasks': self.get_active_tasks(),
            'stuck_heartbeat_tasks': self.get_stuck_tasks_from_heartbeat(),
            'stuck_database_tasks': self.get_database_stuck_tasks(),
        }
        
        # 统计信息
        report['statistics'] = {
            'total_active_tasks': len(report['active_tasks']),
            'stuck_heartbeat_count': len(report['stuck_heartbeat_tasks']),
            'stuck_database_count': len(report['stuck_database_tasks']),
            'video_analysis_stuck': len([t for t in report['stuck_database_tasks'] if t['type'] == 'video_analysis']),
            'profiling_stuck': len([t for t in report['stuck_database_tasks'] if t['type'] == 'profiling'])
        }
        
        return report
    
    def monitor_continuous(self, interval: int = 300):
        """持续监控模式"""
        logger.info(f"开始持续监控，检查间隔: {interval}秒")
        
        while True:
            try:
                logger.info("=" * 50)
                logger.info("执行任务健康检查...")
                
                report = self.generate_report()
                
                # 输出简要统计
                stats = report['statistics']
                logger.info(f"📊 任务统计: 活跃{stats['total_active_tasks']}, "
                           f"心跳卡住{stats['stuck_heartbeat_count']}, "
                           f"数据库卡住{stats['stuck_database_count']}")
                
                # 如果发现问题，输出详细信息
                if stats['stuck_heartbeat_count'] > 0:
                    logger.warning("发现心跳卡住的任务:")
                    for task in report['stuck_heartbeat_tasks']:
                        logger.warning(f"  - {task['task_name']} ({task['task_id'][:8]}...): "
                                     f"卡住{task['stuck_duration']:.0f}秒")
                
                if stats['stuck_database_count'] > 0:
                    logger.warning("发现数据库卡住的任务:")
                    for task in report['stuck_database_tasks']:
                        logger.warning(f"  - {task['type']} (ID: {task['id']}): "
                                     f"状态{task['status']}, 更新于{task['updated_at']}")
                
                # 自动清理过长的卡住任务
                if stats['stuck_database_count'] > 0:
                    logger.info("自动清理长时间卡住的任务...")
                    cleaned = self.cleanup_stuck_database_tasks(dry_run=False)
                    if cleaned > 0:
                        logger.info(f"✅ 已清理 {cleaned} 个卡住的任务")
                
                logger.info(f"下次检查时间: {(datetime.now() + timedelta(seconds=interval)).strftime('%H:%M:%S')}")
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("监控停止")
                break
            except Exception as e:
                logger.error(f"监控过程出错: {e}")
                time.sleep(60)  # 出错后等待1分钟再继续

def main():
    parser = argparse.ArgumentParser(description='Celery任务监控工具')
    parser.add_argument('--check-stuck', action='store_true', help='检查卡住的任务')
    parser.add_argument('--clean-zombie', action='store_true', help='清理僵尸任务')
    parser.add_argument('--monitor', action='store_true', help='持续监控模式')
    parser.add_argument('--interval', type=int, default=300, help='监控间隔（秒）')
    parser.add_argument('--dry-run', action='store_true', help='仅查看，不执行清理')
    
    args = parser.parse_args()
    
    monitor = TaskMonitor()
    
    if args.check_stuck:
        logger.info("🔍 检查卡住的任务...")
        report = monitor.generate_report()
        
        print("\n" + "="*60)
        print("📊 任务监控报告")
        print("="*60)
        print(f"时间: {report['timestamp']}")
        print(f"Celery连接: {'✅ 正常' if report['celery_connection'] else '❌ 异常'}")
        
        stats = report['statistics']
        print(f"\n📈 任务统计:")
        print(f"  活跃任务: {stats['total_active_tasks']}")
        print(f"  心跳卡住: {stats['stuck_heartbeat_count']}")
        print(f"  数据库卡住: {stats['stuck_database_count']}")
        print(f"    - 视频分析: {stats['video_analysis_stuck']}")
        print(f"    - 数据分析: {stats['profiling_stuck']}")
        
        if report['stuck_heartbeat_tasks']:
            print(f"\n⚠️ 心跳卡住的任务:")
            for task in report['stuck_heartbeat_tasks']:
                print(f"  - {task['task_name']} (ID: {task['task_id'][:8]}...)")
                print(f"    卡住时长: {task['stuck_duration']:.1f}秒")
                print(f"    总运行时长: {task['total_duration']:.1f}秒")
        
        if report['stuck_database_tasks']:
            print(f"\n⚠️ 数据库卡住的任务:")
            for task in report['stuck_database_tasks']:
                print(f"  - {task['type']} (ID: {task['id']})")
                print(f"    状态: {task['status']}")
                print(f"    最后更新: {task['updated_at']}")
                if task['type'] == 'video_analysis':
                    print(f"    当前阶段: {task.get('current_phase', 'N/A')}")
                    print(f"    进度: {task.get('progress', 0)}%")
    
    elif args.clean_zombie:
        logger.info("🧹 清理僵尸任务...")
        
        # 撤销心跳卡住的任务
        stuck_heartbeat = monitor.get_stuck_tasks_from_heartbeat()
        for task in stuck_heartbeat:
            task_id = task['task_id']
            logger.info(f"撤销卡住任务: {task_id}")
            if not args.dry_run:
                monitor.revoke_task(task_id, terminate=True)
        
        # 清理数据库中的卡住任务
        cleaned = monitor.cleanup_stuck_database_tasks(dry_run=args.dry_run)
        
        if args.dry_run:
            print(f"DRY RUN: 将清理 {cleaned} 个僵尸任务")
        else:
            print(f"✅ 已清理 {cleaned} 个僵尸任务")
    
    elif args.monitor:
        monitor.monitor_continuous(args.interval)
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main() 