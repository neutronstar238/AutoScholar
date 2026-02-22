# AutoScholar Windows 停止脚本

Write-Host "🛑 停止 AutoScholar..." -ForegroundColor Yellow

docker-compose down

Write-Host "`n✅ 服务已停止" -ForegroundColor Green
