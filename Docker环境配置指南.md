# Docker全局环境配置指南

## 🎯 目标
将Docker命令行配置为系统全局可用，确保我们的视频分析监控工具能正常访问Docker容器。

## 📋 问题现象
- 在命令行中运行 `docker --version` 报错"命令不存在"
- 任务监控工具无法检测容器内的GPU状态
- 需要手动设置PATH才能使用Docker命令

## 🛠️ 解决方案

### 方案一：自动配置（推荐）

#### 1. 使用PowerShell脚本（需管理员权限）
```powershell
# 以管理员身份运行PowerShell，然后执行：
.\configure_docker_global.ps1
```

**功能特点：**
- ✅ 自动检测Docker安装路径
- ✅ 配置系统级PATH环境变量
- ✅ 立即测试配置效果
- ✅ 永久生效，重启后依然有效

#### 2. 使用批处理脚本（简单版）
```batch
# 双击运行：
setup_docker_env.bat
```

**适用场景：**
- 快速临时配置
- 不需要管理员权限
- 需要重新运行生效

### 方案二：手动配置

#### Windows 10/11 图形界面配置

1. **打开系统设置**
   - 按 `Win + X`，选择"系统"
   - 点击"高级系统设置"
   - 点击"环境变量"

2. **编辑系统PATH**
   - 在"系统变量"区域找到"Path"
   - 点击"编辑"
   - 点击"新建"
   - 添加：`C:\Program Files\Docker\Docker\resources\bin`
   - 点击"确定"保存

3. **验证配置**
   - 重新打开命令行窗口
   - 运行：`docker --version`
   - 应该显示Docker版本信息

#### PowerShell命令行配置

```powershell
# 检查当前PATH
$env:PATH -split ';' | Where-Object { $_ -like "*Docker*" }

# 添加Docker路径到系统PATH（需管理员权限）
$dockerPath = "C:\Program Files\Docker\Docker\resources\bin"
$currentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
$newPath = $currentPath + ";" + $dockerPath
[Environment]::SetEnvironmentVariable("PATH", $newPath, "Machine")

# 刷新当前会话
$env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [Environment]::GetEnvironmentVariable("PATH", "User")
```

## 🧪 测试验证

### 1. 基本命令测试
```bash
# 测试Docker版本
docker --version

# 测试容器列表
docker ps

# 测试容器执行
docker exec all_data_solution_sys-celery-worker-1 python -c "print('Hello from container')"
```

### 2. 使用我们的健康检查工具
```bash
# 运行完整健康检查
python debug_video_analysis.py --full-check

# 或使用批处理脚本
check_video_analysis.bat
```

**预期结果：**
```
✅ 容器GPU可用: NVIDIA GeForce RTX 4090 (数量: 1)
🎯 GPU状态: 容器内GPU可用，视频分析将使用GPU加速
📊 健康状态报告: 4/4 检查通过 (100.0%)
🟢 系统状态良好
```

### 3. 任务监控工具测试
```bash
# 检查任务状态
python task_monitor.py --check-stuck

# 启动持续监控
python task_monitor.py --monitor
```

## 🔧 故障排除

### 问题1：仍然提示"docker命令不存在"

**解决方案：**
1. 确认Docker Desktop已安装并运行
2. 重启命令行窗口
3. 重启系统（让环境变量彻底生效）
4. 检查Docker服务状态

### 问题2：Docker路径不正确

**检查实际安装路径：**
```powershell
# 查找Docker安装位置
Get-ChildItem "C:\Program Files\Docker" -Recurse -Name "docker.exe"

# 常见路径：
# C:\Program Files\Docker\Docker\resources\bin\docker.exe
# C:\Program Files\Docker\Docker\resources\bin\
```

### 问题3：权限不足

**解决方案：**
1. 以管理员身份运行PowerShell
2. 或配置用户级PATH（不需要管理员权限）
3. 使用我们的工具内置的Docker路径检测

### 问题4：配置后仍不生效

**排查步骤：**
```powershell
# 检查配置脚本
.\configure_docker_global.ps1 -Check

# 查看当前环境变量
echo $env:PATH

# 手动测试完整路径
& "C:\Program Files\Docker\Docker\resources\bin\docker.exe" --version
```

## 📚 相关工具说明

### 我们的智能解决方案

我们的工具已经内置了Docker路径自动检测功能：

```python
# debug_video_analysis.py 和 task_monitor.py 中的智能检测
docker_paths = [
    "docker",  # 先尝试PATH中的docker
    "C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker.exe",
    os.path.expandvars("%ProgramFiles%\\Docker\\Docker\\resources\\bin\\docker.exe")
]
```

**优势：**
- ✅ 自动适配不同环境
- ✅ 无需手动配置即可工作
- ✅ 提供详细的错误提示
- ✅ 支持多种Docker安装路径

### 配置工具对比

| 工具 | 权限要求 | 持久性 | 适用场景 |
|------|----------|--------|----------|
| `configure_docker_global.ps1` | 管理员 | 永久 | 一次配置，全局生效 |
| `setup_docker_env.bat` | 普通用户 | 临时 | 快速临时解决 |
| 手动GUI配置 | 管理员 | 永久 | 传统方式，可靠性高 |
| 工具内置检测 | 无 | 每次检测 | 最智能，无需配置 |

## ✅ 最佳实践

### 推荐配置流程

1. **首次使用**：运行 `configure_docker_global.ps1`（需管理员权限）
2. **验证配置**：运行 `check_video_analysis.bat`
3. **日常使用**：直接运行监控工具，会自动检测Docker

### 开发环境建议

- **开发者**：配置全局PATH，方便命令行使用
- **生产环境**：依赖工具内置检测，减少配置依赖
- **CI/CD**：使用环境变量或Docker API

## 🎉 配置完成确认

当看到以下输出时，说明配置成功：

```bash
PS C:\> docker --version
Docker version 28.3.2, build 578ccf6

PS C:\> python debug_video_analysis.py --full-check
✅ 容器GPU可用: NVIDIA GeForce RTX 4090 (数量: 1)
📊 健康状态报告: 4/4 检查通过 (100.0%)
🟢 系统状态良好
```

恭喜！您的Docker环境已完全配置好，可以开始使用视频深度分析系统的所有功能了！ 🚀 