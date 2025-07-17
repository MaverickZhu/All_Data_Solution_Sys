@echo off
echo =====================================================
echo 恢复被删除的Docker容器
echo =====================================================

echo.
echo 正在恢复用户根目录项目容器...
cd "C:\Users\Zz-20240101"
if exist docker-compose.yml (
    echo 找到 docker-compose.yml，正在创建容器...
    docker-compose create
    echo 用户根目录项目容器创建完成
) else (
    echo 未找到 docker-compose.yml
)

echo.
echo 正在恢复 PG_Anlize_Sys 项目容器...
cd "C:\Users\Zz-20240101\Desktop\PG_Anlize_Sys"
if exist docker-compose.yml (
    echo 找到 docker-compose.yml，正在创建容器...
    docker-compose create
    echo PG_Anlize_Sys 项目容器创建完成
) else (
    echo 未找到 docker-compose.yml
)

echo.
echo 正在恢复 RAGFlow 项目容器...
cd "C:\Users\Zz-20240101\ragflow\ragflow\docker"
if exist docker-compose.yml (
    echo 找到 docker-compose.yml，正在创建容器...
    docker-compose create
    echo RAGFlow 项目容器创建完成
) else (
    echo 未找到 docker-compose.yml
)

echo.
echo 正在检查其他可能的项目位置...

:: 检查 dify 项目
cd "C:\Users\Zz-20240101\dify\docker"
if exist docker-compose.yml (
    echo 找到 Dify 项目，正在创建容器...
    docker-compose create
    echo Dify 项目容器创建完成
) else (
    echo 未找到 Dify 项目
)

:: 检查 n8n 或其他项目
if exist "C:\Users\Zz-20240101\n8n\docker-compose.yml" (
    echo 找到 n8n 项目，正在创建容器...
    cd "C:\Users\Zz-20240101\n8n"
    docker-compose create
    echo n8n 项目容器创建完成
)

echo.
echo =====================================================
echo 容器恢复完成！
echo 请检查 Docker Desktop 查看恢复的容器
echo =====================================================

echo.
echo 当前所有容器状态：
docker ps -a

pause 