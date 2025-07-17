# 🚀 快速构建脚本
# 使用示例：
#   .\build.ps1                    # 智能增量构建
#   .\build.ps1 -Force            # 强制完全重建  
#   .\build.ps1 -Quick            # 只重建代码层

param(
    [switch]$Force,
    [switch]$Quick,
    [switch]$Verbose
)

Write-Host "🚀 多模态智能数据分析平台 - 快速构建" -ForegroundColor Cyan

if ($Quick) {
    Write-Host "⚡ 快速构建模式 (仅代码变更)" -ForegroundColor Yellow
    docker-compose build backend
} elseif ($Force) {
    Write-Host "🔥 强制完全重建模式" -ForegroundColor Red
    docker-compose build --no-cache backend
} else {
    Write-Host "🧠 智能增量构建模式" -ForegroundColor Green
    
    # 检查requirements.txt是否变化
    $reqHash = ""
    if (Test-Path "backend/requirements.txt") {
        $reqHash = (Get-FileHash "backend/requirements.txt").Hash
    }
    
    $cacheFile = ".build-cache"
    $lastHash = ""
    if (Test-Path $cacheFile) {
        $lastHash = Get-Content $cacheFile -ErrorAction SilentlyContinue
    }
    
    if ($reqHash -ne $lastHash) {
        Write-Host "📦 检测到依赖变化，执行增量构建..." -ForegroundColor Yellow
        docker-compose build backend
        $reqHash | Set-Content $cacheFile
    } else {
        Write-Host "✅ 依赖无变化，执行快速构建..." -ForegroundColor Green
        docker-compose build backend
    }
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ 构建成功！" -ForegroundColor Green
    Write-Host "启动服务: docker-compose up" -ForegroundColor Cyan
} else {
    Write-Host "`n❌ 构建失败" -ForegroundColor Red
    exit 1
} 