@echo off
echo =====================================================
echo 根据数据卷精确恢复原始容器
echo =====================================================

echo.
echo 1. 恢复MongoDB容器 (使用 mongodb_data 卷)...
docker run -d --name mongodb -p 27017:27017 -v mongodb_data:/data/db mongo:latest
echo MongoDB容器已恢复

echo.
echo 2. 恢复n8n容器 (使用 n8n_data 卷)...
docker run -d --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n:latest
echo n8n容器已恢复

echo.
echo 3. 恢复Docker项目的Redis容器 (使用 docker_redis_data 卷)...
docker run -d --name docker-redis-1 -p 6379:6379 -v docker_redis_data:/data redis:6-alpine
echo Docker Redis容器已恢复

echo.
echo 4. 恢复后端Redis容器 (使用 backend_multimodal_redis_data 卷)...
docker run -d --name backend-redis -v backend_multimodal_redis_data:/data redis:latest
echo 后端Redis容器已恢复

echo.
echo 5. 检查并恢复xinference容器...
docker run -d --name xinference -p 9997:9997 xprobe/xinference:latest
echo xinference容器已恢复

echo.
echo 6. 检查并恢复crawl4ai容器...
docker run -d --name crawl4ai -p 8080:8080 unclecode/crawl4ai:basic
echo crawl4ai容器已恢复

echo.
echo 7. 恢复独立的postgres容器...
docker run -d --name postgres -p 5433:5432 -e POSTGRES_PASSWORD=password postgres:latest
echo 独立Postgres容器已恢复

echo.
echo 8. 恢复独立的mysql容器...
docker run -d --name mysql -p 3307:3306 -e MYSQL_ROOT_PASSWORD=password mysql:latest
echo 独立MySQL容器已恢复

echo.
echo =====================================================
echo 精确容器恢复完成！
echo =====================================================

echo.
echo 当前所有容器状态：
docker ps -a

echo.
echo 检查容器总数...
for /f %%i in ('docker ps -a ^| find /c "CONTAINER"') do set count=%%i
set /a count=%count%-1
echo 总容器数：%count%

pause 