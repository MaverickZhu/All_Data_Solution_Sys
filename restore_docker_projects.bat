@echo off
echo =====================================================
echo Docker项目批量恢复脚本
echo =====================================================

echo.
echo 第一步：重新拉取常用基础镜像...
echo.

docker pull postgres:latest
docker pull postgres:13
docker pull postgres:14
docker pull postgres:15
docker pull redis:latest
docker pull redis:7
docker pull mongo:latest
docker pull mongo:6
docker pull nginx:latest
docker pull node:18
docker pull node:16
docker pull node:20
docker pull python:3.11
docker pull python:3.12
docker pull ubuntu:22.04
docker pull ubuntu:20.04

echo.
echo 第二步：检查现有Docker资源...
echo.
docker ps -a
echo.
docker images
echo.
docker volume ls
echo.
docker network ls

echo.
echo =====================================================
echo 基础镜像拉取完成！
echo.
echo 接下来需要手动恢复各个项目：
echo 1. 进入每个项目目录
echo 2. 运行: docker-compose pull
echo 3. 运行: docker-compose up --build -d
echo =====================================================
pause 