# AutoScholar Windows 启动脚本

Write-Host "🚀 启动 AutoScholar..." -ForegroundColor Cyan

# 启动 Docker Compose
docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ 服务启动成功！" -ForegroundColor Green
    Write-Host "`n📊 服务状态:" -ForegroundColor Cyan
    docker-compose ps
    Write-Host "`n🌐 访问地址:" -ForegroundColor Cyan
    Write-Host "  前端：http://localhost:3000" -ForegroundColor Green
    Write-Host "  后端 API: http://localhost:8000" -ForegroundColor Green
    Write-Host "  API 文档：http://localhost:8000/docs" -ForegroundColor Green
} else {
    Write-Host "`n❌ 启动失败，请检查错误信息" -ForegroundColor Red
}
