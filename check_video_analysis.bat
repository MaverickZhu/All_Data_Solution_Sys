@echo off
echo ==========================================================
echo 视频深度分析系统健康检查
echo ==========================================================
echo.

REM 运行健康检查（工具会自动查找Docker）
echo 正在检查视频分析系统状态...
echo.
python debug_video_analysis.py --full-check

echo.
echo ==========================================================
echo 检查完成！
echo.
echo 如果显示"GPU状态: 容器内GPU可用"，说明视频分析将使用GPU加速
echo 如果健康状态显示100%%，说明系统完全正常
echo.
echo 💡 如果遇到Docker相关错误：
echo 1. 确保Docker Desktop正在运行
echo 2. 运行 configure_docker_global.ps1 配置全局环境（需管理员权限）
echo 3. 或重启系统让环境变量生效
echo ==========================================================
pause 