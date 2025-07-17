# 🚀 智能Docker构建脚本
# 检测变化并执行增量构建，最大化缓存利用率

param(
    [string]$Service = "backend",
    [switch]$Force,
    [switch]$NoCache,
    [switch]$Verbose
)

Write-Host "🚀 智能Docker构建系统" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Gray

# 获取文件哈希用于变化检测
function Get-FileHash-Safe {
    param([string]$Path)
    if (Test-Path $Path) {
        return (Get-FileHash $Path -Algorithm MD5).Hash
    }
    return "MISSING"
}

# 检查缓存状态
function Test-BuildCache {
    $cacheFile = ".build-cache.json"
    $currentHashes = @{
        "requirements" = Get-FileHash-Safe "backend/requirements.txt"
        "dockerfile" = Get-FileHash-Safe "Dockerfile"
        "dockerignore" = Get-FileHash-Safe ".dockerignore"
    }
    
    $cacheData = @{
        "lastBuild" = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        "hashes" = $currentHashes
        "buildType" = "unknown"
    }
    
    if (Test-Path $cacheFile) {
        try {
            $lastCache = Get-Content $cacheFile | ConvertFrom-Json
            $changes = @()
            
            foreach ($key in $currentHashes.Keys) {
                if ($lastCache.hashes.$key -ne $currentHashes[$key]) {
                    $changes += $key
                }
            }
            
            $cacheData.buildType = if ($changes.Count -eq 0) { "no-change" } 
                                  elseif ($changes -contains "requirements") { "deps-change" }
                                  elseif ($changes -contains "dockerfile") { "docker-change" }
                                  else { "minor-change" }
            
            return @{
                "needsBuild" = ($changes.Count -gt 0)
                "changes" = $changes
                "buildType" = $cacheData.buildType
                "cache" = $cacheData
            }
        }
        catch {
            Write-Warning "缓存文件损坏，将重新构建"
        }
    }
    
    $cacheData.buildType = "first-build"
    return @{
        "needsBuild" = $true
        "changes" = @("all")
        "buildType" = "first-build" 
        "cache" = $cacheData
    }
}

# 智能构建策略
function Get-BuildStrategy {
    param($BuildInfo)
    
    switch ($BuildInfo.buildType) {
        "no-change" {
            return @{
                "action" = "skip"
                "reason" = "无变化，跳过构建"
                "color" = "Green"
            }
        }
        "minor-change" {
            return @{
                "action" = "quick"
                "reason" = "仅代码变化，快速构建" 
                "args" = @("--target", "production")
                "color" = "Yellow"
            }
        }
        "deps-change" {
            return @{
                "action" = "incremental"
                "reason" = "依赖变化，增量构建"
                "args" = @("--target", "production")
                "color" = "Orange"
            }
        }
        "docker-change" {
            return @{
                "action" = "full"
                "reason" = "Dockerfile变化，完全重建"
                "args" = @("--no-cache", "--target", "production")
                "color" = "Red"
            }
        }
        "first-build" {
            return @{
                "action" = "full"
                "reason" = "首次构建，完全构建"
                "args" = @("--target", "production")
                "color" = "Cyan"
            }
        }
    }
}

# 执行构建
function Invoke-SmartBuild {
    param($Service, $Strategy, $BuildInfo)
    
    Write-Host "📊 构建分析结果:" -ForegroundColor Cyan
    Write-Host "  变化类型: $($BuildInfo.buildType)" -ForegroundColor $Strategy.color
    Write-Host "  构建策略: $($Strategy.reason)" -ForegroundColor $Strategy.color
    
    if ($BuildInfo.changes.Count -gt 0) {
        Write-Host "  检测到变化: $($BuildInfo.changes -join ', ')" -ForegroundColor Yellow
    }
    
    if ($Strategy.action -eq "skip" -and -not $Force) {
        Write-Host "✅ 无需构建，使用现有镜像" -ForegroundColor Green
        return $true
    }
    
    # 构建参数
    $buildArgs = @("compose", "build")
    
    if ($NoCache -or $Strategy.action -eq "full") {
        $buildArgs += "--no-cache"
        Write-Host "🔥 使用 --no-cache 模式" -ForegroundColor Red
    }
    
    if ($Strategy.args) {
        $buildArgs += $Strategy.args
    }
    
    $buildArgs += $Service
    
    if ($Verbose) {
        $buildArgs += "--progress=plain"
        Write-Host "🔍 详细输出模式" -ForegroundColor Gray
    }
    
    Write-Host "🔨 执行构建命令: docker $($buildArgs -join ' ')" -ForegroundColor Cyan
    Write-Host "================================================" -ForegroundColor Gray
    
    # 计时构建过程
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    
    try {
        $process = Start-Process -FilePath "docker" -ArgumentList $buildArgs -Wait -PassThru -NoNewWindow
        $stopwatch.Stop()
        
        if ($process.ExitCode -eq 0) {
            Write-Host "✅ 构建成功完成!" -ForegroundColor Green
            Write-Host "⏱️  构建耗时: $($stopwatch.Elapsed.ToString('mm\:ss'))" -ForegroundColor Green
            
            # 更新缓存
            $BuildInfo.cache | ConvertTo-Json -Depth 3 | Set-Content ".build-cache.json"
            Write-Host "💾 构建缓存已更新" -ForegroundColor Green
            
            return $true
        } else {
            Write-Host "❌ 构建失败 (退出码: $($process.ExitCode))" -ForegroundColor Red
            return $false
        }
    }
    catch {
        $stopwatch.Stop()
        Write-Host "❌ 构建异常: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# 显示缓存优化建议
function Show-OptimizationTips {
    Write-Host "`n💡 缓存优化建议:" -ForegroundColor Cyan
    Write-Host "  📦 只修改代码时: 构建时间 < 1分钟" -ForegroundColor Green
    Write-Host "  📋 修改dependencies时: 构建时间 2-5分钟" -ForegroundColor Yellow  
    Write-Host "  🐳 修改Dockerfile时: 构建时间 15-20分钟" -ForegroundColor Red
    Write-Host "  🚀 使用 -Force 强制重建所有层" -ForegroundColor Gray
    Write-Host "  🔍 使用 -Verbose 查看详细构建过程" -ForegroundColor Gray
}

# 主执行流程
try {
    $buildInfo = Test-BuildCache
    $strategy = Get-BuildStrategy $buildInfo
    
    if ($Force) {
        Write-Host "🔥 强制重建模式" -ForegroundColor Red
        $strategy.action = "full"
        $strategy.reason = "用户强制重建"
        $strategy.args = @("--no-cache", "--target", "production")
    }
    
    $success = Invoke-SmartBuild $Service $strategy $buildInfo
    
    if ($success) {
        Show-OptimizationTips
        
        Write-Host "`n🎉 构建完成，可以启动服务了:" -ForegroundColor Green
        Write-Host "   docker-compose up $Service" -ForegroundColor Cyan
    } else {
        Write-Host "`n💭 构建失败排查建议:" -ForegroundColor Yellow
        Write-Host "   1. 检查依赖版本冲突" -ForegroundColor Gray
        Write-Host "   2. 尝试清理Docker缓存: docker system prune" -ForegroundColor Gray
        Write-Host "   3. 使用 -NoCache 参数重新构建" -ForegroundColor Gray
        exit 1
    }
}
catch {
    Write-Host "❌ 脚本执行异常: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} 