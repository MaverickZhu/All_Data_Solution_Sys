@echo off
echo =====================================================
echo 查找系统中的Docker项目
echo =====================================================

echo.
echo 正在搜索docker-compose.yml文件...
echo.

:: 搜索C盘用户目录下的docker-compose.yml文件
forfiles /p "C:\Users" /s /m docker-compose.yml /c "cmd /c echo 找到项目: @path"

echo.
echo 正在搜索D盘的docker-compose.yml文件...
echo.

:: 如果D盘存在，搜索D盘
if exist D:\ (
    forfiles /p "D:\" /s /m docker-compose.yml /c "cmd /c echo 找到项目: @path" 2>nul
) else (
    echo D盘不存在，跳过...
)

echo.
echo 正在搜索桌面的docker-compose.yml文件...
echo.

forfiles /p "%USERPROFILE%\Desktop" /s /m docker-compose.yml /c "cmd /c echo 找到项目: @path" 2>nul

echo.
echo =====================================================
echo 搜索完成！请手动进入每个项目目录恢复。
echo =====================================================
pause 