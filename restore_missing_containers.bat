@echo off
echo =====================================================
echo 恢复所有缺失的Docker容器
echo =====================================================

echo.
echo 1. 创建独立的Redis容器...
docker run -d --name redis-standalone -p 6379:6379 redis:latest
echo Redis容器创建完成

echo.
echo 2. 创建n8n自动化工具容器...
docker run -d --name n8n-standalone -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n:latest
echo n8n容器创建完成

echo.
echo 3. 创建xinference AI服务容器...
docker run -d --name xinference-standalone -p 9997:9997 xprobe/xinference:latest
echo xinference容器创建完成

echo.
echo 4. 创建crawl4ai爬虫服务容器...
docker run -d --name crawl4ai-standalone -p 8080:8080 unclecode/crawl4ai:basic
echo crawl4ai容器创建完成

echo.
echo 5. 创建MongoDB容器...
docker run -d --name mongodb-standalone -p 27017:27017 -v mongodb_data:/data/db mongo:latest
echo MongoDB容器创建完成

echo.
echo 6. 检查是否有其他项目目录...

:: 检查更多可能的位置
if exist "C:\Users\Zz-20240101\n8n\docker-compose.yml" (
    echo 找到n8n项目目录，创建容器...
    cd "C:\Users\Zz-20240101\n8n"
    docker-compose create
)

if exist "C:\Users\Zz-20240101\xinference\docker-compose.yml" (
    echo 找到xinference项目目录，创建容器...
    cd "C:\Users\Zz-20240101\xinference"
    docker-compose create
)

:: 检查Documents目录
if exist "C:\Users\Zz-20240101\Documents" (
    echo 检查Documents目录中的项目...
    for /d %%i in ("C:\Users\Zz-20240101\Documents\*") do (
        if exist "%%i\docker-compose.yml" (
            echo 找到项目: %%i
            cd "%%i"
            docker-compose create
        )
    )
)

echo.
echo 7. 创建常用数据库容器...
docker run -d --name postgres-standalone -p 5432:5432 -e POSTGRES_PASSWORD=password -v postgres_data:/var/lib/postgresql/data postgres:latest
docker run -d --name mysql-standalone -p 3306:3306 -e MYSQL_ROOT_PASSWORD=password -v mysql_data:/var/lib/mysql mysql:latest

echo.
echo =====================================================
echo 所有容器恢复完成！
echo =====================================================

echo.
echo 当前所有容器状态：
docker ps -a

echo.
echo 检查容器数量...
docker ps -a | find /c "CONTAINER"

pause 