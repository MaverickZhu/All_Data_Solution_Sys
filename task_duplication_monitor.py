#!/usr/bin/env python3
"""
任务重复执行监控脚本
用于检测和预防任务重复执行问题
"""
import os
import sys
import time
import json
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Any

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.core.config import settings
from backend.services.task_execution_guard import get_task_execution_guard
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("task_duplication_monitor")

class TaskDuplicationMonitor:
    """任务重复执行监控器"""
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url)
        self.task_guard = get_task_execution_guard()
        
    def get_all_task_locks(self) -> Dict[str, Any]:
        """获取所有任务锁"""
        pattern = "task_lock:*"
        locks = {}
        
        for key in self.redis_client.scan_iter(match=pattern):
            key_str = key.decode()
            task_id = self.redis_client.get(key)
            if task_id:
                task_id = task_id.decode()
                
                # 解析任务信息
                lock_part = key_str[len("task_lock:"):]
                if ':' in lock_part:
                    task_type, resource_id = lock_part.split(':', 1)
                    
                    # 获取TTL
                    ttl = self.redis_client.ttl(key)
                    
                    locks[key_str] = {
                        'task_type': task_type,
                        'resource_id': int(resource_id),
                        'task_id': task_id,
                        'ttl_seconds': ttl,
                        'expires_at': datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None
                    }
        
        return locks
    
    def get_all_task_statuses(self) -> Dict[str, Any]:
        """获取所有任务状态"""
        pattern = "task_status:*"
        statuses = {}
        
        for key in self.redis_client.scan_iter(match=pattern):
            key_str = key.decode()
            status_data = self.redis_client.get(key)
            if status_data:
                try:
                    status = json.loads(status_data.decode())
                    statuses[key_str] = status
                except json.JSONDecodeError:
                    logger.error(f"无法解析状态数据: {key_str}")
        
        return statuses
    
    def check_for_duplicates(self) -> List[Dict[str, Any]]:
        """检查重复任务"""
        locks = self.get_all_task_locks()
        statuses = self.get_all_task_statuses()
        
        duplicates = []
        task_resource_map = {}
        
        # 按任务类型和资源ID分组
        for lock_key, lock_info in locks.items():
            task_type = lock_info['task_type']
            resource_id = lock_info['resource_id']
            key = f"{task_type}:{resource_id}"
            
            if key not in task_resource_map:
                task_resource_map[key] = []
            
            task_resource_map[key].append({
                'lock_key': lock_key,
                'lock_info': lock_info,
                'status_key': f"task_status:{key}",
                'status_info': statuses.get(f"task_status:{key}")
            })
        
        # 检查重复
        for key, tasks in task_resource_map.items():
            if len(tasks) > 1:
                duplicates.append({
                    'resource_key': key,
                    'duplicate_count': len(tasks),
                    'tasks': tasks
                })
        
        return duplicates
    
    def get_completed_tasks_still_locked(self) -> List[Dict[str, Any]]:
        """获取已完成但仍有锁的任务"""
        locks = self.get_all_task_locks()
        statuses = self.get_all_task_statuses()
        
        completed_with_locks = []
        
        for lock_key, lock_info in locks.items():
            task_type = lock_info['task_type']
            resource_id = lock_info['resource_id']
            status_key = f"task_status:{task_type}:{resource_id}"
            
            status_info = statuses.get(status_key)
            if status_info and status_info.get('status') in ['completed', 'failed']:
                completed_with_locks.append({
                    'lock_key': lock_key,
                    'lock_info': lock_info,
                    'status_info': status_info,
                    'problem': '任务已完成但锁未释放'
                })
        
        return completed_with_locks
    
    def get_long_running_tasks(self, threshold_hours: int = 2) -> List[Dict[str, Any]]:
        """获取长时间运行的任务"""
        statuses = self.get_all_task_statuses()
        long_running = []
        
        threshold = datetime.now() - timedelta(hours=threshold_hours)
        
        for status_key, status_info in statuses.items():
            if status_info.get('status') == 'running':
                start_time_str = status_info.get('start_time')
                if start_time_str:
                    try:
                        start_time = datetime.fromisoformat(start_time_str)
                        if start_time < threshold:
                            long_running.append({
                                'status_key': status_key,
                                'status_info': status_info,
                                'running_hours': (datetime.now() - start_time).total_seconds() / 3600,
                                'problem': f'任务运行超过{threshold_hours}小时'
                            })
                    except ValueError:
                        logger.error(f"无法解析开始时间: {start_time_str}")
        
        return long_running
    
    def clean_orphaned_locks(self, dry_run: bool = True) -> int:
        """清理孤立的锁"""
        completed_with_locks = self.get_completed_tasks_still_locked()
        cleaned_count = 0
        
        for item in completed_with_locks:
            lock_key = item['lock_key']
            status_info = item['status_info']
            
            # 检查任务是否确实已完成且过了一段时间
            end_time_str = status_info.get('end_time')
            if end_time_str:
                try:
                    end_time = datetime.fromisoformat(end_time_str)
                    if datetime.now() - end_time > timedelta(minutes=5):  # 完成5分钟后清理
                        if not dry_run:
                            self.redis_client.delete(lock_key.encode())
                            logger.info(f"清理孤立锁: {lock_key}")
                        else:
                            logger.info(f"[DRY RUN] 将清理孤立锁: {lock_key}")
                        cleaned_count += 1
                except ValueError:
                    logger.error(f"无法解析结束时间: {end_time_str}")
        
        return cleaned_count
    
    def monitor_report(self):
        """生成监控报告"""
        print("=" * 80)
        print(f"📊 任务重复执行监控报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # 1. 检查重复任务
        duplicates = self.check_for_duplicates()
        print(f"\n🔄 重复任务检查:")
        if duplicates:
            print(f"  ❌ 发现 {len(duplicates)} 个重复任务:")
            for dup in duplicates:
                print(f"    - {dup['resource_key']}: {dup['duplicate_count']} 个重复实例")
                for task in dup['tasks']:
                    print(f"      * 任务ID: {task['lock_info']['task_id']}")
                    print(f"        TTL: {task['lock_info']['ttl_seconds']}s")
        else:
            print("  ✅ 未发现重复任务")
        
        # 2. 检查已完成但仍有锁的任务
        completed_locked = self.get_completed_tasks_still_locked()
        print(f"\n🔒 孤立锁检查:")
        if completed_locked:
            print(f"  ⚠️ 发现 {len(completed_locked)} 个孤立锁:")
            for item in completed_locked:
                status = item['status_info']
                print(f"    - {item['lock_key']}")
                print(f"      状态: {status.get('status')}")
                print(f"      结束时间: {status.get('end_time', 'N/A')}")
        else:
            print("  ✅ 未发现孤立锁")
        
        # 3. 检查长时间运行任务
        long_running = self.get_long_running_tasks()
        print(f"\n⏰ 长时间运行任务检查:")
        if long_running:
            print(f"  ⚠️ 发现 {len(long_running)} 个长时间运行任务:")
            for item in long_running:
                print(f"    - {item['status_key']}")
                print(f"      运行时间: {item['running_hours']:.1f}小时")
                print(f"      任务ID: {item['status_info'].get('task_id')}")
        else:
            print("  ✅ 未发现异常长时间运行任务")
        
        # 4. 清理建议
        print(f"\n🧹 清理建议:")
        if completed_locked:
            print(f"  建议清理 {len(completed_locked)} 个孤立锁")
            print("  执行命令: python task_duplication_monitor.py --clean")
        else:
            print("  ✅ 无需清理")
        
        print("\n" + "=" * 80)

def main():
    monitor = TaskDuplicationMonitor()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--clean':
            # 清理模式
            cleaned = monitor.clean_orphaned_locks(dry_run=False)
            print(f"✅ 已清理 {cleaned} 个孤立锁")
        elif sys.argv[1] == '--dry-run':
            # 干运行模式
            cleaned = monitor.clean_orphaned_locks(dry_run=True)
            print(f"📋 将清理 {cleaned} 个孤立锁")
        elif sys.argv[1] == '--watch':
            # 监控模式
            print("🔍 开始持续监控任务重复执行...")
            try:
                while True:
                    monitor.monitor_report()
                    print(f"\n⏰ 下次检查时间: {(datetime.now() + timedelta(minutes=5)).strftime('%H:%M:%S')}")
                    time.sleep(300)  # 5分钟检查一次
            except KeyboardInterrupt:
                print("\n⏹️ 监控停止")
        else:
            print("使用方法:")
            print("  python task_duplication_monitor.py           # 生成监控报告")
            print("  python task_duplication_monitor.py --clean   # 清理孤立锁")
            print("  python task_duplication_monitor.py --dry-run # 预览清理操作")
            print("  python task_duplication_monitor.py --watch   # 持续监控")
    else:
        # 默认生成报告
        monitor.monitor_report()

if __name__ == "__main__":
    main() 