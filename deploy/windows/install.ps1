# AutoScholar Windows 一键安装脚本
# 适用于 Windows 10/11

Write-Host "🚀 AutoScholar Windows 安装程序" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# 检查 Docker Desktop
Write-Host "`n📦 检查 Docker Desktop..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker 已安装：$dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 未检测到 Docker Desktop" -ForegroundColor Red
    Write-Host "请先安装 Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# 检查 Docker Compose
Write-Host "`n📦 检查 Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker-compose --version
    Write-Host "✅ Docker Compose 已安装：$composeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 未检测到 Docker Compose" -ForegroundColor Red
    exit 1
}

# 创建 .env 文件
Write-Host "`n⚙️  创建配置文件..." -ForegroundColor Yellow
if (!(Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "✅ 配置文件已创建，请编辑 .env 文件填入 API Key" -ForegroundColor Green
} else {
    Write-Host "✅ 配置文件已存在" -ForegroundColor Green
}

# 创建数据目录
Write-Host "`n📁 创建数据目录..." -ForegroundColor Yellow
$dirs = @("data/postgres", "data/redis", "data/ollama")
foreach ($dir in $dirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Host "✅ 数据目录已创建" -ForegroundColor Green

Write-Host "`n✨ 安装完成！" -ForegroundColor Green
Write-Host "`n📝 下一步:" -ForegroundColor Cyan
Write-Host "1. 编辑 .env 文件，填入你的 API Key 或配置 Ollama"
Write-Host "2. 运行 .\deploy\windows\start.ps1 启动服务"
Write-Host "3. 访问 http://localhost:3000 使用系统"
