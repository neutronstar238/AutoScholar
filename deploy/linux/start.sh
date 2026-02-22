#!/bin/bash
# AutoScholar Linux 启动脚本

echo "🚀 启动 AutoScholar..."

docker-compose up -d

if [ $? -eq 0 ]; then
    echo -e "\n✅ 服务启动成功！"
    echo -e "\n📊 服务状态:"
    docker-compose ps
    echo -e "\n🌐 访问地址:"
    echo "  前端：http://localhost:3000"
    echo "  后端 API: http://localhost:8000"
    echo "  API 文档：http://localhost:8000/docs"
else
    echo -e "\n❌ 启动失败"
fi
