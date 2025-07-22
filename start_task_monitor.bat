@echo off
echo ==========================================================
echo Celery任务监控器 - 僵尸任务检测和清理
echo ==========================================================
echo.

echo 选择操作模式:
echo 1. 检查卡住的任务
echo 2. 清理僵尸任务 (安全模式)
echo 3. 强制清理僵尸任务
echo 4. 启动持续监控模式
echo 5. 退出
echo.

set /p choice=请输入选择 (1-5): 

if "%choice%"=="1" (
    echo.
    echo 正在检查卡住的任务...
    python task_monitor.py --check-stuck
    goto end
)

if "%choice%"=="2" (
    echo.
    echo 安全模式清理 - 仅显示将要清理的任务，不实际执行
    python task_monitor.py --clean-zombie --dry-run
    goto end
)

if "%choice%"=="3" (
    echo.
    echo ⚠️ 警告：将强制清理僵尸任务！
    set /p confirm=确定要继续吗? (y/N): 
    if /i "%confirm%"=="y" (
        echo 正在清理僵尸任务...
        python task_monitor.py --clean-zombie
    ) else (
        echo 取消操作
    )
    goto end
)

if "%choice%"=="4" (
    echo.
    echo 启动持续监控模式（每5分钟检查一次）
    echo 按 Ctrl+C 停止监控
    echo.
    python task_monitor.py --monitor --interval 300
    goto end
)

if "%choice%"=="5" (
    echo 退出
    goto end
)

echo 无效选择，请重新运行脚本
:end
echo.
echo ==========================================================
echo 操作完成！
echo ==========================================================
pause 