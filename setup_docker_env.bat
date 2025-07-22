@echo off
echo ==========================================================
echo Docker环境变量配置工具
echo ==========================================================
echo.

echo 正在检查Docker安装状态...

REM 检查Docker Desktop是否安装
if exist "C:\Program Files\Docker\Docker\resources\bin\docker.exe" (
    echo ✅ 找到Docker Desktop安装路径
) else (
    echo ❌ 未找到Docker Desktop，请先安装Docker Desktop
    pause
    exit /b 1
)

echo.
echo 正在配置Docker命令行环境变量...

REM 将Docker路径添加到用户PATH环境变量
setx PATH "%PATH%;C:\Program Files\Docker\Docker\resources\bin"

if %errorlevel% equ 0 (
    echo ✅ Docker路径已成功添加到用户环境变量
    echo.
    echo 📝 重要说明：
    echo 1. 需要重新打开命令行窗口才能生效
    echo 2. 新的PowerShell/CMD窗口中docker命令将全局可用
    echo 3. 建议重启系统以确保所有程序都能使用新的环境变量
    echo.
    echo 🔧 验证方法：
    echo 1. 关闭当前命令行窗口
    echo 2. 重新打开PowerShell或CMD
    echo 3. 运行: docker --version
    echo 4. 如果显示版本信息，说明配置成功
) else (
    echo ❌ 配置失败，请以管理员身份运行此脚本
)

echo.
echo ==========================================================
echo 配置完成！请重新打开命令行窗口测试
echo ==========================================================
pause 