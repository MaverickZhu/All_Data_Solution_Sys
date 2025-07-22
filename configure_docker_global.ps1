# PowerShell脚本：配置Docker全局环境变量
# 需要管理员权限运行

param(
    [switch]$Force,
    [switch]$Check
)

# 检查是否以管理员身份运行
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# 显示标题
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Docker全局环境配置工具" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# 如果只是检查模式
if ($Check) {
    Write-Host "🔍 检查Docker环境配置..." -ForegroundColor Blue
    
    # 检查系统PATH
    $systemPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    
    $dockerPath = "C:\Program Files\Docker\Docker\resources\bin"
    
    $systemHasDocker = $systemPath -like "*$dockerPath*"
    $userHasDocker = $userPath -like "*$dockerPath*"
    
    Write-Host "Docker安装路径: $dockerPath"
    Write-Host "系统PATH包含Docker: $(if($systemHasDocker){'✅ 是'}else{'❌ 否'})"
    Write-Host "用户PATH包含Docker: $(if($userHasDocker){'✅ 是'}else{'❌ 否'})"
    
    # 测试Docker命令
    try {
        $version = & docker --version 2>$null
        if ($version) {
            Write-Host "Docker命令测试: ✅ 成功 ($version)" -ForegroundColor Green
        } else {
            Write-Host "Docker命令测试: ❌ 失败" -ForegroundColor Red
        }
    } catch {
        Write-Host "Docker命令测试: ❌ 失败 (命令不存在)" -ForegroundColor Red
    }
    
    return
}

# 检查管理员权限
if (-not (Test-Administrator)) {
    Write-Host "❌ 错误：需要管理员权限才能修改系统环境变量" -ForegroundColor Red
    Write-Host ""
    Write-Host "请按以下步骤操作：" -ForegroundColor Yellow
    Write-Host "1. 右键点击PowerShell图标" -ForegroundColor White
    Write-Host "2. 选择'以管理员身份运行'" -ForegroundColor White
    Write-Host "3. 重新执行此脚本" -ForegroundColor White
    Write-Host ""
    Write-Host "或者使用用户级配置（不需要管理员权限）：" -ForegroundColor Yellow
    Write-Host ".\configure_docker_global.ps1 -UserOnly" -ForegroundColor White
    
    Read-Host "按Enter键退出"
    exit 1
}

# 检查Docker安装
$dockerPath = "C:\Program Files\Docker\Docker\resources\bin"
$dockerExe = Join-Path $dockerPath "docker.exe"

Write-Host "🔍 检查Docker安装..." -ForegroundColor Blue

if (-not (Test-Path $dockerExe)) {
    Write-Host "❌ 未找到Docker Desktop安装" -ForegroundColor Red
    Write-Host "   路径: $dockerExe" -ForegroundColor Gray
    Write-Host ""
    Write-Host "请先安装Docker Desktop：" -ForegroundColor Yellow
    Write-Host "1. 访问 https://www.docker.com/products/docker-desktop" -ForegroundColor White
    Write-Host "2. 下载并安装Docker Desktop for Windows" -ForegroundColor White
    Write-Host "3. 重新运行此脚本" -ForegroundColor White
    
    Read-Host "按Enter键退出"
    exit 1
}

Write-Host "✅ 找到Docker安装: $dockerPath" -ForegroundColor Green

# 检查当前PATH配置
Write-Host ""
Write-Host "🔧 检查当前环境变量..." -ForegroundColor Blue

$systemPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
$userPath = [Environment]::GetEnvironmentVariable("PATH", "User")

$systemHasDocker = $systemPath -like "*$dockerPath*"
$userHasDocker = $userPath -like "*$dockerPath*"

Write-Host "系统PATH包含Docker: $(if($systemHasDocker){'✅ 是'}else{'❌ 否'})"
Write-Host "用户PATH包含Docker: $(if($userHasDocker){'✅ 是'}else{'❌ 否'})"

# 如果已经配置且没有强制标志，跳过
if ($systemHasDocker -and -not $Force) {
    Write-Host ""
    Write-Host "✅ Docker路径已在系统PATH中配置" -ForegroundColor Green
    Write-Host "如果仍有问题，请使用 -Force 参数重新配置" -ForegroundColor Yellow
    
    # 测试Docker命令
    Write-Host ""
    Write-Host "🧪 测试Docker命令..." -ForegroundColor Blue
    try {
        $version = & docker --version
        Write-Host "✅ Docker命令测试成功: $version" -ForegroundColor Green
    } catch {
        Write-Host "❌ Docker命令测试失败，可能需要重启系统" -ForegroundColor Red
    }
    
    Read-Host "按Enter键退出"
    exit 0
}

# 配置系统PATH
Write-Host ""
Write-Host "⚙️ 配置系统环境变量..." -ForegroundColor Blue

try {
    if (-not $systemHasDocker) {
        $newSystemPath = $systemPath + ";" + $dockerPath
        [Environment]::SetEnvironmentVariable("PATH", $newSystemPath, "Machine")
        Write-Host "✅ Docker路径已添加到系统PATH" -ForegroundColor Green
    } else {
        Write-Host "ℹ️ Docker路径已存在于系统PATH中" -ForegroundColor Yellow
    }
    
    # 刷新当前会话的环境变量
    $env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [Environment]::GetEnvironmentVariable("PATH", "User")
    
    Write-Host ""
    Write-Host "🧪 测试Docker命令..." -ForegroundColor Blue
    
    # 等待一秒让环境变量生效
    Start-Sleep -Seconds 1
    
    try {
        $version = & docker --version
        Write-Host "✅ 配置成功！Docker版本: $version" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ 配置完成，但命令测试失败" -ForegroundColor Yellow
        Write-Host "   可能需要重启系统或重新打开命令行窗口" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "🎉 配置完成！" -ForegroundColor Green
    Write-Host ""
    Write-Host "📝 重要说明：" -ForegroundColor Yellow
    Write-Host "1. 配置已应用到系统级PATH环境变量" -ForegroundColor White
    Write-Host "2. 新打开的命令行窗口将自动具有docker命令" -ForegroundColor White
    Write-Host "3. 现有的应用程序可能需要重启才能识别新的PATH" -ForegroundColor White
    Write-Host "4. 如果仍有问题，建议重启系统" -ForegroundColor White
    
} catch {
    Write-Host "❌ 配置失败: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "请检查管理员权限并重试" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Read-Host "按Enter键退出" 