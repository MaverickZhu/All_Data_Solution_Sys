#!/usr/bin/env python3
"""
视频分析任务调试工具 - 弹性分析版本
专注于解决LLM调用阻塞问题，而非简单的时间限制
"""
import os
import sys
import time
import logging
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("video_analysis_debug")

def check_ollama_service():
    """检查Ollama服务状态和模型可用性"""
    logger.info("=== 检查Ollama服务状态 ===")
    
    try:
        import requests
        
        # 检查服务基本状态
        try:
            response = requests.get("http://host.docker.internal:11435/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                logger.info(f"✅ Ollama服务正常，可用模型数: {len(models)}")
                
                # 检查具体模型
                qwen_models = [m for m in models if 'qwen' in m['name'].lower()]
                if qwen_models:
                    for model in qwen_models:
                        name = model.get('name', 'unknown')
                        size = model.get('size', 0) // (1024**3)  # GB
                        logger.info(f"  📹 {name} ({size}GB)")
                else:
                    logger.warning("⚠️ 未发现Qwen视觉模型")
                
                return len(models) > 0
            else:
                logger.error(f"❌ Ollama服务响应异常: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("❌ Ollama服务连接超时")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("❌ 无法连接到Ollama服务")
            return False
            
    except Exception as e:
        logger.error(f"❌ 检查Ollama服务失败: {e}")
        return False

def test_llm_connection():
    """测试LLM连接稳定性"""
    logger.info("=== 测试LLM连接稳定性 ===")
    
    try:
        from backend.services.video_vision_service import VideoVisionService
        
        # 创建服务实例
        vision_service = VideoVisionService()
        
        # 测试健康检查
        async def test_health_check():
            health_ok = await vision_service._check_ollama_health()
            if health_ok:
                logger.info("✅ Ollama健康检查通过")
            else:
                logger.error("❌ Ollama健康检查失败")
            return health_ok
        
        # 运行测试
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        health_result = loop.run_until_complete(test_health_check())
        
        return health_result
        
    except Exception as e:
        logger.error(f"❌ LLM连接测试失败: {e}")
        return False

def check_gpu_status():
    """检查GPU状态 - 区分主机和容器环境"""
    logger.info("=== 检查GPU状态 ===")
    
    gpu_status = {
        "host_gpu": False,
        "container_gpu": False,
        "nvidia_smi": False
    }
    
    # 1. 检查NVIDIA驱动和硬件
    try:
        import subprocess
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            gpu_status["nvidia_smi"] = True
            # 提取GPU信息
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if 'NVIDIA GeForce' in line or 'RTX' in line:
                    gpu_info = line.strip()
                    logger.info(f"✅ 检测到GPU硬件: {gpu_info}")
                    break
        else:
            logger.error("❌ nvidia-smi 执行失败")
    except Exception as e:
        logger.error(f"❌ nvidia-smi 检查失败: {e}")
    
    # 2. 检查主机Python环境的GPU支持
    try:
        import torch
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory // 1024**3
            logger.info(f"✅ 主机GPU可用: {gpu_name} ({gpu_memory}GB)")
            gpu_status["host_gpu"] = True
        else:
            logger.warning("⚠️ 主机GPU不可用（可能缺少CUDA版本PyTorch）")
    except ImportError:
        logger.warning("⚠️ 主机环境缺少PyTorch")
    except Exception as e:
        logger.error(f"❌ 主机GPU检查失败: {e}")
    
    # 3. 检查容器内的GPU支持（这是关键的）
    try:
        import subprocess
        import os
        
        # 尝试找到Docker可执行文件
        docker_paths = [
            "docker",  # 先尝试PATH中的docker
            "C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker.exe",  # Docker Desktop路径
            os.path.expandvars("%ProgramFiles%\\Docker\\Docker\\resources\\bin\\docker.exe")  # 动态路径
        ]
        
        docker_executable = None
        for path in docker_paths:
            try:
                test_result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=5)
                if test_result.returncode == 0:
                    docker_executable = path
                    logger.debug(f"找到Docker可执行文件: {path}")
                    break
            except Exception:
                continue
        
        if not docker_executable:
            logger.error("❌ 无法找到Docker可执行文件")
            logger.error("请确保Docker Desktop已安装并运行")
            return gpu_status
        
        cmd = [
            docker_executable, 'exec', 'all_data_solution_sys-celery-worker-1', 
            'python', '-c', 
            'import torch; print(f"CUDA:{torch.cuda.is_available()};COUNT:{torch.cuda.device_count() if torch.cuda.is_available() else 0};NAME:{torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}")'
        ]
        
        logger.debug(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            output = result.stdout.strip()
            logger.debug(f"容器输出: {output}")
            if "CUDA:True" in output:
                gpu_status["container_gpu"] = True
                # 解析输出
                parts = output.split(';')
                cuda_available = "True" in parts[0]
                gpu_count = parts[1].split(':')[1] if len(parts) > 1 else "0"
                gpu_name = parts[2].split(':')[1] if len(parts) > 2 else "Unknown"
                logger.info(f"✅ 容器GPU可用: {gpu_name} (数量: {gpu_count})")
            else:
                logger.error("❌ 容器内GPU不可用")
                logger.error(f"容器输出: {output}")
        else:
            logger.error(f"❌ 容器GPU检查失败: {result.stderr}")
    except Exception as e:
        logger.error(f"❌ 容器GPU检查异常: {e}")
    
    # 生成GPU状态报告
    if gpu_status["container_gpu"]:
        logger.info("🎯 GPU状态: 容器内GPU可用，视频分析将使用GPU加速")
    elif gpu_status["nvidia_smi"]:
        logger.warning("⚠️ GPU状态: 硬件正常但容器内不可用，需要检查Docker GPU配置")
    else:
        logger.error("❌ GPU状态: GPU硬件或驱动异常")
    
    return gpu_status

def check_video_analysis_health():
    """检查视频分析服务整体健康状态"""
    logger.info("=== 检查视频分析服务健康状态 ===")
    
    health_results = {
        "ollama_service": False,
        "llm_connection": False,
        "gpu_available": False,
        "dependencies": False
    }
    
    # 1. 检查Ollama服务
    health_results["ollama_service"] = check_ollama_service()
    
    # 2. 测试LLM连接
    health_results["llm_connection"] = test_llm_connection()
    
    # 3. 检查GPU状态（修改为使用新的检查方法）
    gpu_status = check_gpu_status()
    health_results["gpu_available"] = gpu_status["container_gpu"]  # 使用容器GPU状态
    
    # 4. 检查关键依赖
    try:
        import aiohttp
        from langchain_ollama import ChatOllama
        from PIL import Image
        logger.info("✅ 关键依赖库可用")
        health_results["dependencies"] = True
    except ImportError as e:
        logger.error(f"❌ 缺少关键依赖: {e}")
    
    # 生成健康报告
    healthy_count = sum(health_results.values())
    total_checks = len(health_results)
    health_score = healthy_count / total_checks * 100
    
    logger.info(f"\n📊 健康状态报告: {healthy_count}/{total_checks} 检查通过 ({health_score:.1f}%)")
    
    if health_score >= 75:
        logger.info("🟢 系统状态良好")
    elif health_score >= 50:
        logger.warning("🟡 系统状态一般，建议检查")
    else:
        logger.error("🔴 系统状态异常，需要修复")
    
    return health_results

def analyze_stuck_patterns():
    """分析任务卡住的模式和规律"""
    logger.info("=== 分析任务卡住模式 ===")
    
    try:
        from backend.core.database import get_sync_db
        from backend.models.video_analysis import VideoAnalysis, VideoAnalysisStatus
        from datetime import datetime, timedelta
        
        db = next(get_sync_db())
        
        # 查找最近24小时的失败任务
        time_threshold = datetime.now() - timedelta(hours=24)
        
        failed_analyses = db.query(VideoAnalysis).filter(
            VideoAnalysis.status == VideoAnalysisStatus.FAILED,
            VideoAnalysis.updated_at > time_threshold
        ).all()
        
        stuck_analyses = db.query(VideoAnalysis).filter(
            VideoAnalysis.status == VideoAnalysisStatus.IN_PROGRESS,
            VideoAnalysis.updated_at < datetime.now() - timedelta(minutes=10)
        ).all()
        
        logger.info(f"最近24小时失败任务: {len(failed_analyses)}")
        logger.info(f"当前卡住任务: {len(stuck_analyses)}")
        
        # 分析失败模式
        error_patterns = {}
        for analysis in failed_analyses:
            error_msg = analysis.error_message or "未知错误"
            # 提取错误关键词
            if "超时" in error_msg or "timeout" in error_msg.lower():
                error_patterns["timeout"] = error_patterns.get("timeout", 0) + 1
            elif "连接" in error_msg or "connection" in error_msg.lower():
                error_patterns["connection"] = error_patterns.get("connection", 0) + 1
            elif "内存" in error_msg or "memory" in error_msg.lower():
                error_patterns["memory"] = error_patterns.get("memory", 0) + 1
            else:
                error_patterns["other"] = error_patterns.get("other", 0) + 1
        
        if error_patterns:
            logger.info("错误模式分析:")
            for pattern, count in error_patterns.items():
                logger.info(f"  {pattern}: {count}次")
        
        # 分析卡住任务的阶段
        stuck_phases = {}
        for analysis in stuck_analyses:
            phase = analysis.current_phase or "unknown"
            stuck_phases[phase] = stuck_phases.get(phase, 0) + 1
        
        if stuck_phases:
            logger.info("卡住阶段分析:")
            for phase, count in stuck_phases.items():
                logger.info(f"  {phase}: {count}个任务")
        
        db.close()
        return {"failed_patterns": error_patterns, "stuck_phases": stuck_phases}
        
    except Exception as e:
        logger.error(f"分析卡住模式失败: {e}")
        return {}

def suggest_solutions(health_results: dict, patterns: dict):
    """基于健康状态和错误模式提供解决建议"""
    logger.info("=== 解决方案建议 ===")
    
    suggestions = []
    
    # 基于健康检查结果
    if not health_results.get("ollama_service"):
        suggestions.append("🔧 重启Ollama服务: docker restart ollama")
    
    if not health_results.get("llm_connection"):
        suggestions.append("🔧 检查网络连接和防火墙设置")
    
    if not health_results.get("gpu_available"):
        suggestions.append("🔧 检查GPU驱动和CUDA环境")
    
    # 基于错误模式
    error_patterns = patterns.get("failed_patterns", {})
    if error_patterns.get("timeout", 0) > 0:
        suggestions.append("⚡ 考虑减少帧采样数量或降低分析复杂度")
    
    if error_patterns.get("connection", 0) > 0:
        suggestions.append("🌐 检查Ollama服务稳定性和网络配置")
    
    if error_patterns.get("memory", 0) > 0:
        suggestions.append("💾 增加系统内存或优化模型参数")
    
    # 基于卡住阶段
    stuck_phases = patterns.get("stuck_phases", {})
    if "视觉分析" in stuck_phases:
        suggestions.append("👁️ 检查视觉分析模型加载状态")
    
    if not suggestions:
        suggestions.append("✅ 系统状态良好，无需特殊处理")
    
    for i, suggestion in enumerate(suggestions, 1):
        logger.info(f"{i}. {suggestion}")
    
    return suggestions

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='视频分析弹性调试工具')
    parser.add_argument('--check-health', action='store_true', help='检查系统健康状态')
    parser.add_argument('--test-connection', action='store_true', help='测试LLM连接')
    parser.add_argument('--analyze-patterns', action='store_true', help='分析错误模式')
    parser.add_argument('--full-check', action='store_true', help='完整健康检查和建议')
    
    args = parser.parse_args()
    
    if args.check_health:
        health_results = check_video_analysis_health()
    elif args.test_connection:
        test_llm_connection()
    elif args.analyze_patterns:
        patterns = analyze_stuck_patterns()
    elif args.full_check:
        health_results = check_video_analysis_health()
        patterns = analyze_stuck_patterns()
        suggest_solutions(health_results, patterns)
    else:
        # 默认执行完整检查
        logger.info("执行完整健康检查和分析...")
        health_results = check_video_analysis_health()
        patterns = analyze_stuck_patterns()
        suggest_solutions(health_results, patterns)

if __name__ == "__main__":
    main() 